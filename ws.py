import asyncio
import json

import websockets
from websockets import WebSocketServerProtocol


class Server:
    def __init__(self, handler, host: str, port: int, ssl_context=None):
        self.handler = handler
        self.host = host
        self.port = port
        self.ssl_context = ssl_context

    @staticmethod
    async def get_data(ws: WebSocketServerProtocol) -> list:
        data: str = await ws.recv()
        if data:
            return data.split('.')

    async def register(self, ws: WebSocketServerProtocol):
        try:
            data = await self.get_data(ws)
            if isinstance(data, list):
                for id_ in data:
                    self.clients[id_] = ws
                    print('ws reg', id_)
                    while 1:
                        print(self.w.balance)
                        await ws.send(json.dumps({'balance': str(self.w.balance)}))
                        await asyncio.sleep(1)
        except websockets.exceptions.ConnectionClosedOK:
            pass

    async def send(self, message: str, id_: str):
        client: WebSocketServerProtocol = self.clients.get(id_)
        if client:
            try:
                await client.send(str(message))
                print('ws send')
            except websockets.exceptions.ConnectionClosedOK:
                pass

    def run(self):
        protocol = 'wss' if self.ssl_context else 'ws'
        print(f'{protocol}://{self.host}:{self.port}')

        start_server = websockets.serve(self.handler, self.host, self.port, ssl=self.ssl_context)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_server)
        loop.run_forever()
