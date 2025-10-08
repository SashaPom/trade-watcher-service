import asyncio
import json
import logging
from typing import Iterable, List, Optional

import websockets
from websockets import WebSocketServerProtocol

from config.ws_server import URL_PROFILES
from utils import run_in_thread, request_to_main
from watcher import Manager

log = logging.getLogger(__name__)


async def _stream_watchers(ws: WebSocketServerProtocol, ids: Iterable[int], interval_sec: float = 1.0):
    def row(w):
        return [
            w.id,
            str(w.balance),
            str(w.max_balance),
            str(w.available_balance),
            str(w.un_pnl),
            bool(w.is_blocked),
            bool(w.is_trade_now),
            int(w.lose_streak),
        ]

    ids = [int(x) for x in ids if isinstance(x, int) or (isinstance(x, str) and x.isdigit())]
    last: dict[int, list] = {}

    try:
        while True:
            changed = []
            current_watchers = {}
            for wid in ids:
                w = await Manager.async_get_watcher(wid)
                if w:
                    current_watchers[wid] = w

            alive_ids = set()
            for wid, w in current_watchers.items():
                try:
                    w.update_balance()
                except Exception:
                    continue
                alive_ids.add(wid)
                r = row(w)
                if r != last.get(wid):
                    last[wid] = r
                    changed.append(r)

            for wid in ids:
                if wid not in alive_ids:
                    zero_row = [wid, "0", "0", "0", "0", False, False, 0]
                    if zero_row != last.get(wid):
                        last[wid] = zero_row
                        changed.append(zero_row)

            if changed:
                await ws.send(json.dumps(changed))

            await asyncio.sleep(interval_sec)
    except websockets.exceptions.ConnectionClosed:
        pass



@run_in_thread
def update_profiles():
    profiles = request_to_main(URL_PROFILES) or []
    seen_ids: List[int] = []
    for profile in profiles:
        pid = int(profile["id"])
        seen_ids.append(pid)

        watcher = Manager.get_watcher(pid)
        if watcher:
            Manager.update_watcher(profile, watcher)
        else:
            watcher = Manager.create_watcher(profile)
            Manager.start_watcher(watcher, strict=False)

    for wid, watcher in list(Manager.get_watcher_dict().items()):
        if wid not in seen_ids:
            Manager.stop_watcher(watcher)


async def handler_watcher(ws: WebSocketServerProtocol, uri: str):
    stream_task: Optional[asyncio.Task] = None

    try:
        await ws.send(json.dumps({"type": "hello"}))
    except websockets.exceptions.ConnectionClosed:
        return

    try:
        async for msg in ws:
            if not isinstance(msg, str):
                continue

            text = msg.strip()
            if not text:
                continue

            if text.lower() == "update":
                update_profiles()
                await ws.send(json.dumps({"type": "ok", "cmd": "update"}))
                continue

            try:
                ids = [int(x) for x in text.split(".") if x.isdigit()] if "." in text else [int(text)]
            except ValueError:
                await ws.send(json.dumps({"type": "error", "msg": "bad command"}))
                continue

            if stream_task and not stream_task.done():
                stream_task.cancel()
                try:
                    await stream_task
                except asyncio.CancelledError:
                    pass

            stream_task = asyncio.create_task(_stream_watchers(ws, ids))

    except websockets.exceptions.ConnectionClosed:
        log.info("WebSocket closed by client")
    except Exception as e:
        log.exception("WS handler error: %s", e)
    finally:
        if stream_task and not stream_task.done():
            stream_task.cancel()
            try:
                await stream_task
            except asyncio.CancelledError:
                pass
