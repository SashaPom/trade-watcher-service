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


async def _stream_watchers(ws: WebSocketServerProtocol, ids: Iterable[int], interval_sec: float = 3.0):
    watchers = {}
    for wid in ids:
        w = await Manager.async_get_watcher(wid)
        if w:
            watchers[wid] = w

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

    initial = []
    for w in watchers.values():
        try:
            w.update_balance()
        except Exception as e:
            print(f"[ERROR] initial update_balance for {w.id} failed: {e}")
        initial.append(row(w))
    if initial:
        await ws.send(json.dumps(initial))

    last: dict[int, list] = {}
    alive_ids = set(watchers.keys())

    try:
        while True:
            changed = []
            current_ids = set()

            for wid, w in list(watchers.items()):
                current_ids.add(wid)
                try:
                    w.update_balance()
                except Exception as e:
                    print(f"[WARN] update_balance for {wid} failed: {e}")
                    continue

                r = row(w)
                if r != last.get(wid):
                    last[wid] = r
                    changed.append(r)

            # если какой-то id пропал (например, stop) → шлём нули
            stopped_ids = set(last.keys()) - current_ids
            for sid in stopped_ids:
                zero_row = [sid, "0", "0", "0", "0", False, False, 0]
                changed.append(zero_row)
                last[sid] = zero_row

            if changed:
                await ws.send(json.dumps(changed))

            alive_ids = current_ids

            await asyncio.sleep(interval_sec)
    except websockets.exceptions.ConnectionClosed:
        pass



@run_in_thread
def update_profiles():
    """
    Тянем профили из Django и синхронизируем менеджер вотчеров:
      - новые профили → создать watcher и запустить
      - существующие → обновить поля
      - отсутствующие → остановить их watcher
    """
    profiles = request_to_main(URL_PROFILES) or []
    log.info("update_profiles(): fetched %s items from %s", len(profiles or []), URL_PROFILES)

    seen_ids: List[int] = []
    for profile in profiles:
        pid = int(profile["id"])
        seen_ids.append(pid)

        watcher = Manager.get_watcher(pid)
        if watcher:
            Manager.update_watcher(profile, watcher)
        else:
            watcher = Manager.create_watcher(profile)
            Manager.start_watcher(watcher)

    for wid, watcher in list(Manager.get_watcher_dict().items()):
        if wid not in seen_ids:
            watcher.stop()


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
                # подтянуть профили/переназначения
                update_profiles()
                # можно коротко ответить
                await ws.send(json.dumps({"type": "ok", "cmd": "update"}))
                continue

            # подписка на витрины по id-списку, разделённому точками: "1.2.3"
            # допускаем и одиночное число "42"
            try:
                if "." in text:
                    ids = [int(x) for x in text.split(".") if x.isdigit()]
                else:
                    ids = [int(text)]
            except ValueError:
                # неизвестная команда — игнор
                await ws.send(json.dumps({"type": "error", "msg": "bad command"}))
                continue

            # отменяем предыдущий стрим, если был
            if stream_task and not stream_task.done():
                stream_task.cancel()
                try:
                    await stream_task
                except asyncio.CancelledError:
                    pass

            # запускаем новый стрим
            stream_task = asyncio.create_task(_stream_watchers(ws, ids))

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        log.exception("WS handler error: %s", e)
    finally:
        # гарантированно гасим активный стрим при закрытии
        if stream_task and not stream_task.done():
            stream_task.cancel()
            try:
                await stream_task
            except asyncio.CancelledError:
                pass
