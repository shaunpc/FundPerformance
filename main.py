#
#  Fund Performance Analysis
#
#
from scrapeData import scrape_data
import pandas as pd

# === Scrape the web data ===
scrape_data(10, 'funds_10.csv')

# df = pd.read_csv('funds_3500.csv', encoding='utf-8')
# print(df)
