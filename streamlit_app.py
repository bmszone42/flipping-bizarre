import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

st.title('Dividend Investing Analysis')

# Function to get dividend and historical data 
@st.cache
def get_data(ticker):
    dividends = yf.Ticker(ticker).dividends
    hist = yf.Ticker(ticker).history(period="max")
    return dividends, hist

# Function to analyze data
def analyze(dividends, hist, num_years):
    
    results = []
    
    for year in range(num_years):
        y = datetime.today().year - year
        
        # Filter to dividends paid in given year
        divs = dividends[dividends.index.year==y]
        
        # Get historical prices around dividend dates
        analysis = []
        for i, row in divs.iterrows():
            s = row.name - timedelta(days=10)
            e = row.name + timedelta(days=90)
            prices = hist.loc[s:e]['Close']
            
            # Calculate days to recovery
            amt = row['Dividends']
            targets = [prices.iloc[0] + 0.5*amt, prices.iloc[0] + 0.75*amt, prices.iloc[0] + amt]
            days = [0,0,0]
            for p in prices:
                if p >= targets[0] and days[0]==0: days[0] = 1
                if p >= targets[1] and days[1]==0: days[1] = 1 
                if p >= targets[2] and days[2]==0: days[2] = 1
            analysis.append(days)
        
        # Average the days        
        avg = [sum(x)/len(x) for x in zip(*analysis)]
        results.append(avg)
        
    return results
            
# Streamlit app
st.header('Parameters')
ticker = st.text_input('Enter a ticker', value='T')  
years = st.slider('Number of years', 1, 10, 5)

if st.button('Analyze'):

    with st.spinner('Fetching data...'):
        dividends, hist = get_data(ticker)

    results = analyze(dividends, hist, years)

    st.header('Results')
    for i, result in enumerate(results):
        st.write(f'Year {datetime.today().year-i}') 
        st.write(f'Days to recover 50%: {result[0]:.2f}')
        st.write(f'Days to recover 75%: {result[1]:.2f}')
        st.write(f'Days to recover 100%: {result[2]:.2f}')
