You're right, my previous README section on implementation does not look quite right. Here is an updated implementation section with clearer formatting for the key components:

## Implementation

The key components of the app are:

- `app.py`: Main Streamlit app code. This contains the UI and calls the analysis functions.

- `analysis.py`: Contains the functions to fetch data and perform analysis.

    - `get_data()`: Fetches dividend and price history data from Yahoo Finance.

    - `analyze()`: Analyzes each year's dividends and calculates recovery days.

- `requirements.txt`: Lists the Python package dependencies for recreating the environment.

The analysis works by:

1. Fetching dividend and price history data from Yahoo Finance API using `get_data()`.

2. Filtering the dividends to those paid each year. 

3. Getting the price history around each dividend date.

4. Calculating the days for the stock to recover 50%, 75%, and 100% of the dividend amount. 

5. Averaging the recovery days for each year.

The results are then output in the Streamlit app `app.py` for the user.

Let me know if this provides a clearer explanation of the key components and implementation!
