import yfinance as yf
import streamlit as st
import pandas as pd 
import numpy as np
import plotly.express as px
from datetime import datetime

# Fetching the historical data
@st.cache_data
def download_data(symbols, period='max'):
    data = {}
    for symbol in symbols:
        try:
            # Check if the symbol is valid
            if not yf.Ticker(symbol).info:
                st.error(f"Invalid symbol: {symbol}. Please check if the symbol is correct.")
                continue
            
            ticker = yf.Ticker(symbol)
            history = ticker.history(period=period)
            dividends = ticker.dividends.rename(f'{symbol}_Dividends')
            df = pd.concat([history, dividends], axis=1)
            data[symbol] = df
        except:
            st.error(f"Failed to download data for symbol: {symbol}. Please check if the symbol is correct.")
    return data


# Extracting the dividend data
def get_dividends(df):
    if 'Dividends' in df.columns:
        return df[['Dividends']]
    else:
        return pd.DataFrame()


# Calculating the days to reach dividend target
def get_days_to_target(divs, prices, targets):
    if divs.empty:
        return {f'{target*100}%': None for target in targets}
    else:
        div = divs.iloc[0,0]
        return {f'{target*100}%': min((i for i, price in enumerate(prices) if price > target * div), default=None) for target in targets}

def setup_streamlit():
    st.title('Dividend Stock Analysis')  
    st.sidebar.header('Input')

    # Add a dropdown to select period
    period = st.sidebar.selectbox('Period', options=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'], index=10)

    # Default symbols set to the five dividend-paying stocks
    symbols = st.sidebar.multiselect('Stock symbols', options=['KO', 'PG', 'JNJ', 'MCD', 'PEP'], default=['KO', 'PG', 'JNJ', 'MCD', 'PEP']) 

    # Add text input for additional stock symbols
    new_symbol = st.sidebar.text_input('Add a stock symbol', '')

    # Add a 'Search Now' button
    search_button = st.sidebar.button('Search Now')

    # Add a dropdown to select plot color
    color = st.sidebar.selectbox('Select plot color', options=['red', 'green', 'blue', 'purple'], index=0)

    return period, symbols, new_symbol, search_button, color

def main():
    params = setup_streamlit()
    if params is None:
        return

    period, symbols, new_symbol, search_button, color = params

    # If 'Search Now' is clicked, add the new symbol to the symbols list
    if search_button and new_symbol:
        symbols.append(new_symbol)

    data = download_data(symbols, period)

    st.header('Analysis')
    for symbol in symbols:
        perform_analysis(symbol, data, color)

    st.header('Combined view')
    combined = pd.concat([data[symbol][f'{symbol}_Dividends'] for symbol in symbols], axis=1)
    st.write(combined)
    
def perform_analysis(symbol, data, color):
    st.subheader(symbol)

    prices = data[symbol]['Close']
    fig = px.line(prices, line_shape="linear", color_discrete_sequence=[color])
    fig.update_yaxes(title='Price (Dollars)')
    st.plotly_chart(fig)

    divs = get_dividends(data[symbol])
    if not divs.empty:
        plot_dividends(divs, color)
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
