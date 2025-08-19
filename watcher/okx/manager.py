from watcher.base_manager import BaseManager
from watcher.okx.watcher import OKXWatcher
from watcher.utils import profile_to_kwargs_for_watcher


class OKXManager(BaseManager):
    @classmethod
    def create_watcher(cls, profile: dict) -> OKXWatcher:
        return OKXWatcher(
            api_key=profile['api_key'],
            secret_key=profile['secret_key'],
            passphrase=profile['passphrase'],

            **profile_to_kwargs_for_watcher(profile)
        )
