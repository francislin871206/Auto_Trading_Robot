'''
This function is responsible for recording trading and error messages.
'''
  
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
