# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 15:00:30 2022

@author: Hien Huynh
"""

#%% IMPORT 
# PACKAGES
import pandas as pd
from datetime import datetime
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.trigger_rule import TriggerRule

# PYTHON FUNCTIONS
import upselling_metafields.upsell_recommendations_to_shopify as upsell_recommendations_to_shopify
import shopify_metafield_functions
import GBQ

#%%

# CREDENTIALS OF SHOPIFY STORES
languages = ["NL","DE"]

channel_secrets_and_variables = "channel_secrets_and_variables.json"
    
try:
    CLIENT_LANGUAGES = Variable.get(channel_secrets_and_variables, deserialize_json=True)

    with open(channel_secrets_and_variables, 'w') as outfile:
        json.dumps(CLIENT_LANGUAGES, outfile)
except Exception as e:
    print(e)
    pass


# DAG

# SCHEDULE UPSELL RECOMMENDATIONS METAFIELD COMPARISON AND API CALLS
# WEEKLY ON MONDAY AT MIDNIGHT 00:00
with DAG("upselling_metafields", 
         start_date = datetime(2022, 3, 27),
         schedule_interval = "0 0 * * 1",
         description = 'Upselling recommendations metafield comparison and API calls to Shopify',
         catchup = False
         ) as dag:

    # START
    start = DummyOperator(
        task_id="start")
    
    # MAIN OPERATOR: LOOP THROUGH LANGUAGES
    metafields_to_shopify = {}
    for language in languages:
        metafields_to_shopify[language] = PythonOperator(
            task_id="UpsellingMetafieldComparisonAndAPICalls_{}".format(language.upper()),
            python_callable = upsell_recommendations_to_shopify.upsell_recommendations_to_shopify, 
            op_kwargs = {"language":language,
                         "API_KEY":CLIENT_LANGUAGES[language]["SHOPIFY_API_KEY"],
                         "API_PASS":CLIENT_LANGUAGES[language]["SHOPIFY_API_PASS"],
                         "STORE":CLIENT_LANGUAGES[language]["SHOPIFY_STORE"]},
            trigger_rule= "all_success",
            retries = 1
            )
    
    # COMPLETE
    complete = DummyOperator(
        task_id="complete")
        
    # OPERATOR RELATIONSHIP
    for language in languages:
        start.set_downstream(metafields_to_shopify[language])
        metafields_to_shopify[language].set_downstream(complete)