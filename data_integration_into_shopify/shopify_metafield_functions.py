# -*- coding: utf-8 -*-
"""
Created on Thu Feb 10 14:21:18 2022

@author: Hien Huynh
"""



"""
DIFFERENT FUNCTIONS WHICH MAINLY DO THE FOLLOWING JOBS:

* TRACK NEW METAFIELDS OR UPDATES IN EXISTING METAFIELDS FOR PRODUCTS IN SHOPIFY;
* PERFORM API CALLS ACCORDINGLY.
"""



#%% IMPORT 

# IMPORT PACKAGES
import google.auth
from google.cloud import bigquery
from google.cloud import bigquery_storage
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import numpy as np
import time
import os
import ast
import requests
import json


# IGNORE WARNINGS
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None  # default='warn'

#%% FUNCTIONS
# EXTRACT SKU FROM VARIANTS
def get_sku(variants):
    variants = ast.literal_eval(variants)
    variants = variants[0] # Now it's a dictionary
    return variants.get('sku')

# CONVERT SKUS TO HANDLES
def skuToHandle(sku_list,sku_handle_dict):
    handles = []
    for i in sku_list:
        handle = sku_handle_dict.get(i)
        handles.append(handle)
    return handles

# CONVERT A LIST OF STRINGS TO STRING (SEPARATED BY COMMAS)
def ListToString(List):
    return ','.join(List)

# GET INDICES OF SKUS WHICH EXIST IN A PARTICULAR STORE
def index_existing_skus(sku_list,sku_handle_dict):
    indices = []
    for i in range(len(sku_list)):
        if sku_handle_dict.get(sku_list[i]) == None:
            pass
        else:
            indices.append(i)
    return indices


### MAIN COMPARISON AND UPDATING FUNCTIONS ###
# RETRIEVE METAFIELD BY NAMESPACE & KEY
def filter_metafield_by_namespace_and_key(namespace,key,product_metafields):
    filtered = {}
    for idx, metafield in enumerate(product_metafields):
        if (metafield.get('namespace') == namespace) and (
                metafield.get('key') == key):
            filtered = product_metafields[idx]
        else:
            pass
    return filtered

# COMPARE VALUES OF METAFIELDS
def comparison(metafield_tocompare,metafield_current):
    status = ""
    if metafield_current == {}:
        status = "Add new metafield"
    elif metafield_current.get('value') == metafield_tocompare:
        status = "No change"
    else:
        status = "Update existing metafield"
    return status
        
# CREATE UPDATE/ADD REQUESTS BY APPLYING COMPARISON FUNCTION
def create_requests(namespace,key,value_type,df_tocompare,col_tocompare,shopify_product_info):
    
    # If shopify_product_info does not have col 'item_sku' yet, add this col
    if 'item_sku' not in shopify_product_info.columns.to_list():
        shopify_product_info['item_sku'] = shopify_product_info['variants'].apply(get_sku)
    else:
        pass
    
    # Remove irrelevant skus    
    shopify_product_info = shopify_product_info[
        shopify_product_info['item_sku'].isin(df_tocompare['item_sku'].to_list())]
    
    df_tocompare = df_tocompare[
        df_tocompare['item_sku'].isin(shopify_product_info['item_sku'].to_list())]
    
    # String object to a list of dictionaries (incl. namespace, key etc.)
    shopify_product_info['product_metafields'] = shopify_product_info['product_metafields'].apply(
        lambda x: ast.literal_eval(x))
    
    
    # Use 'filter_metafield_by_namespace_and_key' to retrieve target metafield
    # by namespace & key
    shopify_product_info['filtered_metafield'] = shopify_product_info['product_metafields'].apply(
        lambda x: filter_metafield_by_namespace_and_key(namespace,key,x))
    
    df_tocompare = pd.merge(df_tocompare,
                            shopify_product_info[['item_sku','id','filtered_metafield']],
                            on='item_sku')
    df_tocompare = df_tocompare.rename(columns={'id':'product_id'})
    
    
    
    # Use function 'comparison' to make the comparison between current metafield value
    # and metafield value from df_tocompare
    df_tocompare['status'] = df_tocompare.apply(lambda x: comparison(
        x[col_tocompare],x['filtered_metafield']),axis=1)
    
    # Create new column name, e.g. product_delivery.days(json_string)
    new_col_name = namespace+"."+key+" "+"["+value_type+"]"
    
    # Rename column, use new_col_name defined above
    df_tocompare = df_tocompare.rename(columns={col_tocompare:new_col_name})
    
    
    # DataFrame: Add new metafield
    add_new_metafield = df_tocompare[df_tocompare['status']=="Add new metafield"][[
        'item_sku','product_id',new_col_name]].reset_index(drop=True)
    
    # DataFrame: Update existing metafield
    update_ex_metafield = df_tocompare[df_tocompare['status']=="Update existing metafield"]
    update_ex_metafield['metafield_id'] = update_ex_metafield['filtered_metafield'].apply(
        lambda x: x.get('id'))
    
    update_ex_metafield = update_ex_metafield[['item_sku','product_id',
                                               new_col_name,'metafield_id']].reset_index(drop=True)
    
    return add_new_metafield, update_ex_metafield


### API FUNCTIONS ###
def create_metafield(add_metafield_df, column, namespace, key, value_type, api_key, api_pass, store):
    counter = 0
    while counter < len(add_metafield_df):
        row = add_metafield_df.iloc[counter]
        url = "https://%s:%s@%s.myshopify.com/admin/api/2021-10/products/%d/metafields.json" % (api_key, api_pass, store, row['product_id'])
        metafield_value = row[column]

        
        body = {
            "metafield": {
                "namespace": namespace,
                "key": key,
                "value": metafield_value,
                "type": value_type
                }
            }
        
        
        response = requests.post(url = url, json = body)
        
        
        if response.status_code == 201:
            print("{}/{} For SKU {}, updated {}.".format(
                counter+1,len(add_metafield_df),row['item_sku'],metafield_value))
            counter += 1
        elif response.status_code == 429:
            print("{}/{} For SKU {}, encounter 429 error. Retry after 2 seconds.".format(
                counter+1,len(add_metafield_df),row['item_sku']))
            time.sleep(2)
            continue
        else:
            print("{}/{} For SKU {}, encounter {} error.".format(
                counter+1,len(add_metafield_df),row['item_sku'],response.status_code))
            counter += 1
         
    return print('Creating New Metafield Job Done.')

def update_metafield(update_metafield_df, column, value_type, api_key, api_pass, store):

    counter = 0
    while counter < len(update_metafield_df):
        row = update_metafield_df.iloc[counter]
        url = "https://%s:%s@%s.myshopify.com/admin/api/2021-10/metafields/%d.json" % (api_key, api_pass, store, row['metafield_id'])      
        metafield_value = row[column]
        
        
        body = {
            "metafield":{
                "id": int(row['metafield_id']),
                "value": metafield_value,
                "type": value_type    
                }
        }
            
        
        response = requests.put(url = url, json = body)
        
        if response.status_code == 200:
            print("{}/{} For SKU {}, updated {}.".format(
                counter+1,len(update_metafield_df),row['item_sku'],metafield_value))
            counter += 1
        elif response.status_code == 429:
            print("{}/{} For SKU {}, encounter 429 error. Retry after 2 seconds.".format(
                counter+1,len(update_metafield_df),row['item_sku']))
            time.sleep(2)
            continue
        else:
            print("{}/{} For SKU {}, encounter {} error.".format(
                counter+1,len(update_metafield_df),row['item_sku'],response.status_code))
            counter += 1
    return print("Updating Metafield Job Done.")