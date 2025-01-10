from binance.client import Client
import pandas as pd
import logger
import time

API_KEY = "Mzc11VjlGVTGcvS14rE4lqOO7ReTAilhESEt74KzBQKVcwrF9fOndggibojR3oNE"
API_SECRET = "uNhDk5QblGGcNERNX3yNuhZWQODyrekBbtdDSkwGmisJvnnJUkARrtbay31krwEo"

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
    獲取指定幣種的餘額
    """
  # 手動指定資產名稱（若只針對 ETH 交易）： 如果這段代碼僅針對 ETHUSDT，可以手動指定 asset 變量，直接將其設為 'ETH'
    balance = client.get_asset_balance(asset=symbol)
    return float(balance['free'])


def place_buy_order(symbol, quantity, min_quantity=0.001, reduction_factor=0.5):
    """
    試圖下買單 如果USDT餘額不足則逐步縮小交易量直到成功執行或達到最小交易量。
    """
    # 獲取USDT餘額
    available_usdt_balance = get_current_balance("USDT")
    
    # 獲取當前ETH/USDT的價格
    current_price = float(client.get_symbol_ticker(symbol=symbol)['price'])
    
    # 不斷嘗試縮小交易量，直到達到可用餘額限制
    while quantity > min_quantity:
        try:
            # 計算購買所需的USDT數量
            required_usdt = quantity * current_price

            # 如果USDT餘額不足，則減少ETH購買數量
            if available_usdt_balance < required_usdt:
                logger.log_error(f"Insufficient USDT balance for buying {quantity} ETH. Reducing quantity...")
                quantity *= reduction_factor  # 減少ETH購買數量
                quantity = round(quantity, 3)  # 保留小數位數（根據交易所規定）
                continue

            # 嘗試下單
            order = client.order_market_buy(symbol=symbol, quantity=quantity)
            
            # 檢查是否成功成交
            if order['status'] == 'FILLED':
                actual_quantity = get_current_balance(symbol.replace('USDT', ''))
                logger.log_trade(f"Order filled for {quantity} of {symbol}")
                return actual_quantity  # 返回實際持有的數量
            else:
                logger.log_error(f"Buy order for {symbol} not fully executed.")
                return None  # 返回 None 表示交易失敗
        except Exception as e:
            logger.log_error(f"Error in placing buy order for {quantity} of {symbol}: {e}")
            quantity *= reduction_factor  # 再次減少交易量
            quantity = round(quantity, 3)  # 保留小數位數

    logger.log_error("Unable to place buy order: quantity reduced below minimum limit.")
    return None  # 當交易量小於最小值後退出

def place_sell_order(symbol, quantity, interval=2, max_retries=10):
    """
    分批下市價賣單，遇到部分成交時重新嘗試賣出剩餘數量，以最大化避險效果。
    """
    total_quantity = quantity
    retries = 0  # 計數重試次數
    
    while total_quantity > 0 and retries < max_retries:
        # 確定本次賣出數量
        sell_quantity =  total_quantity
        
        try:
            # 下市價單
            order = client.order_market_sell(symbol=symbol, quantity=sell_quantity)
            
            # 檢查是否完全成交
            if order['status'] == 'FILLED':
                logger.log_trade(f"Sold {sell_quantity} of {symbol}")
                total_quantity -= sell_quantity  # 減少剩餘數量
                retries = 0  # 重置重試計數，因為成交成功
            elif order['status'] == 'PARTIALLY_FILLED':
                # 訂單部分成交，記錄並繼續重試剩餘部分
                filled_quantity = float(order['executedQty'])
                total_quantity -= filled_quantity  # 減少部分成交的數量
                logger.log_error(f"Partial fill for {sell_quantity} of {symbol}, {filled_quantity} executed.")
            else:
                # 如果完全未成交，增加重試計數
                retries += 1
                logger.log_error(f"No fill for {sell_quantity} of {symbol}. Retrying ({retries}/{max_retries})...")
            
        except Exception as e:
            logger.log_error(f"Error in placing sell order: {e}")
            retries += 1  # 增加重試計數
        
        # 等待 interval 秒後再嘗試下一批訂單
        time.sleep(interval)

    if total_quantity > 0:
        logger.log_error(f"Unable to complete full sell order. Remaining quantity: {total_quantity}")


def check_order_status(symbol, order_id):
    """
    持續輪詢檢查訂單狀態，直到訂單完全成交或放棄
    """
    while True:
        order = client.get_order(symbol=symbol, orderId=order_id)
        
        # 檢查訂單狀態
        if order['status'] == 'FILLED':
            print(f"The order {order_id} is completely fullfilled")
            return True
        elif order['status'] == 'PARTIALLY_FILLED':
            print(f"The order {order_id} is partially fullfilled, wait for completely fullfilling...")
        else:
            print(f"The order {order_id} isn't fullfilled, keep waiting...")
        
        # 等待30秒後再次檢查
        time.sleep(30)

