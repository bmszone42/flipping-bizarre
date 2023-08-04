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

    # Add a multiselect input for the number of weeks
    weeks = st.sidebar.multiselect('Weeks to check for price change', options=[1, 2, 3, 4, 5, 6, 7, 8, 9], default=[2, 4, 6])

    # Add a 'Search Now' button
    search_button = st.sidebar.button('Search Now')

    return period, symbols, new_symbol, search_button, color, weeks
  
def perform_analysis(symbol, data, color, new_df, weeks):
    st.subheader(symbol)

    prices = data[symbol][['Close']]
    fig = px.line(prices, line_shape="linear", color_discrete_sequence=[color])
    fig.update_yaxes(title='Closing Price ($)')

    fig.update_layout(title=f'Price Over Time for {symbol}', xaxis_title='Date')

    divs = get_dividends(data[symbol])
    if not divs.empty:
        div_dates = divs[divs['Dividends'] > 0].index.drop_duplicates()

        if not div_dates.empty:
            fig.add_trace(go.Scatter(
                x=div_dates,
                y=prices.loc[div_dates, 'Close'],
                mode='markers+text',
                marker=dict(
                    symbol='star',
                    size=12,
                    color='white',
                    line=dict(width=2, color='DarkSlateGrey')
                ),
                text=prices.loc[div_dates, 'Close'].round(2),
                textposition='top center',
                name=symbol + ' dividend')
            )

            div_dates = div_dates.sort_values()

            x_line = []
            y_line = []

            for i in range(len(div_dates)-1):
                x_line.append(div_dates[i])
                x_line.append(div_dates[i+1])

                y_line.append(prices.loc[div_dates[i], 'Close']) 
                y_line.append(prices.loc[div_dates[i+1], 'Close'])

            fig.add_trace(go.Scatter(
                x=x_line,
                y=y_line,
                mode='lines',
                line=dict(color='white', width=2),
                showlegend=False
            ))

            st.plotly_chart(fig)

            div_dates = div_dates.tz_convert(prices.index.tz)
            dates_with_prices = pd.DataFrame()
            dates_with_prices['Dividend Date'] = div_dates
            dates_with_prices['Dividend Date'] = dates_with_prices['Dividend Date'].dt.strftime('%Y-%m-%d')

            dates_with_prices = dates_with_prices.set_index('Dividend Date')
            dates_with_prices['Dividend'] = divs.loc[div_dates, 'Dividends'].values

            try:
                dates_with_prices['Closing Price'] = prices.loc[div_dates, 'Close'].values
            except KeyError:
                dates_with_prices['Closing Price'] = prices.nearest(div_dates).loc[div_dates].values

            for week in weeks:
                # Calculate the price after the given number of weeks
                prices_shifted = prices.shift(-5*week)

                # Add the price and percentage change to the DataFrame
                dates_with_prices[f'Price at {week} Weeks'] = prices_shifted.loc[div_dates, 'Close'].values.round(2)
                dates_with_prices[f'Change at {week} Weeks (%)'] = ((dates_with_prices[f'Price at {week} Weeks'] - dates_with_prices['Closing Price']) / dates_with_prices['Closing Price'] * 100).round(2)

            st.write(f"Dividend Dates for {symbol} with Closing Prices:")
            st.write(dates_with_prices)

        else:
            st.write("No dividend data available for this stock.")
    else:
        st.write("No dividend data available for this stock.")
  
def main():
    params = setup_streamlit()
    if params is None:
        return

    period, symbols, new_symbol, search_button, color, weeks = params

    # If 'Search Now' is clicked, add the new symbol to the symbols list
    if search_button and new_symbol:
        symbols.append(new_symbol)

    data = download_data(symbols, period)
    #st.header('Data view')
    
    # Displaying the first 5 rows for each stock in the DataFrame
    # for symbol, df in data.items():
    #     st.subheader(symbol)
    #     st.write(df.head())


     # Create a new DataFrame 'new_df' with specified columns from ticker.info
    new_df_data = []
    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        stock_info = ticker.info
        new_row = {
            "symbol": stock_info.get("symbol"),
            "previousClose": stock_info.get("previousClose"),
            "open": stock_info.get("open"),
            "dayLow": stock_info.get("dayLow"),
            "dayHigh": stock_info.get("dayHigh"),
            "targetHighPrice": stock_info.get("targetHighPrice"),
            "targetLowPrice": stock_info.get("targetLowPrice"),
            "targetMeanPrice": stock_info.get("targetMeanPrice"),
            "targetMedianPrice": stock_info.get("targetMedianPrice"),
            "exchange": stock_info.get("exchange"),
        }
        new_df_data.append(new_row)

    new_df = pd.DataFrame(new_df_data)

    # Display the new DataFrame 
    st.header(f'Ticker Data for {", ".join(symbols)}')
    st.write(new_df)

    st.header('Analysis')
    for symbol in symbols:
        try:
            perform_analysis(symbol, data, color, new_df, weeks)
        except Exception as e:
            print("Error occurred in perform_analysis:", e)  # Debug print statement

    #st.header('Combined view')
    #combined = pd.concat([data[symbol][f'{symbol}_Dividends'] for symbol in symbols], axis=1)
    #st.write(combined)

if __name__ == "__main__":
    main()
            
