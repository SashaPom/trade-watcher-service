from config import EXCHANGE_NAME
from watcher.binance.manager import BinanceManager
from watcher.binance.watcher import BinanceWatcher
from watcher.okx.manager import OKXManager
from watcher.okx.watcher import OKXWatcher

watchers = {
    'BINANCE': BinanceWatcher,
    'OKX': OKXWatcher,
}

managers = {
    'BINANCE': BinanceManager,
    'OKX': OKXManager,
}

Watcher = watchers.get(EXCHANGE_NAME)
Manager = managers.get(EXCHANGE_NAME)

if not (Watcher and Manager):
    raise Exception(f'EXCHANGE_NAME has bad value:"{EXCHANGE_NAME}"')
