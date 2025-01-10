#1. 主交易策略模組 main_strategy.py
#此模組包含主要的交易邏輯，並調用其他模組提供的函數來完成各種操作。
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

def monitor_price_and_sell(symbol, entry_price, criteria_price,stop_loss_price, take_profit_price_1, take_profit_price_2, quantity, atr_value):
    """
    自動監控價格，當觸發止盈或止損條件時執行賣出。
    """
    while positions[symbol]['active']:
        current_price = float(client.get_symbol_ticker(symbol=symbol)['price'])
        logger.log_trade(f"Criteria Price is {criteria_price}； Position opened for {SYMBOL} with entry price {current_price}, stop-loss {stop_loss_price}, and take-profits at {take_profit_price_1}, {take_profit_price_2}")
        
        if current_price <= stop_loss_price:
            place_sell_order(symbol, quantity)  # 觸發止損
            logger.log_trade(f"止損觸發，於價格 {current_price} 賣出 {symbol}")
            update_position_status(True)  # 平倉
            break

        #elif current_price >= take_profit_price_1:
        #    place_sell_order(symbol, quantity * 0.5)  # 第一次止盈
        #    logger.log_trade(f"第一次止盈觸發，於價格 {current_price} 賣出 {symbol} 50% 持倉")
        #    stop_loss_price = max(stop_loss_price, current_price - (1.5 * atr_value))  # 提升止損

        elif current_price >= take_profit_price_2:
            place_sell_order(symbol, quantity)  # 全部止盈
            logger.log_trade(f"最終止盈觸發，於價格 {current_price} 賣出 {symbol}")
            update_position_status(True)  # 平倉
            break

        # 每次價格檢查後更新止損以鎖定更多利潤；暫時不動態止損太多價格
        stop_loss_price = max(stop_loss_price, current_price - (2 * atr_value))
        time.sleep(5)  # 每 5 秒檢查一次

def trading_bot(account_balance):
    while True:
        try:
            # 獲取歷史數據並計算指標
            df_1m = get_historical_data(SYMBOL, TIME_INTERVAL)
            df_1m = get_historical_data(SYMBOL, SUB_INTERVAL)
            df_1m = calculate_indicators(df_1m)
            current_price = df_1m['close'].iloc[-1]
            resistance_level = df_1m['high'][-17:-2].max()
            actual_quantity = round(get_current_balance("ETH"),3)

            # 計算動態 ATR 閾值
            atr_value, entry_threshold, stop_loss_price, take_profit_price_1, take_profit_price_2 = calculate_dynamic_atr(df_1m, current_price)
            logger.log_trade(f"Current Price (1m): {current_price}, Resistance Level: {float(resistance_level) + float(0*entry_threshold)}, ETH current quantity: {actual_quantity}")
            logger.log_trade(f"Stop Loss Price: {stop_loss_price},Take Profit 1: {take_profit_price_1},Take Profit 2: {take_profit_price_2}")

            
            
            # 檢查突破條件和進場條件
            if current_price > resistance_level + entry_threshold*0 and should_enter_trade():
                position_size = calculate_position_size(account_balance, current_price, stop_loss_price, RISK_PERCENTAGE, LEVERAGE)
                
                place_buy_order(SYMBOL, position_size)
                actual_quantity = round(get_current_balance("ETH"),3)
                
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
                    criteria_price = current_price*1.005
                    # 啟動價格監控
                    monitor_price_and_sell(SYMBOL, current_price, criteria_price, stop_loss_price, take_profit_price_1, take_profit_price_2, actual_quantity,atr_value)
            
            time.sleep(5)  # 每分鐘檢查一次
        except Exception as e:
            logger.log_error(f"Unexpected error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    account_balance = 1000  # 假設的帳戶資金
    trading_bot(account_balance)