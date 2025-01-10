#3. 技術指標模組 technical_indicators.py
#此模組包含技術指標的計算邏輯，使用 pandas-ta 或其他技術分析庫進行技術指標計算。

import pandas_ta as ta

def calculate_indicators(df):
    df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    bbands = ta.bbands(df['close'], length=20)
    df = df.join(bbands)
    
    # 重命名布林帶的列名
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
    print(df['ATR'].iloc[-1])
    atr_value = df['ATR'].iloc[-1]
    if atr_value > 2:  # 高波動市場
        atr_multiplier = 2.5
        entry_threshold = 1.5 * atr_value
    else:  # 低波動市場
        atr_multiplier = base_multiplier
        entry_threshold = 0.75 * atr_value

    stop_loss_price = current_price - (atr_multiplier *1 *atr_value)
    take_profit_price_1 = current_price + (atr_multiplier * 1.5 * atr_value)
    take_profit_price_2 = current_price + (atr_multiplier * 1.5 *atr_value)
    

    return atr_value,entry_threshold, stop_loss_price, take_profit_price_1, take_profit_price_2

def check_breakout(resistance_level, current_price):
    return current_price >= resistance_level
