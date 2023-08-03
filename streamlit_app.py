import yfinance as yf
import streamlit as st
import pandas as pd 
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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
            stock_info = ticker.info
            
                        # Assuming you have the `stock_info` dictionary obtained from `ticker.info`
            stock_info = {
                "maxAge": 86400,
                "previousClose": 291.07,
                "open": 290.26,
                "dayLow": 289.38,
                "dayHigh": 293.45211449823232,
                "exchange": "NYQ",
                "quoteType": "EQUITY",
                "symbol": "MCD",
                "targetHighPrice": 383,
                "targetLowPrice": 300,
                "targetMeanPrice": 328.94,
                "targetMedianPrice": 330
            }
            
            # Create a new DataFrame 'new_df' with the specified data
            new_df = pd.DataFrame([stock_info])
            
            # Display the new DataFrame
            st.write(new_df)

            # Print available data for the stock
            #st.write(f"Available data for {symbol}:")
            #st.write(stock_info)

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


def get_days_to_target(divs, prices, targets):
    if divs.empty:
        return {f'{target*100}%': None for target in targets}
    else:
        div_prices = pd.merge(prices, divs, left_index=True, right_index=True, how='inner')

        results = {}
        for target in targets:
            target_price = div_prices['Close'] * (1 + target * div_prices['Dividends'])
            days_to_reach_value = min((i+1 for i, price in enumerate(target_price) if price > div_prices['Close'][0]), default=None)
            results[f'{target*100}%'] = days_to_reach_value

            # Additional code to visualize how the days are calculated
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=div_prices.index, y=div_prices['Close'], mode='lines', name='Price'))
            fig.add_trace(go.Scatter(x=div_prices.index, y=target_price, mode='lines', name=f'{target*100}% Target Price', line=dict(dash='dash')))
            fig.add_trace(go.Scatter(x=[div_prices.index[days_to_reach_value]], y=[target_price[days_to_reach_value]], mode='markers', name=f'{target*100}% Target Achieved', marker=dict(size=10)))

            fig.update_layout(title=f'Days to Reach {target*100}% Dividend Target', xaxis_title='Date', yaxis_title='Price ($)')
            st.plotly_chart(fig)

        return results


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
    
def perform_analysis(symbol, data, color):
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
            fig.add_trace(go.Scatter(x=div_dates, y=prices.loc[div_dates, 'Close'], mode='markers', marker=dict(symbol='star', size=12, color=color, line=dict(width=2, color='DarkSlateGrey')), name=symbol))

        st.plotly_chart(fig)

         # Display the DataFrame with the dividend dates and closing price on those dates
        div_dates_with_prices = divs[divs['Dividends'] > 0].join(prices, how='inner')

        # Calculate 1-year price target on the day the dividend was paid (assuming 1-year is 365 days)
        div_dates_with_prices['1-Year Price Target'] = div_dates_with_prices['Close'] * (1 + 365 * div_dates_with_prices['Dividends'])

        st.write("Dividend Dates with Closing Prices and 1-Year Price Target:")
        st.write(div_dates_with_prices)
        
        # Add a title to the div/date chart
        div_chart_title = f'Dividends Over Time for {symbol}'
        plot_dividends(divs, color, title=div_chart_title)

        plot_dividends(divs, color)
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

def show_dividend_targets(divs, prices):
    targets = [0.5, 0.75, 1.0]
    results = get_days_to_target(divs, prices, targets)
    st.write(pd.DataFrame(results, index=[f'{t*100}%' for t in targets]))

def calculate_dividend_metrics(divs, prices):
    clean_prices = prices.dropna().values  
    high_prices = [clean_prices[max(i-365, 0):i] for i in range(1, len(clean_prices))]

    results = []
    for date, div in divs.iterrows():
        year = date.year
        target = clean_prices[0] + div
        to_reach_50 = days_to_reach(high_prices, target * 0.5)
        to_reach_75 = days_to_reach(high_prices, target * 0.75)
        to_reach_100 = days_to_reach(high_prices, target)
        results.append([year, to_reach_50, to_reach_75, to_reach_100])

    numeric_results = [row for row in results if all(isinstance(value, (int, float)) for value in row[1:])]

    if numeric_results:
        averages = [sum(x)/len(x) for x in zip(*numeric_results)]
        results.append(["Average"] + averages[1:])
    
    return results

def days_to_reach(high_prices, target):
    days_to_reach_values = []
    for prices in high_prices:
        prices = [price for _, price in prices]
        prices = np.array(prices)  # Convert prices to a numpy array
        st.write("Prices:", prices)  # Debug print statement
        st.write("Target:", target)  # Debug print statement
        days_to_reach_value = next((i+1 for i, price in enumerate(prices) if price >= target), 0)
        days_to_reach_values.append(days_to_reach_value)
    return days_to_reach_values

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

    st.header('Analysis')
    for symbol in symbols:
        try:
            perform_analysis(symbol, data, color)
        except Exception as e:
            print("Error occurred in perform_analysis:", e)  # Debug print statement

    st.header('Combined view')
    combined = pd.concat([data[symbol][f'{symbol}_Dividends'] for symbol in symbols], axis=1)
    st.write(combined)

if __name__ == "__main__":
    main()
