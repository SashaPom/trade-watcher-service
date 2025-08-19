import os

EXCHANGE_NAME = os.getenv('EXCHANGE_NAME').upper()

TESTNET = os.getenv('TESTNET', 'false').lower() == 'true'

DATETIME_FORMAT = '%Y.%m.%d %H:%M:%S'
