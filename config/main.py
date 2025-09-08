import os

EXCHANGE_NAME = os.getenv('EXCHANGE_NAME').upper()

TESTNET = os.getenv('TESTNET', 'false').lower() == 'true'

URL_UPDATE_PROFILE = os.getenv('URL_UPDATE_PROFILE')

DATETIME_FORMAT = '%Y.%m.%d %H:%M:%S'
