import yfinance as yf
import streamlit as st
import pandas as pd 
import numpy as np
import plotly.express as px
from datetime import datetime

# Fetching the historical data
def download_data(symbols, years):
    end = datetime.today()
    start = end - pd.DateOffset(years=years)
    return {symbol: yf.download(symbol, start=start, end=end) for symbol in symbols}

# Extracting the dividend data
def get_dividends(df):
    div_cols = [col for col in df.columns if 'Dividend' in col]
    return df[div_cols] if div_cols else pd.DataFrame()

# Calculating the days to reach dividend target
def get_days_to_target(divs, prices, targets):
    div = divs.iloc[0,0]
    return {f'{target*100}%': min(i for i, price in enumerate(prices) if price > target * div) for target in targets}

# Streamlit setup
def setup_streamlit():
    st.title('Dividend Stock Analysis')  
    st.sidebar.header('Input')
    years = st.sidebar.slider('Number of years', 1, 10, 5)  
    symbols = st.sidebar.multiselect('Stock symbols', options=['T', 'MSFT', 'AAPL']) 
    return years, symbols

def main():
    years, symbols = setup_streamlit()
    data = download_data(symbols, years)

    st.header('Analysis')
    for symbol in symbols:
        perform_analysis(symbol, data)

    st.header('Combined view')
    combined = pd.concat([get_dividends(data[symbol]) for symbol in symbols], axis=1)
    st.write(combined)

def perform_analysis(symbol, data):
    st.subheader(symbol)
    
    prices = data[symbol]['Close']
    fig = px.line(prices)
    st.plotly_chart(fig)

    divs = get_dividends(data[symbol])
    if not divs.empty:
        plot_dividends(divs)
        show_dividend_targets(divs, prices)
    else:
        st.write("No dividend data available for this stock.")

def plot_dividends(divs):
    fig = px.bar(divs, x=divs.index, y=divs.columns)
    st.plotly_chart(fig)

def show_dividend_targets(divs, prices):
    targets = [0.5, 0.75, 1.0]
    results = get_days_to_target(divs, prices, targets)
    st.write(pd.DataFrame(results, index=[f'{t*100}%' for t in targets]))

if __name__ == "__main__":
    main()
