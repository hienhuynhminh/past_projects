# -*- coding: utf-8 -*-
"""
Created on Tue Apr 12 13:32:38 2022

@author: Hien Huynh
"""

#%% IMPORT PACKAGES
from tensorflow import keras
import h5py
import boto3
from PIL import Image
from urllib import request
from io import BytesIO
import numpy as np
import pandas as pd
import datetime

#%% FUNCTIONS
# LOAD SAVED MODEL (H5 FILE)
def load_model():
    
    filename = "best_model.h5"    
    
    model = None

    try:
        model = h5py.File(filename)
    except Exception as e:
        print(e)
        pass
    
    if model == None:
        print("Could not load model.")
    else:
        model = keras.models.load_model(model)
        print(model)
        print("Model successfully loaded.")
    return model 

# CONNECT TO AWS S3
# USING HIEN'S AWS CREDENTIALS
def connect():
    access_key = 'YYYY' # Replace YYYY with a valid access key
    secret_key = 'ZZZZ' # Replace ZZZZ with a valid secret key

    return boto3.client('s3', aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key)

# FOR EACH S3 BUCKET, LOAD AND PROCESS IMAGES (INTO NUMPY ARRAYS) AS MODEL INPUTS
# THEN PERFORM CLASSIFICATION AND UPDATE PREDICTED LABELS TO IMAGE METADATA
def image_classification():
    # LOAD SAVED MODEL
    model = load_model()
    
    # CONNECT TO AWS S3
    s3 = connect()
    
    # LIST OF ALL BUCKETS
    response = s3.list_buckets()
    buckets = response.get('Buckets')
    buckets = [bucket.get('Name') for bucket in buckets]
    
    # LIST OF BUCKETS WHERE IMAGE CLASSIFICATION WOULD BE IRRELEVANT
    buckets_to_exclude = ['naduvi-videos']
    # EXCLUDE IRRELEVANT BUCKETS
    for bucket_to_exclude in buckets_to_exclude:
        buckets.remove(bucket_to_exclude)
    
    # DEFINE CLASS NAMES
    class_names = ['ambience', 'ambience close-up', 'product', 
                   'product close-up', 'specifications']
    
    # TEST
    # buckets = ['hien-test-classification']
    
    # PER BUCKET: LOAD & PROCESS IMAGES, THEN PERFORM PREDICTION
    paginator = s3.get_paginator("list_objects_v2")
    counter = 0
    for bucket in buckets:
        images = []
        urls = []
        filenames = []
        for page in paginator.paginate(Bucket=bucket):
            for item in page['Contents']:
                filename = item['Key']
                metadata = s3.head_object(Bucket=bucket, Key= filename).get('Metadata')
                contenttype = s3.head_object(Bucket=bucket, Key= filename).get('ContentType')
                
                if (metadata.get('predictedlabel') == None) and ("image" in contenttype):
                    url = "https://{}.s3.eu-central-1.amazonaws.com/{}".format(bucket, filename)
                    res = request.urlopen(url).read()
                    image = Image.open(BytesIO(res)).resize((128,128))
                    image = keras.utils.img_to_array(image).astype('float32')/255
                    images.append(image)
                    urls.append(url)
                    filenames.append(filename)
                else:
                    pass
        
        if len(images) > 0:
            counter += len(images)
            images = np.array(images)
            # PREDICT LABELS
            predicted_labels = []
            prediction_scores = model.predict(images)
            
            for score in prediction_scores:
                predicted_index = np.argmax(score)
                predicted_labels.append(class_names[predicted_index])
            
            # SAVE FILENAMES & PREDICTED LABELS TO A DATAFRAME
            image_df = pd.DataFrame(list(zip(filenames, predicted_labels)), columns =['filenames', 'predicted_labels'])
            
            # LOOP THROUGH IMAGE DF, UPDATE EACH IMAGE'S METADATA
            for i, row in image_df.iterrows():
                print('\nUpdate predicted for {} in Bucket {}'.format(row['filenames'],bucket))
                metadata = s3.head_object(Bucket=bucket, Key=row['filenames']).get('Metadata')
                metadata.update({'predictedlabel':row['predicted_labels']})
                contenttype = s3.head_object(Bucket=bucket, Key= filename).get('ContentType')
                
                if ('binary'in contenttype) and ('.png' in filename):
                    print(f'Bucket {bucket}: Update content-type image/png for file {filename}')
                    s3.copy_object(Key=filename, Bucket=bucket,
                                   CopySource={"Bucket": bucket, "Key": filename},
                                   Metadata=metadata,
                                   ACL='public-read',
                                   ContentType='image/png',
                                   MetadataDirective="REPLACE")
                elif ('binary'in contenttype) and (('.jpg' in filename) or ('.jpeg' in filename)):
                    print(f'Bucket {bucket}: Update content-type image/jpeg for file {filename}')
                    s3.copy_object(Key=filename, Bucket=bucket,
                                   CopySource={"Bucket": bucket, "Key": filename},
                                   Metadata=metadata,
                                   ACL='public-read',
                                   ContentType='image/jpeg',
                                   MetadataDirective="REPLACE")
        else:
            print('\nAll objects in bucket {} already had predicted labels.'.format(bucket))
    
    print('\nOn {}, prediction was performed and metadata was updated for {} images'.format(
        datetime.datetime.today().date(), counter))