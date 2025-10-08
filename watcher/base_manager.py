import threading

from abc import ABC, abstractmethod
from typing import Dict, Iterable, Optional

from watcher.base_watcher import BaseWatcher
from watcher.exceptions import DuplicateWatcher


class BaseManager(ABC):
    _objects: Dict[int, BaseWatcher] = {}
    _lock = threading.RLock()

    @classmethod
    def get_watcher(cls, id_) -> Optional[BaseWatcher]:
        with cls._lock:
            return cls._objects.get(id_)

    @classmethod
    def get_all_watchers(cls) -> Iterable[BaseWatcher]:
        with cls._lock:
            return list(cls._objects.values())

    @classmethod
    def get_watcher_ids(cls) -> Iterable[int]:
        with cls._lock:
            return list(cls._objects.keys())

    @classmethod
    def get_watcher_dict(cls) -> Dict[int, BaseWatcher]:
        with cls._lock:
            return dict(cls._objects)

    @classmethod
    def has_watcher(cls, id_) -> bool:
        with cls._lock:
            return id_ in cls._objects

    @classmethod
    def add_watcher(cls, watcher: BaseWatcher, *, strict: bool = True) -> BaseWatcher:
        with cls._lock:
            existing = cls._objects.get(watcher.id)
            if existing is not None:
                if strict:
                    raise DuplicateWatcher(f"Watcher with id={watcher.id} already exists")
                return existing
            cls._objects[watcher.id] = watcher
            return watcher

    @classmethod
    def remove_watcher(cls, id_):
        with cls._lock:
            cls._objects.pop(id_, None)

    @classmethod
    def start_watcher(cls, watcher: BaseWatcher, *, strict: bool = False) -> BaseWatcher:
        obj = cls.add_watcher(watcher, strict=strict)
        try:
            watcher.start()
        except RuntimeError:
            pass
        return obj

    @classmethod
    def stop_watcher(cls, watcher: BaseWatcher):
        if not watcher:
            return
        try:
            watcher.stop()
        finally:
            with cls._lock:
                cls._objects.pop(watcher.id, None)

    @classmethod
    async def async_get_watcher(cls, id_) -> Optional[BaseWatcher]:
        return cls.get_watcher(id_)

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
