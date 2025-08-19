from watcher.base_manager import BaseManager
from watcher.binance.watcher import BinanceWatcher
from watcher.utils import profile_to_kwargs_for_watcher


class BinanceManager(BaseManager):
    @classmethod
    def create_watcher(cls, profile: dict) -> BinanceWatcher:
        return BinanceWatcher(
            api_key=profile['api_key'],
            secret_key=profile['secret_key'],

            **profile_to_kwargs_for_watcher(profile)
        )
