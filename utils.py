import os
import threading
import time
from datetime import datetime
from decimal import Decimal
from typing import Union, Tuple

import requests

# из config подтягиваем адреса
from config import WS_ADDRESS, WS_PORT

# НЕОБЯЗАТЕЛЬНО: если есть PUBLIC_HOST — именно им представляемся Django
PUBLIC_HOST = os.getenv("PUBLIC_HOST")  # например, "localhost"
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "10"))


def _addr_header() -> str:
    """
    Адрес, который watcher будет класть в заголовок 'addr' при запросе в Django.
    ДОЛЖЕН 1-в-1 совпадать с TWServer.address:port в БД Django.
    """
    host = (PUBLIC_HOST or WS_ADDRESS or "127.0.0.1").strip()
    port = str(WS_PORT).strip()
    return f"{host}:{port}"


def run_in_thread(func):
    """Простой декоратор – выполнить функцию в отдельном демоне."""
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        t.start()
        return t
    return wrapper


def time_execution(func):
    def wrapper(*args, **kwargs):
        start_time = Decimal(time.time())
        r = func(*args, **kwargs)
        print("seconds ->", Decimal(time.time()) - start_time)
        return r
    return wrapper


def get_now() -> datetime:
    return datetime.utcnow()


def do_nothing():
    pass


def request_to_main(url: str) -> Union[list, dict]:
    """
    GET в Django с заголовком addr.
    Возвращает JSON (list|dict). В случае ошибки – поднимает исключение.
    """
    headers = {"addr": _addr_header()}
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    # на профили сервер шлёт массив
    return resp.json()
