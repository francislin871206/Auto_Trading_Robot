from binance.client import Client
import pandas as pd
import logger
import time

API_KEY = "My Own API_Key"
API_SECRET = "My Own Secret_Code"

client = Client(API_KEY, API_SECRET)

def get_historical_data(symbol, interval, limit=100):
    try:
        candles = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(candles, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 
            'close_time', 'quote_asset_volume', 'number_of_trades', 
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        return df
    except Exception as e:
        logger.log_error(f"Error in fetching data: {e}")
        return pd.DataFrame()
    

def get_current_balance(symbol):
    """
    Retrieve the balance of a specified asset.
    """
    balance = client.get_asset_balance(asset=symbol)
    return float(balance['free'])

def place_buy_order(symbol, quantity, min_quantity=0.001, reduction_factor=0.5):
    """
    Attempt to place a buy order. If the USDT balance is insufficient, gradually reduce the order quantity until 
    the order is successfully executed or the minimum tradeable amount is reached.
    """
    # Get the USDT balance
    available_usdt_balance = get_current_balance("USDT")
    
    # Get the current ETH/USDT price
    current_price = float(client.get_symbol_ticker(symbol=symbol)['price'])
    
    # Continuously try to reduce the order quantity until it meets the balance limit
    while quantity > min_quantity:
        try:
            # Calculate the required USDT for the order
            required_usdt = quantity * current_price

            # If the USDT balance is insufficient, reduce the order quantity
            if available_usdt_balance < required_usdt:
                logger.log_error(f"Insufficient USDT balance for buying {quantity} ETH. Reducing quantity...")
                quantity *= reduction_factor
                quantity = round(quantity, 3)  # Keep decimal places based on exchange requirements
                continue

            # Attempt to place the order
            order = client.order_market_buy(symbol=symbol, quantity=quantity)
            
            # Check if the order was successfully filled
            if order['status'] == 'FILLED':
                actual_quantity = get_current_balance(symbol.replace('USDT', ''))
                logger.log_trade(f"Order filled for {quantity} of {symbol}")
                return actual_quantity
            else:
                logger.log_error(f"Buy order for {symbol} not fully executed.")
                return None
        except Exception as e:
            logger.log_error(f"Error in placing buy order for {quantity} of {symbol}: {e}")
            quantity *= reduction_factor
            quantity = round(quantity, 3)

    logger.log_error("Unable to place buy order: quantity reduced below minimum limit.")
    return None

def place_sell_order(symbol, quantity, interval=2, max_retries=10):
    """
    Place market sell orders in batches, retrying if partially filled, to maximize hedging efficiency.
    """
    total_quantity = quantity
    retries = 0
    
    while total_quantity > 0 and retries < max_retries:
        sell_quantity = total_quantity
        
        try:
            # Place a market sell order
            order = client.order_market_sell(symbol=symbol, quantity=sell_quantity)
            
            # Check if the order was filled
            if order['status'] == 'FILLED':
                logger.log_trade(f"Sold {sell_quantity} of {symbol}")
                total_quantity -= sell_quantity
                retries = 0
            elif order['status'] == 'PARTIALLY_FILLED':
                filled_quantity = float(order['executedQty'])
                total_quantity -= filled_quantity
                logger.log_error(f"Partial fill for {sell_quantity} of {symbol}, {filled_quantity} executed.")
            else:
                retries += 1
                logger.log_error(f"No fill for {sell_quantity} of {symbol}. Retrying ({retries}/{max_retries})...")
            
        except Exception as e:
            logger.log_error(f"Error in placing sell order: {e}")
            retries += 1
        
        # Wait for the interval before retrying the next batch order
        time.sleep(interval)

    if total_quantity > 0:
        logger.log_error(f"Unable to complete full sell order. Remaining quantity: {total_quantity}")

def check_order_status(symbol, order_id):
    """
    Continuously poll the order status until the order is completely filled or abandoned.
    """
    while True:
        order = client.get_order(symbol=symbol, orderId=order_id)
        
        # Check the order status
        if order['status'] == 'FILLED':
            print(f"The order {order_id} is completely filled")
            return True
        elif order['status'] == 'PARTIALLY_FILLED':
            print(f"The order {order_id} is partially filled, waiting for full completion...")
        else:
            print(f"The order {order_id} isn't filled, continuing to wait...")
        
        # Wait 30 seconds before checking again
        time.sleep(30)



