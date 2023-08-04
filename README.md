# Dividend Stock Analysis App

This is a Streamlit app for analyzing dividend stocks. 

## Overview

The app allows users to:

- Select dividend paying stocks
- View historical price and dividend data
- Analyze stock prices around dividend payment dates

## Usage

The app has several user inputs on the sidebar:

- Stock Symbol(s) - Enter or select stock tickers
- Time Period - Select how far back to get historical data
- Plot Color - Pick color for the interactive plots 

After entering selections, click "Search Now" to load data and run analysis.

Key features:

- Interactive price chart with dividend payment markers
- Dividend dates and amounts table
- Prices before and after dividend payments

## Running Locally

To run the app locally:

1. Clone this repo
2. Create and activate a virtual environment 
3. Install requirements from requirements.txt
4. Run `streamlit run app.py`

## Resources

This app uses:

- Streamlit for the UI
- yfinance for stock data
- Pandas and Plotly for analysis and visualization

## Contributing

Contributions are welcome! Open an issue or PR if you would like to help add features or fix bugs.
