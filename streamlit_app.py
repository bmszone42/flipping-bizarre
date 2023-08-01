import yfinance as yf
import streamlit as st
import pandas as pd 
import numpy as np
import plotly.express as px
from datetime import datetime

# Download historical data and cache
@st.cache_data
def download_data(symbols, years):
    data = {}
    end = datetime.today()
    start = end - pd.DateOffset(years=years)
    for symbol in symbols:
        data[symbol] = yf.download(symbol, start=start, end=end)
    return data

# Extract dividend data 
def get_dividends(df):
    div_cols = [col for col in df.columns if 'Dividend' in col]
    return df[div_cols]

# Calculate days to reach dividend target 
def get_days_to_target(divs, prices, targets):

    days = {}
    
    for target in targets:
      
        # Extract scalar dividend value
        div = divs.iloc[0,0]  
        
        days[f'{target*100}%'] = min(i for i, price in enumerate(prices) if price > target * div)
        
    return days

# App title
st.title('Dividend Stock Analysis')  

# Sidebar with controls
st.sidebar.header('Input')
years = st.sidebar.slider('Number of years', 1, 10, 5)  
symbols = st.sidebar.multiselect('Stock symbols', options=['T', 'MSFT', 'AAPL']) 

# Load data on demand
data = download_data(symbols, years)

# Analysis section
st.header('Analysis')
for symbol in symbols:

    # Print stock name  
    st.subheader(symbol)
    
    # Plot historical prices
    prices = data[symbol]['Close']
    fig = px.line(prices)
    st.plotly_chart(fig)

    # Extract dividends
    divs = get_dividends(data[symbol])
    
    # Plot dividends
    fig = px.bar(divs, x=divs.index, y=divs.columns)
    st.plotly_chart(fig)
    
    # Dividend targets 
    targets = [0.5, 0.75, 1.0]
    results = get_days_to_target(divs, prices, targets)

    # Print days to target
    st.write(pd.DataFrame(results, index=[f'{t*100}%' for t in targets]))
    
# Combined view 
st.header('Combined view')
combined = pd.concat([get_dividends(data[symbol]) for symbol in symbols], axis=1)
st.write(combined)
