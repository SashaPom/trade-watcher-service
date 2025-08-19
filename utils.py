import threading
import time
from datetime import datetime
from decimal import Decimal
from typing import Union

import requests

from config import WS_ADDRESS, WS_PORT


def run_in_thread(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()

    return wrapper


def time_execution(func):
    def wrapper(*args, **kwargs):
        start_time = Decimal(time.time())
        r = func(*args, **kwargs)
        print('seconds ->', Decimal(time.time()) - start_time)
        return r

    return wrapper


def get_now() -> datetime:
    return datetime.utcnow()


def do_nothing():
    pass


def request_to_main(url: str) -> Union[list, dict]:
    res = requests.get(url, headers={'addr': f'{WS_ADDRESS}:{WS_PORT}'})
    return res.json()
