# Data Integration into Shopify
*This project demo was part of the data engineering internship I did in 2022.*\\
Keywords:
* data manipulation (```pandas```)
* Google Cloud Platform, Google BigQuery
* API
* orchestration with Airflow

## Project Descriptions
* The company where I did my data engineering internship, NADUVI, is an e-commerce business and advertises home and living (i.e. furniture) products on their webshop. They build their e-commerce platform on Shopify.
* For each product, product information is provided to the viewers. For example, specifications of a furniture piece are detailed, including its height, breadth and width.
* In this project, the aim is to update upselling recommendations for every product in the inventory. These recommendations are products of a similar category to the target product, and are intended to enrich the customer's journey on NADUVI's site and increase the chance of their purchases.



## Workflow Summary
* Each product in the inventory has a Shopify metafield for similar product recommendations. This metafield is in the format of a list of products (product handles).
* These metafields, or lists of recommendations, are stored in a column a table in the data warehouse in Google BigQuery. We call this Table 1.
* New lists of recommendations are generated. This allows new products to enter the lists of recommendations. This process is done in a separate step and was created by another colleague. Then, these new lists are pushed to Table 2 in the data warehouse.
* We compare Table 1 with Table 2 to track changes in the lists of product recommendations. There are three possible outcomes:
1. For a given product, the metafield for recommendations is an empty value, i.e. { }, potentially because this product is new and no recommendations have not been generated for this product yet. As such, we take values from Table 2, push them to Shopify and create a new metafield for recommendations to display related products on Shopify.
2. For a given product, the current metafield for recommendations on Shopify which is stored in Table 1 is different from the new list of recommendations which is stored in Table 2. We use the values in Table 2 to make an update to the current metafield.
3. For a given product, the current metafield for recommendations on Shopify which is stored in Table 1 is **not** different from the new list of recommendations which is stored in Table 2. For this product, no update is needed.
* Depending on the outcome (as outlined above), an appropriate API call is made to communicate the changes to Shopify.

## Python Scripts
### Script 1: ```shopify_metafield_functions.py```
Script 1 contains a collection of functions:
* The main function is called ```create_requests```. It takes the table that stores current product information (i.e. current Shopify metafields) to compare with new product information (which has been generated in a separate step and stored in the ```df_tocompare``` dataframe). As a result, the function outputs two new dataframes. The first dataframe stores products which currently do not have the target metafields yet. The other dataframe stores products which currently have the target metafields, but the values in these metafields should be updated according to ```df_tocompare```.
* Two functions ```create_metafield``` and ```update_metafield``` generate API calls to either create or update metafields to products on Shopify.
* Other functions are support functions which serve data processing, cleaning, manipulation etc. purposes.

### Script 2: ```upsell_recommendations_to_shopify.py```
Script 2 takes the functions which were created in Script 1 (i.e. ```shopify_metafield_functions.py```) and generates a pipeline to integrate upselling recommendations into Shopify. Information specific to upselling recommendations (i.e. table names and columns in Google BigQuery, metafield namespaces and API keys and passes in Shopify) is detailed and provided to the functions from Script 1.

### Script 3: ```upselling_metafields_dag.py```
After the pipeline has been created in the previous script, Script 3 contains an Airflow DAG which schedules the pipeline to be executed automatically. Here, the cron expression ```0 0 * * 1``` states that the pipeline would be executed every Monday at 00:00. Moreover, the DAG is split into several "languages" (i.e. in a ```for``` loop) because the company operates in two domains .nl & .de.
