import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

st.title('Dividend Stock Analysis')

stocks = st.text_input('Enter stock symbols separated by space')

if stocks:
    stocks = stocks.split()
    
    data = {}
    for stock in stocks:
        data[stock] = yf.Ticker(stock).history(period="max")
        
    st.write('## Historical Price Data')
    for stock in stocks:
        fig = px.line(data[stock]['Close'])
        st.plotly_chart(fig, use_container_width=True)
        
    st.write('## Dividend Data')
    div_data = {}
    for stock in stocks:
        div = data[stock].iloc[::-1][data[stock]['Dividends'] > 0]
        div.set_index('Date', inplace=True)
        div_data[stock] = div['Dividends']
        
        fig = px.bar(div, x=div.index, y='Dividends')
        st.plotly_chart(fig, use_container_width=True)
        
    agg_div = pd.DataFrame({stock: div_data[stock] for stock in stocks})  
    st.write(agg_div.reindex(sorted(agg_div.columns), axis=1))
    
else:
    st.write('Enter stock symbols above')
