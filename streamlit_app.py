import yfinance as yf
import streamlit as st
import pandas as pd 
import numpy as np
import plotly.express as px
from datetime import datetime

# Fetching the historical data
def download_data(symbols):
    data = {}
    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        
        # get stock price data
        data[symbol] = ticker.history(period='max')
        
        # get dividends
        data[symbol]['Dividends'] = ticker.dividends
    return data

# Extracting the dividend data
def get_dividends(df):
    if 'Dividends' in df.columns:
        return df[['Dividends']]
    else:
        return pd.DataFrame()


# Calculating the days to reach dividend target
def get_days_to_target(divs, prices, targets):
    div = divs.iloc[0,0]
    return {f'{target*100}%': min(i for i, price in enumerate(prices) if price > target * div) for target in targets}

def setup_streamlit():
    st.title('Dividend Stock Analysis')  
    st.sidebar.header('Input')

    # Default symbols set to the five dividend-paying stocks
    symbols = st.sidebar.multiselect('Stock symbols', options=['KO', 'PG', 'JNJ', 'MCD', 'PEP'], default=['KO', 'PG', 'JNJ', 'MCD', 'PEP']) 

    # Add text input for additional stock symbols
    new_symbol = st.sidebar.text_input('Add a stock symbol', '')

    # Add a 'Search Now' button
    search_button = st.sidebar.button('Search Now')

    return symbols, new_symbol, search_button


def main():
    symbols, new_symbol, search_button = setup_streamlit()

    # If 'Search Now' is clicked, add the new symbol to the symbols list
    if search_button and new_symbol:
        symbols.append(new_symbol)

    data = download_data(symbols)

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
