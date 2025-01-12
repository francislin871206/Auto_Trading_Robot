# This module contains the logic for calculating technical indicators using pandas-ta and other technical analysis libraries.

import pandas_ta as ta

def calculate_indicators(df):
    """
    Calculate technical indicators for the given DataFrame.
    """
    df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    bbands = ta.bbands(df['close'], length=20)
    df = df.join(bbands)
    
    # Rename Bollinger Bands columns
    df.rename(columns={
        'BBL_20_2.0': 'lower_band',
        'BBM_20_2.0': 'middle_band',
        'BBU_20_2.0': 'upper_band',
        'BBB_20_2.0': 'Bandwidth',
        'BBP_20_2.0': '%B'
        }, inplace=True)
    
    df['RSI'] = ta.rsi(df['close'], length=14)
    return df

def calculate_dynamic_atr(df, current_price, base_multiplier=1.5):
    """
    Calculate dynamic ATR-based thresholds for stop loss and take profit.
    """
    print(df['ATR'].iloc[-1])
    atr_value = df['ATR'].iloc[-1]
    if atr_value > 2:  # High volatility market
        atr_multiplier = 2.5
        entry_threshold = 1.5 * atr_value
    else:  # Low volatility market
        atr_multiplier = base_multiplier
        entry_threshold = 0.75 * atr_value

    stop_loss_price = current_price - (atr_multiplier * 1 * atr_value)
    take_profit_price_1 = current_price + (atr_multiplier * 1.5 * atr_value)
    take_profit_price_2 = current_price + (atr_multiplier * 1.5 * atr_value)

    return atr_value, entry_threshold, stop_loss_price, take_profit_price_1, take_profit_price_2

def check_breakout(resistance_level, current_price):
    """
    Check if the current price has broken out above the resistance level.
    """
    return current_price >= resistance_level
