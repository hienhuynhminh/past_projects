# -*- coding: utf-8 -*-
"""
Created on Tue Apr 12 16:14:33 2022

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
import image_classification_airflow_test.image_classification_workflow as image_classification_workflow

#%% DAG

# SCHEDULE IMAGE CLASSIFIER TO RUN MONTHLY AT 20:00
with DAG("",
         description='Deploy Image Classification Model and Predict Labels for Images in AWS',
         start_date = datetime(2022, 4, 12),
         schedule_interval = "0 18 15 * *", 
         catchup = False
         ) as dag: 
    
    # START
    start = DummyOperator(
        task_id="start")
    
    # MAIN
    deploy_model = PythonOperator(
        task_id="deploy_image_classifier",
        python_callable = image_classification_workflow.image_classification, 
        trigger_rule= "all_success",
        retries = 1
        )
    
    # COMPLETE
    complete = DummyOperator(
        task_id="complete")
        
    
    # OPERATOR RELATIONSHIP
    start.set_downstream(deploy_model)
    deploy_model.set_downstream(complete)
