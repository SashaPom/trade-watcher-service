import asyncio
import json

import websockets
from websockets import WebSocketServerProtocol

from config import URL_PROFILES
from utils import run_in_thread, request_to_main
from watcher import Manager


async def handler_watcher(ws: WebSocketServerProtocol, uri: str):
    try:
        data: str = await ws.recv()
        print('handler_watcher', data)
        if data == 'update':
            update_profiles()
        elif '.' in data:
            await sent_watchers_data(ws, data)
    except websockets.exceptions.ConnectionClosedOK:
        pass


@run_in_thread
def update_profiles():
    profiles = request_to_main(URL_PROFILES)
    print(profiles)

    profiles_ids = []

    for profile in profiles:
        profile_id = profile['id']
        profiles_ids.append(profile_id)

        watcher = Manager.get_watcher(profile_id)

        if watcher:
            Manager.update_watcher(profile, watcher)
        else:
            watcher = Manager.create_watcher(profile)
            Manager.start_watcher(watcher)

    for id_, watcher in Manager.get_watcher_dict().items():
        if id_ not in profiles_ids:
            watcher.stop()


async def sent_watchers_data(ws: WebSocketServerProtocol, data: str):
    ids = data.split('.')
    watchers = []
    for id_ in ids:
        if id_.isdigit():
            watcher = await Manager.async_get_watcher(int(id_))
            if watcher:
                watchers.append(watcher)

    while True:
        answer = []
        for watcher in watchers:
            answer.append([
                watcher.id,
                str(watcher.balance),
                str(watcher.max_balance),
                str(watcher.available_balance),
                str(watcher.un_pnl),
                watcher.is_blocked,
                watcher.is_trade_now,
                watcher.lose_streak
            ])
        await ws.send(json.dumps(answer))
        await asyncio.sleep(3)
