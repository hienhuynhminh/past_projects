# Data Integration into Shopify


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
* This script contains the main function to compare the current lists of recommendations with the newly generated lists of recommendations, two functions to make API calls to Shopify (one to create new metafields, and another to update existing metafields), as well as some supporting functions.

### Script 2: ```upsell_recommendations_to_shopify.py```
* This script was written to apply the functions in Script 1. Here, the parameters for these functions are provided, for example, table names for new and current lists of recommendations in Google BigQuery, or API keys/passes to interact with Shopify.

### Script 3: ```upselling_metafields_dag.py```
* In this script, a DAG is created to trigger Airflow to automate the process in Script 2.
