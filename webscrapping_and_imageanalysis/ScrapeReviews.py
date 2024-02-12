#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  9 13:57:01 2023

@author: hienhuynh
"""

#%% IMPORT PYTHON LIBRARIES
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time


#%%
# FUNCTION TO SCRAPE REVIEWS
def scrape_reviews(url,pages_to_scrape,restaurant_name,restaurant_category):
    # WEBDRIVER OPTIONS
    options = webdriver.ChromeOptions() 
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # WEBDRIVER
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url)
    
    # ACCEPT PRIVACY OPTION
    time.sleep(59)
    driver.find_element("xpath",".//button[@id='onetrust-accept-btn-handler']").click()
    
    # SELECT REVIEWS OF ALL LANGUAGES
    driver.find_element("xpath",".//label[@for='filters_detail_language_filterLang_ALL']").click()
    time.sleep(4)
    
    # RESTAURANT ADDRESS
    address_element = driver.find_elements("xpath","//a[@class='AYHFM']")
    restaurant_address = [a.text for a in address_element if "The Netherlands" in a.text][-1]
    
    # EMPTY DATAFRAME WITH COLUMN NAMES
    columns = ["RESTAURANT_NAME","RESTAURANT_ADDRESS","RESTAURANT_CATEGORY",
               "REVIEW_ID","DATE","TITLE","TEXT","RATING","PHOTO_URL"]
    reviews_df = pd.DataFrame(columns=columns)
    
    idx = 0
    page = 0
    while page < pages_to_scrape:
        print("Restaurant: {restaurant_name}\t\tPage: {page}".format(
            restaurant_name=restaurant_name,
            page=page+1))
        
        
        # RESTAURANT REVIEW
        try:
            container = driver.find_elements("xpath","//div[@class='review-container']")
            for i in range(0,len(container)):
                # EMPTY LIST TO STORE DATA
                lst = []
                # REVIEW ID
                review_id = container[i].get_attribute("data-reviewid")
                
                # REVIEW DATE
                review_date = container[i].find_element(
                    "xpath",".//span[contains(@class, 'ratingDate')]").get_attribute("title")
                
                # REVIEW TITLE
                review_title = container[i].find_element(
                    "xpath",".//span[contains(@class, 'noQuotes')]").text
                
                # REVIEW TEXT
                review_text_element = container[i].find_element(
                    "xpath",".//p[@class='partial_entry']")
                review_text = review_text_element.text
                # Post Snippet
                post_snippet = ""
                review_text_element_children = review_text_element.find_elements(
                    "xpath",".//*")
                for j in range(len(review_text_element_children)):
                    if review_text_element_children[j].get_attribute("class")=="postSnippet":
                        post_snippet = review_text_element_children[j].get_attribute("innerHTML")
                        review_text = " ".join([review_text,post_snippet])
                review_text = review_text.replace("...More","")
                
                # REVIEW RATING
                review_rating = container[i].find_element(
                    "xpath",".//span[contains(@class, 'ui_bubble_rating bubble_')]").get_attribute(
                        "class").split("_")[3]
                
                # SCROLL TO REVIEW
                review = driver.find_element(
                    "xpath","//div[@data-reviewid='{review_id}']".format(
                        review_id=review_id))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});",review)
                
                # REVIEW IMAGES
                photos_wrapper = container[i].find_elements(
                    "xpath",".//div[@class='inlinePhotosWrapper']")
                review_photos = []
                if photos_wrapper != []:
                    photos_wrapper_children = photos_wrapper[-1].find_elements(
                        "xpath",".//*")
                    for k in range(len(photos_wrapper_children)):
                        if photos_wrapper_children[k].tag_name == "img":
                            review_photos.append(photos_wrapper_children[k].get_attribute("src"))
                if review_photos == []:
                    review_photos = ""
                else:
                    review_photos = list(set(review_photos))
                lst = [restaurant_name,restaurant_address,restaurant_category,
                       review_id,review_date,review_title,review_text,review_rating,
                       review_photos]
                reviews_df.loc[idx] = lst
                idx += 1
            page += 1
        except:
            print('\tRetry page {page}'.format(page=page+1))
            continue
        try:
            time.sleep(2)
            driver.find_elements(
                "xpath",".//a[@class='nav next ui_button primary']")[0].click()
            time.sleep(3)
        except:
            break
    # CLOSE THE CURRENT WINDOW
    driver.close()
    
    reviews_df = reviews_df.explode("PHOTO_URL")
    # DROP DUPLICATES (IF ANY)
    reviews_df = reviews_df.drop_duplicates(keep='first')
    reviews_df = reviews_df.reset_index(drop=True)
    return reviews_df


#%%
# READ RESTAURANT CSV
restaurant_df = pd.read_csv("./data/list_restaurants_amsterdam.csv")

# START REVIEW SCRAPING
pages_to_scrape = 200
for idx, row in restaurant_df.iterrows():
    restaurant_name = row['RESTAURANT_NAME']
    restaurant_category = row['RESTAURANT_CATEGORY']
    url = row['RESTAURANT_URL']
    review_df = scrape_reviews(url,pages_to_scrape,restaurant_name,restaurant_category)
    #review_df.to_csv('./data/reviews/{restaurant_name}.csv'.format(
    #    restaurant_name=restaurant_name),
    #    index=False)
    time.sleep(1)