# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 12:26:52 2022

@author: Hien Huynh
"""

"""
COMPARE RECOMMENDATIONS METAFIELDS (NAMESPACE: RECOMMENDATIONS; KEY: SKUS);
TRACK NEW RECOMMENDATIONS METAFIELDS OR UPDATES IN EXISTING RECOMMENDATIONS METAFIELDS;
PERFORM API CALLS ACCORDINGLY.
"""

#%% IMPORT
# IMPORT PACKAGES
import google.auth
from google.cloud import bigquery
from google.cloud import bigquery_storage
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import numpy as np
import os
import ast
import requests

# IMPORT PYTHON FUNCTIONS
import shopify_metafield_functions
import GBQ

#%% 
def upsell_recommendations_to_shopify(language, API_KEY, API_PASS, STORE):
    # LOAD TABLES FROM GBQ
    
    # SHOPIFY PRODUCT INFO COMPLETE
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    credentials_location = 'client_secret.json'
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_location, scope)
    
    print(f"Loading Shopify Product Info Complete {language.upper()}")
    project_id = "masterdata-291714"
    dataset = "Shopify_product_info"
    table = f"Shopify_product_info_complete_{language.upper()}" 
    shopify_product_info = GBQ.get_gbq_data(project_id, dataset, table, credentials_location)
    print(f"Shopify Product Info Complete {language.upper()} loaded")
    
    
    # UPSELL RECOMMENDATIONS (FROM TRANSFORMED DATA PROJECT)
    credentials_location = 'client_secret_transformed_data.json'
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_location, scope)
    
    print("Loading Upsell Recommendations (Unsorted)")
    project_id = "naduvi-data"
    dataset = "SKU_insights"
    table = "Upsell_recommendations" 
    all_recommendations = GBQ.get_gbq_data(project_id, dataset, table, credentials_location)
    print("Upsell Recommendations (Unsorted) loaded")
    
    
    
    # ADD ITEM_SKU (COLUMN) TO SHOPIFY PRODUCT INFO COMPLETE
    shopify_product_info['item_sku'] = shopify_product_info['variants'].apply(shopify_metafield_functions.get_sku)
    
    # CREATE DATAFRAME THAT CONSISTS OF PUBLISHED AND ACTIVE SKUS
    available_skus = shopify_product_info
    shopify_product_info = shopify_product_info[['item_sku','id','product_metafields']]
    
    # REMOVE ROWS IN DATAFRAME WHERE COL PUBLISHED_AT IS EMPTY STRING
    available_skus = available_skus[available_skus['published_at']!=""]
    
    # REMOVE ROWS IN STATUS IF NOT ACTIVE
    available_skus = available_skus[available_skus['status']=="active"]
    available_skus = available_skus.reset_index(drop=True)

    # SKU-HANDLE DICTIONARY
    # USED TO CONVERT SKUS TO HANDLES
    sku_handle_dict =dict(zip(available_skus['item_sku'], available_skus['handle']))
    
    # DELETE AVAILABLE_SKUS DATAFRAME
    del available_skus
    
    
    # CLEAN ALL_RECOMMENDATIONS (UNSORTED) TABLE   
    print('Sort and Clean Upsell Recommendations')
    # REMOVE EMPTY RECOMMENDATIONS (EMPTY STRINGS)
    all_recommendations['recommendations'].replace('', np.nan, inplace=True)
    all_recommendations.dropna(subset=['recommendations'], inplace=True)
    
    
    # REMOVE IRRELEVANT SKUS (COL SKU) FOR A PARTICULAR STORE
    all_recommendations = all_recommendations[
        all_recommendations['SKU'].isin(shopify_product_info['item_sku'].to_list())]
    all_recommendations = all_recommendations.reset_index(drop=True)
        
    
    # STRING REPRESENTATIONS OF LISTS TO ACTUAL LISTS
    # COL RECOMMENDATIONS
    all_recommendations['recommendations'] = all_recommendations['recommendations'].apply(
        lambda x: ast.literal_eval(x))
    # COL NADUVI_SCORE 
    all_recommendations['NADUVI_score'] = all_recommendations['NADUVI_score'].apply(
        lambda x: ast.literal_eval(x))
    # COL UPSELL_ORDER
    all_recommendations['Upsell_order'] = all_recommendations['Upsell_order'].apply(
        lambda x: ast.literal_eval(x))
    # COL TYPE_ORDER
    all_recommendations['Type_order'] = all_recommendations['Type_order'].apply(
        lambda x: ast.literal_eval(x))
    
    
    # FOR SKUS IN COL RECOMMENDATIONS, REMOVE NON-EXISTING SKUS IN A PARTICULAR STORE
    # RETRIEVE INDICES OF EXISTING SKUS
    all_recommendations['existing_skus_indices'] =  all_recommendations['recommendations'].apply(
        lambda x: shopify_metafield_functions.index_existing_skus(x,sku_handle_dict))
    
    
    
    # KEEP SKUS (COL RECOMMENDATIONS), NADUVI_SCORE, UPSELL_ORDER AND TYPE_ORDER
    # BASED ON COL EXISTING_SKUS_INDICES
    for i, row in all_recommendations.iterrows():
        indices = row['existing_skus_indices']
        
        row['recommendations'] = [row['recommendations'][idx] for idx in indices]
        row['NADUVI_score'] = [row['NADUVI_score'][idx] for idx in indices]
        row['Upsell_order'] = [row['Upsell_order'][idx] for idx in indices]
        row['Type_order'] = [row['Type_order'][idx] for idx in indices]
        
        # PERFORM SORTING FOR RECOMMENDATIONS BASED ON NADUVI_SCORE, UPSELL_ORDER AND TYPE_ORDER
        # USE A TEMPORARY DATAFRAME TO SORT
        zipped = list(zip(row['recommendations'],row['NADUVI_score'],row['Upsell_order'],row['Type_order']))
        temp_df = pd.DataFrame(zipped,columns=['recommendations','NADUVI_score',
                                               'Upsell_order','Type_order'])
        temp_df = temp_df.sort_values(['Type_order','Upsell_order','NADUVI_score'],
                                      ascending=False)
        
        # RETURN SORTED LIST OF RECOMMENDATIONS, GET FIRST 10 SKUS
        row['recommendations'] = temp_df['recommendations'].to_list()[:10]
        row['NADUVI_score'] = temp_df['NADUVI_score'].to_list()[:10]
        row['Upsell_order'] = temp_df['Upsell_order'].to_list()[:10]
        row['Type_order'] = temp_df['Type_order'].to_list()[:10]
        
        # CONVERT LIST OF SKUS IN COL RECOMMENDATIONS TO LIST OF HANDLES
        row['recommendations'] = shopify_metafield_functions.skuToHandle(row['recommendations'],
                                                                         sku_handle_dict)
        
        # CONVERT LIST OF HANDLES TO STRING REPRESENTATION OF LIST
        row['recommendations'] = shopify_metafield_functions.ListToString(row['recommendations'])
        del temp_df
    
    
    # FINAL SORTED RECOMMENDATIONS DF
    all_recommendations_sorted = all_recommendations[['SKU','recommendations']]
    del all_recommendations
    # RENAME COL SKU TO ITEM_SKU
    # REQUIRED FOR THE NEXT COMPARISON FUNCTION
    all_recommendations_sorted.rename(columns={'SKU':'item_sku',
                                               'recommendations':'sorted_recommendations'},inplace=True)
    
    
    # ACTUAL COMPARISON BETWEEN SHOPIFY CURRENT RECOMMENDATIONS METAFIELDS AND NEW RECOMMENDATIONS FROM GBQ
    
    print('Perform comparisons for {} data'.format(language.upper()))
    # CREATE REQUESTS FUNCTION TAKES AS INPUT:
        # METAFIELD NAMESPACE: 'RECOMMENDATIONS'
        # METAFIELD KEY: 'SKUS'
        # METAFIELD VALUE TYPE: 'STRING'
        # DATAFRAME TO BE COMPARED WITH CURRENT METAFIELDS IN SHOPIFY PRODUCT INFO COMPLETE (1)
        # SPECIFIC COLUMN IN (1) THAT CONTAINS VALUES TO COMPARE
        # SHOPIFY PRODUCT INFO COMPLETE (CONTAINING CURRENT PRODUCT METAFIELDS IN SHOPIFY)
        
    # ATTRIBUTES OF THE RECOMMENDATIONS METAFIELDS
    namespace = 'recommendations'
    key = 'skus'
    value_type = 'string'
    
    # COLUMN SORTED RECOMMENDATIONS FROM GBQ TABLE ALL RECOMMENDATIONS SORTED
    column = 'sorted_recommendations'
    
    # APPLY CREATE REQUESTS FUNCTION THAT TRACKS NEW METAFIELDS OR UPDATES IN
    # EXISTING METAFIELDS, RETURNS TWO DFs USED IN THE API CALLS
    add_new_metafield, update_ex_metafield = shopify_metafield_functions.create_requests(namespace,key,value_type,
                                                                                         all_recommendations_sorted,column,
                                                                                         shopify_product_info)
    
    
    
    
    # API CALLS - NEW METAFIELDS AND UPDATES IN EXISTING METAFIELDS TO SHOPIFY
    print('Start making API calls')
    
    # IF-ELSE BLOCK: ONLY MAKE API CALLS WHEN LENGTH OF DFs IS LARGER THAN 0
    if len(add_new_metafield) > 0:
        shopify_metafield_functions.create_metafield(add_new_metafield, column,
                                                     namespace, key, value_type, 
                                                     API_KEY, API_PASS, STORE)
    else:
        print('No new metafields to be added to {} store.'.format(language.upper()))
    
    
    if len(update_ex_metafield) > 0:
        shopify_metafield_functions.update_metafield(update_ex_metafield, column,
                                                     value_type, API_KEY, API_PASS, STORE)
    else:
        print('No changes found for existing metafields in {} store.'.format(language.upper()))
    
    print('API calls completed.')
    
    # REPORT (TO BE SEEN IN TASK INSTANCE LOGS)
    print('### OVERVIEW FOR {}: ###'.format(language.upper()))
    print('Number of Rows in Shopify Product Info Complete {} Table: {}'.format(
        language.upper(),len(shopify_product_info)))
    print('Number of POST Requests: {}'.format(len(add_new_metafield)))
    print('Number of PUT Requests: {}'.format(len(update_ex_metafield)))
