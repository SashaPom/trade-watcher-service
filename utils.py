import os
import threading
import time
import urllib.request
import requests
import logging
import json


from datetime import datetime
from decimal import Decimal
from typing import Union, Tuple, Optional, Any
from config.ws_server import WS_ADDRESS, WS_PORT

log = logging.getLogger("tw.utils")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "10"))


def _addr_header() -> str:
    host = (WS_ADDRESS or "127.0.0.1").strip()
    return f"{host}:{WS_PORT}"


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


def request_to_main(
    url: str,
    method: str = "GET",
    data: Optional[Any] = None,
    timeout: int = REQUEST_TIMEOUT,
):
    """
    GET/POST JSON-запрос к Django:
      - добавляет заголовок addr
      - делает до 5 попыток
      - при неудаче возвращает []
    """
    headers = {"addr": _addr_header()}
    log.info("[WATCHER] request_to_main url=%s addr_header=%s", url,headers["addr"])
    body = None

    m = (method or "GET").upper()
    if m != "GET" and data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=m)

    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else []
        except Exception as e:
            # важное: логгер теперь точно есть
            log.warning("request_to_main(%s) failed: %s (try %s/5)", url, e, attempt + 1)
            time.sleep(1 + attempt)

    return []
