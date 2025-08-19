import time
from typing import Iterable

from config.exchenges import binance


def limit_usage_from_response(*limit_names):
    def wrapper(func):
        def wrapper_(watcher, *args, **kwargs):
            limit_sleep(limit_names, watcher.limit_usage)

            response = func(watcher, *args, **kwargs)

            watcher.limit_usage.update({key: int(value) for key, value in response['limit_usage'].items()})
            print(watcher.limit_usage)
            return response['data']

        return wrapper_

    return wrapper


def limit_sleep(limit_names: Iterable, limit_usage: dict):
    sleeps = []

    for limit_name in limit_names:
        usage_percent = limit_usage[limit_name] // binance.LIMIT_1_PERCENT[limit_name]
        dif = usage_percent - binance.LIMIT_PERCENT
        print(dif)
        if dif > 0:
            sleeps.append(dif)

    if sleeps:
        time.sleep(max(sleeps))
