# analysis.py

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_data(ticker):

    dividends = yf.Ticker(ticker).dividends    
    prices = yf.Ticker(ticker).history(period='max')[['Close']]

    return dividends, prices

def analyze(dividends, prices, years):

    results = []

    for year in range(years):
      
        # Fix 1: Convert to DataFrame
        divs = dividends[dividends.index.year==2021-year].reset_index(drop=False)

        data = []
        for _, div in divs.iterrows():

            # Fix 2: Use Date column 
            date = div['Date']
            start = date - timedelta(days=10)
            end = date + timedelta(days=90)

            window = prices.loc[start:end]

            amt = div['Dividends']
            thresholds = [window.iloc[0] + 0.5*amt, window.iloc[0] + 0.75*amt, window.iloc[0] + amt]

            days = [0,0,0]

            # Fix 3: Compare element-wise
            for i, p in enumerate(window['Close']):
                if p >= thresholds[0] and days[0] == 0:
                    days[0] = i+1
                if p >= thresholds[1] and days[1] == 0:
                    days[1] = i+1
                if p >= thresholds[2] and days[2] == 0:  
                    days[2] = i+1

            data.append(days)

        avg = [sum(col)/len(col) for col in zip(*data)]
        results.append(avg)

    return results
