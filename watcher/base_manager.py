from abc import ABC, abstractmethod
from typing import Iterable, Dict

from watcher.base_watcher import BaseWatcher
from watcher.exceptions import DuplicateWatcher


class BaseManager(ABC):
    objects = {}

    @classmethod
    def get_watcher(cls, id_) -> BaseWatcher:
        return cls.objects.get(id_)

    @classmethod
    def get_all_watchers(cls) -> Iterable[BaseWatcher]:
        return cls.objects.values()

    @classmethod
    def get_watcher_ids(cls) -> Iterable[int]:
        return cls.objects.keys()

    @classmethod
    def get_watcher_dict(cls) -> Dict[int, BaseWatcher]:
        return cls.objects

    @classmethod
    def has_watcher(cls, id_) -> bool:
        return id_ in cls.objects

    @classmethod
    def add_watcher(cls, watcher: BaseWatcher):
        if watcher.id in cls.objects:
            raise DuplicateWatcher

        cls.objects[watcher.id] = watcher

    @classmethod
    def remove_watcher(cls, id_):
        cls.objects.pop(id_, None)

    @classmethod
    def start_watcher(cls, watcher: BaseWatcher):
        cls.add_watcher(watcher)
        watcher.start()

    @classmethod
    def stop_watcher(cls, watcher: BaseWatcher):
        if watcher:
            watcher.stop()

    @classmethod
    async def async_get_watcher(cls, id_) -> BaseWatcher:
        return cls.objects.get(id_)

    @classmethod
    def update_watcher(cls, profile: dict, watcher: BaseWatcher):
        name = profile['name']
        telegram_chat_id = profile['telegram_chat_id']
        clear_checking_time = profile['refresh_time']
        lose_percent_limit = profile['lose_percent_limit']
        lose_amount_limit = profile['lose_amount_limit']
        lose_streak_limit = profile['lose_streak_limit']

        if watcher.name_ != name:
            watcher.name_ = name

        if watcher.telegram_chat_id != telegram_chat_id:
            watcher.telegram_chat_id = telegram_chat_id

        if watcher.clear_checking_time_str != clear_checking_time:
            watcher.set_clear_checking_time(clear_checking_time)

        if watcher.lose_percent_limit_ != lose_percent_limit:
            watcher.set_lose_percent_limit(lose_percent_limit)

        if watcher.lose_amount_limit_ != lose_amount_limit:
            watcher.set_lose_amount_limit(lose_amount_limit)

        if watcher.lose_streak_limit_ != lose_streak_limit:
            watcher.set_lose_streak_limit(lose_streak_limit)

    @classmethod
    @abstractmethod
    def create_watcher(cls, profile: dict) -> BaseWatcher:
        pass
