#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 25 16:52:42 2023

@author: hienhuynh
"""

#%% IMPORT PYTHON LIBRARIES
import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager



#%% FUNCTION
def scrape_restaurants(url,pages_to_scrape):
    # REGULAR EXPRESSION
    regex = re.compile('[a-zA-Z]')
    # DRIVER
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url)
    
    # ACCEPT PRIVACY OPTION
    time.sleep(18)
    driver.find_element("xpath",".//button[@id='onetrust-accept-btn-handler']").click()
    
    # EMPTY DATAFRAME TO STORE DATA
    restaurant_df = pd.DataFrame(columns=["RESTAURANT_URL",
                                          "RESTAURANT_NAME",
                                          "RESTAURANT_CATEGORY"])
    
    idx = 0
    for p in range(0,pages_to_scrape):
        print("Page: {p}/{pages_to_scrape}".format(
            p=p+1,
            pages_to_scrape=pages_to_scrape))
        time.sleep(2)
        names = driver.find_elements("xpath","//div[@class='biGQs _P fiohW alXOW NwcxK GzNcM ytVPx UTQMg RnEEZ ngXxk']")
        urls = driver.find_elements("xpath","//a[@class='BMQDV _F Gv wSSLS SwZTJ FGwzt ukgoS']")
        urls = urls[-len(names):]
        categories = driver.find_elements("xpath","//span[@class='YECgr']")
        categories = categories[-len(names):]
        for i in range(len(names)):
            restaurant_name = names[i].text.split(". ", 1)[-1]
            restaurant_url = urls[i].get_attribute('href')
            restaurant_category = regex.sub("",categories[i].text).replace("\n","").replace(",","").strip()
            restaurant_df.loc[idx] = [restaurant_url,restaurant_name,restaurant_category]
            idx += 1
            time.sleep(0.5)
        
        # CLICK ON "NEXT" BUTTON TO MOVE TO NEXT PAGE
        #button = WebDriverWait(driver, 60).until(
        #    EC.element_to_be_clickable(("xpath",".//a[@class='nav next rndBtn ui_button primary taLnk']")))
        #driver.execute_script('arguments[0].click()', button)
    driver.quit()
    return restaurant_df


#%% IMPLEMENTATION

url = 'https://www.tripadvisor.com/Restaurants-g188590-Amsterdam_North_Holland_Province.html'
pages_to_scrape = 118
restaurant_df = scrape_restaurants(url,pages_to_scrape)
# SAVE AS A CSV FILE
restaurant_df.to_csv("./data/list_restaurants_amsterdam.csv",index=False)
