import robin_stocks.robinhood as rh
import numpy as np
import pandas as pd
from datetime import datetime, time
import time as sleep_time

# Function to buy options
def buy_option(symbol, expiration_date, strike_price, option_type, quantity):
    # Get the option id
    option_id = rh.options.find_options_by_expiration_and_strike(
        symbol, expiration_date, strike_price, option_type
    )[0]['id']

    # Place a market order for the option
    order = rh.options.order_buy_option(
        option_id=option_id,
        quantity=quantity,
        price=None,  # None for a market order
        time_in_force='gtc'  # Good till cancelled
    )
    
    if order:
        print(f"Successfully placed a buy order for {quantity} {symbol} {option_type} option(s) at strike {strike_price}.")
    else:
        print("Failed to place order.")

# Function to sell options
def sell_option(symbol, expiration_date, strike_price, option_type, quantity):
    # Get the option id
    option_id = rh.options.find_options_by_expiration_and_strike(
        symbol, expiration_date, strike_price, option_type
    )[0]['id']

    # Place a market order for the option
    order = rh.options.order_sell_option(
        option_id=option_id,
        quantity=quantity,
        price=None,  # None for a market order
        time_in_force='gtc'  # Good till cancelled
    )
    
    if order:
        print(f"Successfully placed a sell order for {quantity} {symbol} {option_type} option(s) at strike {strike_price}.")
    else:
        print("Failed to place order.")

# Login to Robinhood
def login_to_robinhood(username, password):
    rh.login(username=username, password=password)

# Function to keep track of positions
def get_positions():
    positions = rh.options.get_open_option_positions()
    return positions

def get_stock_data(symbol, interval='day', span='3month'):
    """
    Fetch historical stock data from Robinhood.

    :param symbol: The stock ticker symbol, e.g., 'AAPL'.
    :param interval: The interval between data points ('5minute', '10minute', 'hour', 'day', 'week').
    :param span: The time span of data ('day', 'week', 'month', '3month', 'year', '5year', 'all').
    :return: A pandas DataFrame containing historical stock data.
    """
    historicals = rh.stocks.get_stock_historicals(symbol, interval=interval, span=span)
    if not historicals:
        raise ValueError(f"No historical data found for symbol: {symbol}")
    # print(historicals)
    # Convert the data to a pandas DataFrame
    data = pd.DataFrame(historicals)
    data['close_price'] = pd.to_numeric(data['close_price'])
    data['high_price'] = pd.to_numeric(data['high_price'])
    data['low_price'] = pd.to_numeric(data['low_price'])
    # print(data)
    return data
# Function to get the current price of a stock
def get_current_price(symbol):
    try:
        price = rh.stocks.get_latest_price(symbol)[0]  # Returns a list; get the first element
        return float(price) if price else None
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None

def calculate_moving_averages(data, short_window=50, long_window=200):
    """
    Calculate Simple and Exponential Moving Averages.

    :param data: A pandas DataFrame containing 'close_price'.
    :param short_window: The number of periods for the short moving average (e.g., 50-day).
    :param long_window: The number of periods for the long moving average (e.g., 200-day).
    :return: A DataFrame with added columns for moving averages.
    """
    # Ensure the 'close_price' column is present in the DataFrame
    if 'close_price' not in data.columns:
        raise ValueError("DataFrame must contain 'close_price' column")

    # Calculate Simple Moving Averages (SMA)
    data['SMA50'] = data['close_price'].rolling(window=short_window).mean()
    data['SMA200'] = data['close_price'].rolling(window=long_window).mean()

    # Calculate Exponential Moving Averages (EMA)
    data['EMA50'] = data['close_price'].ewm(span=short_window, adjust=False).mean()
    data['EMA200'] = data['close_price'].ewm(span=long_window, adjust=False).mean()

    return data
def calculate_support_resistance(data, window=5):
    """
    Calculate support and resistance levels for a stock.

    :param data: A pandas DataFrame containing 'close_price', 'high_price', and 'low_price'.
    :param window: The window size to identify local minima and maxima.
    :return: A tuple containing lists of support and resistance levels.
    """
    supports = []
    resistances = []
    # print(data)
    for i in range(window, len(data) - window):
        high = data['high_price'][i]
        low = data['low_price'][i]

        if high == max(data['high_price'][i - window:i + window + 1]):
            resistances.append(high)
        if low == min(data['low_price'][i - window:i + window + 1]):
            supports.append(low)

    return supports, resistances

def calculate_support_resistance_improved(data, window=5):
    """
    Improved method to calculate support and resistance levels using moving averages and volume analysis.

    :param data: A pandas DataFrame containing 'close_price', 'high_price', 'low_price', 'volume'.
    :param window: The window size to identify local minima and maxima.
    :return: A tuple containing lists of support and resistance levels.
    """
    supports = []
    resistances = []
    
    # Calculate moving averages (e.g., 50-day and 200-day)
    data['MA50'] = data['close_price'].rolling(window=50).mean()
    data['MA200'] = data['close_price'].rolling(window=200).mean()

    for i in range(window, len(data) - window):
        high = data['high_price'][i]
        low = data['low_price'][i]

        # Check if the current high is a local maximum and above moving averages
        if high == max(data['high_price'][i - window:i + window + 1]) and high > data['MA50'][i] and high > data['MA200'][i]:
            resistances.append((high, data['volume'][i]))

        # Check if the current low is a local minimum and below moving averages
        if low == min(data['low_price'][i - window:i + window + 1]) and low < data['MA50'][i] and low < data['MA200'][i]:
            supports.append((low, data['volume'][i]))

    # Filter by significant volume levels
    supports = [s for s in supports if s[1] > data['volume'].mean()]
    resistances = [r for r in resistances if r[1] > data['volume'].mean()]

    return supports, resistances

def analyze_stock(symbol):
    """
    Analyze the stock for different time frames and calculate support and resistance levels.

    :param symbol: The stock ticker symbol.
    """
    # Intraday levels (1 day, 5-minute interval)
    intraday_data = get_stock_data(symbol, interval='5minute', span='day')
    intraday_supports, intraday_resistances = calculate_support_resistance(intraday_data)
    
    # Short-term levels (3 months, daily interval)
    short_term_data = get_stock_data(symbol, interval='day', span='3month')
    short_term_supports, short_term_resistances = calculate_support_resistance(short_term_data)
    
    # Long-term levels (1 year, weekly interval)
    long_term_data = get_stock_data(symbol, interval='week', span='year')
    long_term_supports, long_term_resistances = calculate_support_resistance(long_term_data)
    
    MAdata = get_stock_data(symbol, interval='day', span='year')
    movingAverages = calculate_moving_averages(MAdata)
    # Print results
    print(f"Intraday Support Levels for {symbol}: {intraday_supports}")
    print(f"Intraday Resistance Levels for {symbol}: {intraday_resistances}")
    
    print(f"\nShort-Term Support Levels for {symbol}: {short_term_supports}")
    print(f"Short-Term Resistance Levels for {symbol}: {short_term_resistances}")
    
    print(f"\nLong-Term Support Levels for {symbol}: {long_term_supports}")
    print(f"Long-Term Resistance Levels for {symbol}: {long_term_resistances}")
    
    print(f"50 Day Simple Moving Average {movingAverages['SMA50'][len(movingAverages) - 1]} ")
    print(f"200 Day Simple Moving Average {movingAverages['SMA200'][len(movingAverages) - 1]} ")
    analysis = {
        "intraday_supports":intraday_supports,
        "intraday_resistances":intraday_resistances,
        "short_term_supports":short_term_supports,
        "short_term_resistances":short_term_resistances,
        "long_term_supports":long_term_supports,
        "long_term_resistances":long_term_resistances,
        "SMA50":movingAverages['SMA50'][len(movingAverages) - 1],
        "SMA200":movingAverages['SMA200'][len(movingAverages) - 1]
    }
    return analysis
def is_market_open():
    """Checks if the current time is within US stock market trading hours."""
    now = datetime.now().time()
    market_open = time(9, 30)   # 9:30 AM ET
    market_close = time(16, 0)  # 4:00 PM ET
    return market_open <= now <= market_close

if __name__ == "__main__":
    # Symbol of stock to trade
    symbol = "SPY"
    # Replace these with your actual Robinhood credentials
    username = 'Username'
    password = 'Password'
    # Login to Robinhood
    rh.login(username=username, password=password)
    while (is_market_open()):
        print("Market is open. Running trading operations...")
        # Collect Relevant data
        analysis = analyze_stock(symbol)
        current_price = get_current_price(symbol)
        print("""
        Symbol: {symbol}:{current_price},
        Analysis:{analysis}
        """)
        # Perform your trading logic here
        # Your code for trading operations
        # Sleep for a period of time (e.g., 60 seconds) to avoid too frequent API calls
        time.sleep(60)
    print("Market is closed. Stopping trading bot.")
    # Logout after the operation
    rh.logout()