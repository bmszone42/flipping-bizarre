import yfinance as yf 
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

# Helper functions

def add_years(d, years):
    try: 
        return d.replace(year = d.year + years)
    except ValueError:
        return d + (datetime(d.year + years, 1, 1) - datetime(d.year, 1, 1))
        
def get_year(d):
    return d.year

@st.cache_data    
def download_data(stocks, years):
    data = {}
    for stock in stocks:
        data[stock] = yf.Ticker(stock).history(period=f"{years}y")
    return data
    
def div_columns(df):
    return [col for col in df.columns if col.startswith('Dividend')]

# Main app 

st.title('Dividend Analysis')

years = st.slider('Number of years', 1, 10, 5)
stocks = st.text_input('Enter stock symbols separated by space')

if stocks:
    stocks = stocks.split()   
    
    data = download_data(stocks, years + 1)
    
    st.write('## Historical Prices')
    for stock in stocks:
        fig = px.line(data[stock]['Close'])
        st.plotly_chart(fig, use_container_width=True)
        
    # Dividend data
    dividends = {}
    for stock in stocks:
        divs = data[stock].loc[:, div_columns(data[stock])]
        divs.columns = [get_year(col) for col in divs.columns] 
        dividends[stock] = divs
    
    st.write('## Dividends')        
    for stock in stocks:
        fig = px.bar(dividends[stock], x=dividends[stock].index, y=dividends[stock].columns)
        st.plotly_chart(fig, use_container_width=True)
        
    # Aggregate dividends 
    agg_divs = pd.concat(dividends, axis=1)
    agg_divs.columns = stocks
    st.write(agg_divs)
        
else:
    st.write('Enter symbols above')
