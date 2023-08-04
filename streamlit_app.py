import yfinance as yf
import streamlit as st
import pandas as pd 
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

TARGETS = [0.5, 0.75, 1.0] 

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
            stock_info = ticker.info

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

def setup_streamlit():
    st.title('Dividend Stock Analysis')  
    st.sidebar.header('Input')

    # Add a dropdown to select period
    period = st.sidebar.selectbox('Period', options=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'], index=10)

    # Default symbols set to the five dividend-paying stocks
    symbols = st.sidebar.multiselect('Stock symbols', options=['KO', 'PG', 'JNJ', 'MCD', 'PEP'], default=['KO', 'PG', 'JNJ', 'MCD', 'PEP']) 

    # Add text input for additional stock symbols
    new_symbol = st.sidebar.text_input('Add a stock symbol', '')

    # Add a dropdown to select plot color
    color = st.sidebar.selectbox('Select plot color', options=['red', 'green', 'blue', 'purple'], index=0)

    # Add a 'Search Now' button
    search_button = st.sidebar.button('Search Now')

    return period, symbols, new_symbol, search_button, color

def show_dividend_targets(dividends, prices):
    targets = [price * (1 + tgt) for tgt in TARGETS]

    for target in targets:
        days_to_target = days_to_reach(prices, target)
        if not np.isnan(days_to_target):
            st.write(f"Days to {target:.2f}: {days_to_target}")
        else:
            st.write(f"Target {target:.2f} not reached.")

    
def perform_analysis(symbol, data, color, new_df):
    st.subheader(symbol)

    prices = data[symbol][['Close']]
    fig = px.line(prices, line_shape="linear", color_discrete_sequence=[color])
    fig.update_yaxes(title='Closing Price ($)')

    # Add a title to the price/date chart
    fig.update_layout(title=f'Price Over Time for {symbol}', xaxis_title='Date')

    divs = get_dividends(data[symbol])
    if not divs.empty:
        div_dates = divs[divs['Dividends'] > 0].index.drop_duplicates()  # Keep only unique dividend payment dates with dividends greater than 0

        if not div_dates.empty:
            # Add stars to the price graph for dividend payment dates with dividends greater than 0
            fig.add_trace(go.Scatter(x=div_dates, y=prices.loc[div_dates, 'Close'], mode='markers', marker=dict(symbol='star', size=12, color=color, line=dict(width=2, color='DarkSlateGrey')), name=symbol + ' dividend'))

            st.plotly_chart(fig)

            # Display the DataFrame with the dividend dates and closing price on those dates
            div_dates_with_prices = divs[divs['Dividends'] > 0].join(prices, how='inner')
            st.write("Dividend Dates with Closing Prices:")
            st.write(div_dates_with_prices)

            # Add a title to the div/date chart
            div_chart_title = f'Dividends Over Time for {symbol}'
            plot_dividends(divs, color, title=div_chart_title)
            
        else:
            st.write("No dividend data available for this stock.")
    else:
        st.write("No dividend data available for this stock.")
    
def plot_dividends(divs, color, title=None):
    fig = go.Figure()
    for column in divs.columns:
        fig.add_trace(go.Bar(x=divs.index, y=divs[column], name=column, marker_color=color))
    fig.update_layout(yaxis_title="Price ($)", title=title)  # Set the title for the dividends chart
    st.plotly_chart(fig)

def get_dividend_for_date(div_data, date):
    for div_date, div in div_data:
        if div_date == date.strftime("%Y-%m-%d"):
            return div
    return None

# Calculate days to reach each target  
def days_to_reach_targets(prices, divs):
    print("Prices DataFrame:")
    print(prices.head())

    print("Dividends DataFrame:")
    print(divs.head())

    results = []

    # Match dividend dates to prices
    prices = prices.reindex(divs.index)
    prices = prices.fillna(method='ffill')

    for date, div in divs.items():
        if div > 0:
            price = prices.loc[date]
            targets = [price * (1 + tgt) for tgt in TARGETS]

            days = [days_to_reach(prices.loc[date:], tgt) for tgt in targets]

            result = [date] + days
            results.append(result)

    return pd.DataFrame(results, columns=["Date", "Days to 50%", "Days to 75%", "Days to 100%"])


# Helper function    
def days_to_reach(prices, target):
    # Returns NaN if target not reached
    idx = np.argmax(prices >= target)
    if idx == 0 and prices[0] < target:
        print(f"Target {target} not reached in prices.")
        return np.nan
    return idx


def analyze_dividends(symbol, prices, dividends):
    results = days_to_reach_targets(prices, dividends)

    # Check index is set properly
    results.set_index('Date', inplace=True)

    # Filter dividend dates with dividends greater than 0
    div_dates = dividends[dividends > 0].index

    # Calculate 50% higher closing price dates and values
    results['Dividend Paid'] = dividends[dividends > 0]
    results['Closing Price on Dividend Day'] = prices.loc[div_dates, 'Close']
    results['50% Higher Closing Price'] = prices.loc[div_dates, 'Close'] * 1.5
    results['Date of 50% Increase'] = pd.to_datetime(np.nan)

    # Calculate days to reach 50% higher closing price
    for idx, row in results.iterrows():
        start_date = idx
        end_date = results.loc[idx, 'Date of 50% Increase']

        if np.isnan(end_date):
            days_to_50_percent = days_to_reach(prices[start_date:], row['50% Higher Closing Price'])
            if not np.isnan(days_to_50_percent):
                end_date = start_date + pd.Timedelta(days=days_to_50_percent)
                results.at[idx, 'Date of 50% Increase'] = end_date

    st.write(results)  # inspect results dataframe

    
def main():
    params = setup_streamlit()
    if params is None:
        return

    period, symbols, new_symbol, search_button, color = params

    # If 'Search Now' is clicked, add the new symbol to the symbols list
    if search_button and new_symbol:
        symbols.append(new_symbol)

    data = download_data(symbols, period)
    st.header('Data view')
    
    # Displaying the first 5 rows for each stock in the DataFrame
    for symbol, df in data.items():
        st.subheader(symbol)
        st.write(df)

     # Create a new DataFrame 'new_df' with specified columns from ticker.info
    new_df_data = []
    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        stock_info = ticker.info
        new_row = {
            "previousClose": stock_info.get("previousClose"),
            "open": stock_info.get("open"),
            "dayLow": stock_info.get("dayLow"),
            "dayHigh": stock_info.get("dayHigh"),
            "exchange": stock_info.get("exchange"),
            "quoteType": stock_info.get("quoteType"),
            "symbol": stock_info.get("symbol"),
            "targetHighPrice": stock_info.get("targetHighPrice"),
            "targetLowPrice": stock_info.get("targetLowPrice"),
            "targetMeanPrice": stock_info.get("targetMeanPrice"),
            "targetMedianPrice": stock_info.get("targetMedianPrice"),
        }
        new_df_data.append(new_row)

    new_df = pd.DataFrame(new_df_data)

    # Display the new DataFrame 'new_df'
    st.header('New DataFrame - ticker.info Data')
    st.write(new_df.head())

    st.header('Analysis')
    for symbol in symbols:
        try:
            perform_analysis(symbol, data, color, new_df)
        except Exception as e:
            print("Error occurred in perform_analysis:", e)  # Debug print statement

      # Analyze each symbol
    for symbol in symbols:
  
        prices = data[symbol]['Close']
        dividends = data[symbol]['Dividends']
        st.write('Dividend Analysis')
        analyze_dividends(symbol, prices, dividends)

    st.header('Combined view')
    combined = pd.concat([data[symbol][f'{symbol}_Dividends'] for symbol in symbols], axis=1)
    st.write(combined)

if __name__ == "__main__":
    main()
