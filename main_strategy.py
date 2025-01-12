"""
Purpose: This module contains the core trading logic and calls functions from other modules to perform various operations.
Function:
    - monitor_price_and_sell: Automatically monitors price and triggers sell orders based on stop-loss or take-profit conditions.
    - trading_bot: function is the core of this trading system, responsible for automating the end-to-end trading process.
"""

from binance.client import Client
from api_interface import get_historical_data, place_buy_order, place_sell_order, get_current_balance, client
from technical_indicators import calculate_indicators, check_breakout, calculate_dynamic_atr
from risk_management import calculate_position_size, should_enter_trade, update_position_status, in_position
import logger
import time

SYMBOL = 'ETHUSDT'
TIME_INTERVAL = '1m'
SUB_INTERVAL = '1m'
LEVERAGE = 3
RISK_PERCENTAGE = 0.05

positions = {}

def monitor_price_and_sell(symbol, entry_price, criteria_price, stop_loss_price, take_profit_price_1, take_profit_price_2, quantity, atr_value):
    """
    Automatically monitors price and triggers sell orders based on stop-loss or take-profit conditions.
    """
    while positions[symbol]['active']:
        current_price = float(client.get_symbol_ticker(symbol=symbol)['price'])
        logger.log_trade(f"Criteria Price is {criteria_price}; Position opened for {SYMBOL} with entry price {current_price}, stop-loss {stop_loss_price}, and take-profits at {take_profit_price_1}, {take_profit_price_2}")
        
        if current_price <= stop_loss_price:
            place_sell_order(symbol, quantity)  # Trigger stop-loss
            logger.log_trade(f"Stop-loss triggered, sold {symbol} at price {current_price}")
            update_position_status(True)  # Close position
            break

        elif current_price >= take_profit_price_2:
            place_sell_order(symbol, quantity)  # Trigger final take-profit
            logger.log_trade(f"Final take-profit triggered, sold {symbol} at price {current_price}")
            update_position_status(True)  # Close position
            break

        # Update stop-loss dynamically to lock in profits
        stop_loss_price = max(stop_loss_price, current_price - (2 * atr_value))
        time.sleep(5)  # Check every 5 seconds

def trading_bot(account_balance):
    while True:
        try:
            # Retrieve historical data and calculate indicators
            df_1m = get_historical_data(SYMBOL, TIME_INTERVAL)
            df_1m = get_historical_data(SYMBOL, SUB_INTERVAL)
            df_1m = calculate_indicators(df_1m)
            current_price = df_1m['close'].iloc[-1]
            resistance_level = df_1m['high'][-17:-2].max()
            actual_quantity = round(get_current_balance("ETH"), 3)

            # Calculate dynamic ATR thresholds
            atr_value, entry_threshold, stop_loss_price, take_profit_price_1, take_profit_price_2 = calculate_dynamic_atr(df_1m, current_price)
            logger.log_trade(f"Current Price (1m): {current_price}, Resistance Level: {float(resistance_level) + float(entry_threshold)}, ETH current quantity: {actual_quantity}")
            logger.log_trade(f"Stop Loss Price: {stop_loss_price},Take Profit 1: {take_profit_price_1},Take Profit 2: {take_profit_price_2}")

            # Check breakout and entry conditions
            if current_price > resistance_level + entry_threshold and should_enter_trade():
                position_size = calculate_position_size(account_balance, current_price, stop_loss_price, RISK_PERCENTAGE, LEVERAGE)
                
                place_buy_order(SYMBOL, position_size)
                actual_quantity = round(get_current_balance("ETH"), 3)
                
                if actual_quantity > 0:
                    positions[SYMBOL] = {
                        'entry_price': current_price,
                        'stop_loss_price': stop_loss_price,
                        'take_profit_price_1': take_profit_price_1,
                        'take_profit_price_2': take_profit_price_2,
                        'quantity': actual_quantity,
                        'active': True
                        }
                    logger.log_trade(f"Position opened for {SYMBOL} with entry price {current_price}, stop-loss {stop_loss_price}, and take-profits at {take_profit_price_1}, {take_profit_price_2}")
                    criteria_price = current_price * 1.005
                    # Start price monitoring
                    monitor_price_and_sell(SYMBOL, current_price, criteria_price, stop_loss_price, take_profit_price_1, take_profit_price_2, actual_quantity, atr_value)
            
            time.sleep(5)  # Check every 5 seconds
        except Exception as e:
            logger.log_error(f"Unexpected error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    account_balance = 1000  # Assumed account balance
    trading_bot(account_balance)
