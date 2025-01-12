"""
Purpose: This module is responsible for position management and risk control.
Function: 
    - calculate_position_size: Calculate position size based on account balance, entry price, stop loss distance, and leverage.
    - should_enter_trade: Check if trading is allowed based on the current position state.
    - update_position_status: Change the trading state to reflect whether a position is active or not.
"""

# Track position status globally
in_position = True

def calculate_position_size(account_balance, entry_price, stop_loss_price, risk_percentage, leverage):
    """
    Calculate position size based on account balance, entry price, stop loss distance, and leverage.
    """
    risk_amount = account_balance * risk_percentage
    stop_loss_distance = abs(entry_price - stop_loss_price)
    position_size = round((risk_amount * leverage) / stop_loss_distance, 3)
    return position_size

def should_enter_trade():
    return in_position

def update_position_status(status):
    global in_position
    in_position = status
