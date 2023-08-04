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

# Modified dividend metrics function
def calculate_dividend_metrics(divs, prices):

  clean_prices = prices.dropna().values
  high_prices = [clean_prices[max(i-365, 0):i] for i in range(1, len(clean_prices))]

  results = []
  for date, div in divs.iterrows():
    target_prices = [div * (1 + target) for target in TARGETS]
    days_to_targets = [days_to_reach(hp, tp) for hp, tp in zip(high_prices, target_prices)]
    averages = [mean(col) for col in zip(*days_to_targets)]

    result = [date.year, *averages]
    results.append(result)
  
  return results

# Simplified show targets  
def show_dividend_targets(divs, prices):
  results = calculate_dividend_metrics(divs, prices)
  targets = [f"{target*100}%" for target in TARGETS]
  df = pd.DataFrame(results, columns=["Year", *targets])
  st.write(df)

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

            quote_data, results = calculate_dividend_metrics(divs, prices)
            st.write("Dividend Targets:") 
            st.write(results)
        
        else:
            st.write("No dividend data")
      
        st.plotly_chart(fig)

        # Display the DataFrame with the dividend dates and closing price on those dates
        div_dates_with_prices = divs[divs['Dividends'] > 0].join(prices, how='inner')
     
        # Loop through each dividend date and add rows from new_df for that date
        for date in div_dates_with_prices.index:
            symbol_row = new_df[new_df['symbol'] == symbol]
            symbol_row['date'] = date
            div_dates_with_prices = pd.concat([div_dates_with_prices, symbol_row], axis=0)

        st.write("Dividend Dates with Closing Prices, Price Targets, and Analyst Targets:")
        st.write(div_dates_with_prices)

        # Add a title to the div/date chart
        div_chart_title = f'Dividends Over Time for {symbol}'
        plot_dividends(divs, color, title=div_chart_title)

        show_dividend_targets(divs, prices)
        quote_data, results = calculate_dividend_metrics(divs, prices)
        st.write("Dividend Metrics:")
        st.write(pd.DataFrame(results, columns=["Year", "To Reach 50%", "To Reach 75%", "To Reach 100%"]))
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

    st.header('Combined view')
    combined = pd.concat([data[symbol][f'{symbol}_Dividends'] for symbol in symbols], axis=1)
    st.write(combined)

if __name__ == "__main__":
    main()
