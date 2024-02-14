# Web Scraping and Image Analysis

## Project Description
* For the master's thesis I wrote in 2023, I asked a research question about user-generated content, specifically about review photos. Those are photos that users post on review platforms like TripAdvisor together with their review texts. In this demo, I showed how I performed web scraping with Python to collect the data for my research.
* In a following step, I demonstrated how I performed image analyses on the photos I gathered from TripAdvisor to gain insights from the user-generated photos. In particular, I was trying to extract (several) photographic attributes from the images, e.g. brightness, contrast etc.

## Workflow Summary
1. On TripAdvisor, a destination (city) is selected, e.g. [Amsterdam](https://www.tripadvisor.com/Restaurants-g188590-Amsterdam_North_Holland_Province.html). On this URL about restaurants in Amsterdam, a list of restaurant suggestions is given. For each restaurant, I scrap its name, category (either cheap eats, mid-range or fine dining) and the URL to the restaurant's own page on TripAdvisor. Eventually, all of this data is saved in a csv file.
