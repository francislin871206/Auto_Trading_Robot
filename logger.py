#5. 日誌和錯誤處理模組 (logger.py)
#此模組負責記錄交易和錯誤信息。
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, filename='trading_bot.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

def log_trade(message):
    logging.info(message)
    print(message)  # Optional, for console output

def log_error(message):
    logging.error(message)
    print(message)  # Optional, for console output