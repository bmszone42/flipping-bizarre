# analysis.py
import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

@st.cache_data
def get_data(ticker):

    dividends = yf.Ticker(ticker).dividends
    prices = yf.Ticker(ticker).history(period='max')[['Close']]

    return dividends, prices

def analyze(dividends, prices, years):

    results = []

    for year in range(years):

        # Filter dividends 
        divs = dividends[dividends.index.year==2021-year].reset_index()

        data = []
        for _, div in divs.iterrows():

            date = div['Date']
            
            start = date - timedelta(days=10)
            end = div.name + timedelta(days=90)
            window = prices.loc[start:end]

            amt = div['Dividends']  
            thresholds = [window.iloc[0] + 0.5*amt, window.iloc[0] + 0.75*amt, window.iloc[0] + amt] 

            days = [0, 0, 0]
            for i, p in enumerate(window['Close']):
                if p >= thresholds[0] and days[0] == 0: days[0] = i+1
                if p >= thresholds[1] and days[1] == 0: days[1] = i+1
                if p >= thresholds[2] and days[2] == 0: days[2] = i+1

            data.append(days)

        avg = [sum(col)/len(col) for col in zip(*data)]
        results.append(avg)

    return results
