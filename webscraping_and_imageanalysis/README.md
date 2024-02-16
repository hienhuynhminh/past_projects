# Web Scraping and Image Analysis

## Project Description
* For the master's thesis I wrote in 2023, I asked a research question about user-generated content, specifically about review photos. When a reviewer writes about his/her experience at a restaurant and post it on platforms like TripAdvisor, he/she might attach several images (i.e. review photos). In this demo, I show how I performed web scraping to gather the restaurant reviews, including review photographs, with Python in order to obtain the data for my research.
* Once I gathered the review photos, in a following step, I performed several image analyses to extract *photographic attributes* from the images, for example, brightness, contrast, colorfulness etc.

## Workflow Summary
### Script 1: ```ScrapeRestaurants.py```
* On TripAdvisor, a destination (city) is selected, e.g. [Amsterdam](https://www.tripadvisor.com/Restaurants-g188590-Amsterdam_North_Holland_Province.html). On this URL about restaurants in Amsterdam, a list of restaurant suggestions is given. For each restaurant, I scrap its name, category (either cheap eats, mid-range or fine dining) and the URL to the restaurant's own page on TripAdvisor. Eventually, all of this data is saved in a csv file.

### Script 2: ```ScrapeReviews.py```
* The output of Script 1 is a table (in a csv file) that contains numerous restaurants in Amsterdam. For each restaurant (i.e. URL to the restaurant page on TripAdvisor, I scrap the reviews written about this restaurant. Each review is an observation (row) in the table, which is eventually saved as a csv file.
* The tables for restaurant reviews contain the following columns:
  1. restaurant name
  2. restaurant address
  3. restaurant category (either cheap eats, mid-range or fine dining)
  4. review id
  5. date
  6. title
  7. text
  8. rating (i.e. points given by the reviewer)
  9. photo url (link to the photo posted in the review, e.g. [https://media-cdn.tripadvisor.com/media/photo-s/1a/2c/55/35/cafe-bedier.jpg](https://media-cdn.tripadvisor.com/media/photo-s/1a/2c/55/35/cafe-bedier.jpg))
* For both Script 1 and Script 2, web scraping was performed by using the package ```Selenium``` in Python.

### Script 3: 

