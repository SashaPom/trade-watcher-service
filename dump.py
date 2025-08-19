import json
import os
from typing import Iterable

from config import DUMP_WATCHER_PROFILES, DATETIME_FORMAT


def dump_watcher_profiles(watchers: Iterable):
    os.makedirs(os.path.dirname(DUMP_WATCHER_PROFILES), exist_ok=True)

    with open(DUMP_WATCHER_PROFILES, 'w') as file:
        json.dump(
            {watcher.id: {
                'max_balance': float(watcher.max_balance),
                'lose_streak': watcher.lose_streak,
                'is_blocked': watcher.is_blocked,
                'next_clear_checking_datetime': (watcher.next_clear_checking_datetime.strftime(DATETIME_FORMAT)
                                                 if watcher.next_clear_checking_datetime else None),
            } for watcher in watchers},
            file,
        )


def load_watcher_profiles() -> dict:
    with open(DUMP_WATCHER_PROFILES, 'r') as file:
        return json.load(file)
