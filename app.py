# app.py

import streamlit as st
from analysis import get_data, analyze
import pandas as pd
import matplotlib.pyplot as plt

st.title('Dividend Analysis App')

ticker = st.text_input('Enter Stock Ticker', 'AAPL')
years = st.slider('Years to Analyze', 1, 10, 3)  

if st.button('Analyze'):

    with st.spinner('Fetching data...'):
        dividends, prices = get_data(ticker)

    results = analyze(dividends, prices, years)

    st.header('Results')
    for i, result in enumerate(results):
        st.write(f'Year {2021-i}') 
        st.write(f'Days to Recover 50%: {result[0]:.2f}')
        st.write(f'Days to Recover 75%: {result[1]:.2f}')  
        st.write(f'Days to Recover 100%: {result[2]:.2f}')

    # Plot average days to recover
    df = pd.DataFrame(results, columns=['50%', '75%', '100%'])
    ax = df.plot.bar(rot=0)
    ax.set_xlabel('Year')
    ax.set_ylabel('Days to Recover')
    st.pyplot(plt)
