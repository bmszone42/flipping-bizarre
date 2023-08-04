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
            # Plot dividend stars
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

            # Sort dividend dates
            div_dates = div_dates.sort_values()
            
            # Create lists for x and y line values
            x_line = []
            y_line = []
            
            # Loop through dividend dates 
            for i in range(len(div_dates)-1):
              x_line.append(div_dates[i])
              x_line.append(div_dates[i+1])
              
              y_line.append(prices.loc[div_dates[i], 'Close']) 
              y_line.append(prices.loc[div_dates[i+1], 'Close'])

            # # Check if the next day's price is up or down
            # next_day_prices = prices.loc[div_dates[i+1]]
            # up_down = 'green' if next_day_prices > prices.loc[div_dates[i]] else 'red'

            # fig.add_trace(go.Scatter(
            #   x=div_dates[i+1],
            #   y=next_day_prices,
            #   mode='markers',
            #   marker=dict(symbol='triangle', size=12, color=up_down),
            #   showlegend=False
            # ))

            # Plot connecting line
            fig.add_trace(go.Scatter(
              x=x_line,
              y=y_line,
              mode='lines',
              line=dict(color='white', width=2),
              showlegend=False
            ))
            
            st.plotly_chart(fig)

            div_dates = div_dates.tz_convert(prices.index.tz)

            # Display the DataFrame with the dividend dates and closing price on those dates
            div_dates_with_prices = divs[divs['Dividends'] > 0].join(prices, how='inner')
            st.write("Dividend Dates with Closing Prices:")
            st.write(div_dates_with_prices)

            dates_with_prices = pd.DataFrame()
            dates_with_prices['Dividend Date'] = div_dates
            dates_with_prices['Dividend Date'] = dates_with_prices['Dividend Date'].dt.strftime('%Y-%m-%d')

            # Set Dividend Date as index
            dates_with_prices = dates_with_prices.set_index('Dividend Date')
            dates_with_prices['Dividend Amount'] = divs.loc[div_dates, 'Dividends'].values

            try:
              dates_with_prices['Closing Price'] = prices.loc[div_dates, 'Close'].values
            except KeyError:
              dates_with_prices['Closing Price'] = prices.nearest(div_dates).loc[div_dates].values
                
            dates_with_prices['Price Next Day'] = prices.loc[div_dates + pd.Timedelta(days=1), 'Close'].values

            # Calculate the price one week after the dividend
            prices_shifted = prices.shift(-5)
            dates_with_prices['Price After Week'] = prices_shifted.loc[div_dates, 'Close'].values
    
            # Calculate the percentage change
            dates_with_prices['Price Change (%)'] = ((dates_with_prices['Price After Week'] - dates_with_prices['Closing Price']) / dates_with_prices['Closing Price']) * 100


            #dates_with_prices['Price Next 2 Days'] = prices.loc[div_dates + pd.Timedelta(days=2), 'Close'].values
            
            # # Calculate percentage change 
            # div_dates_with_prices['Percent Change (10 Days)'] = (div_dates_with_prices['Price +10 Days'] - div_dates_with_prices['Closing Price']) / div_dates_with_prices['Closing Price'] * 100

            st.write("Dividend Dates with More Closing Prices:")
            st.write(dates_with_prices)

        else:
            st.write("No dividend data available for this stock.")
    else:
        st.write("No dividend data available for this stock.")
    
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
        st.write(df.head())


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
            
