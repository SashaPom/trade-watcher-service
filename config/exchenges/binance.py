import os

# LIMITS
LIMIT_WEIGHT_60_NAME = 'x-mbx-used-weight-1m'
LIMIT_ORDERS_10_NAME = 'x-mbx-order-count-10s'
LIMIT_ORDERS_60_NAME = 'x-mbx-order-count-1m'

LIMIT_NAMES = (LIMIT_WEIGHT_60_NAME, LIMIT_ORDERS_10_NAME, LIMIT_ORDERS_60_NAME)

LIMIT = {
    LIMIT_WEIGHT_60_NAME: int(os.getenv('LIMIT_WEIGHT_60')),
    LIMIT_ORDERS_10_NAME: int(os.getenv('LIMIT_ORDERS_10')),
    LIMIT_ORDERS_60_NAME: int(os.getenv('LIMIT_ORDERS_60')),
}

LIMIT_1_PERCENT = {limit_name: LIMIT[limit_name] // 100 for limit_name in LIMIT_NAMES}

LIMIT_PERCENT = int(os.getenv('LIMIT_PERCENT'))

# TESTNET
TESTNET_ADDRESS = 'https://testnet.binancefuture.com'
