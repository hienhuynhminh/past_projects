# Image Classification (with Images in AWS S3)

## Project Description
* An e-commerce business runs a webshop to advertise their furniture products. Hence, each product is displayed with several images. The images can be categorised into different classes, for example, product images (e.g. a wooden chair with a white background) or ambient images (e.g. a couch being placed in a living room with other items like a coffee table or a lamp).
* A machine learning model (a convolutional neural network) was trained to classify these types of images. Performance was fairly good (the accuracy rate was high), therefore, we decided to deploy the model on our production data.
* In this demo, I show how I deployed the model to perform the image classification task on the product images. As a matter of fact, the images shown on the website are objects which are stored in various buckets in AWS S3.

## Python Scripts
### Script 1: ```image_classification_workflow.py```
In this script, the image classification task is divided into the following (main) steps:
* The CNN model is loaded.
* Connect to AWS S3, using an ```access_key``` and a ```secret_key```.
* Get all 'buckets' from AWS S3, each bucket contains photos from a specific supplier/brand.
* For each bucket, retrieve the items in the bucket. These items meet 2 criteria: (1) item is an image and (2) the metadata ```predictedlabel``` of item is an empty value (i.e. this item does not have a label yet).
* Get two outputs: a NumPy array which contains all the images in the bucket and a dataframe that contains the metadata of each image (e.g. filename, url to image etc.)
* With the NumPy array of images, task the model to perform prediction (image classification). Save results to the dataframe.
* Loop through dataframe, for each ```filename```, update the metadata with the predicted label.

### Script 2: ```image_classification_dag.py```
Using Airflow to automate the image classification workflow.
