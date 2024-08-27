#!/usr/bin/env python3
import asyncio
import websockets
import hashlib
import random
import os
import sys


import conn


LOCALHOST = '::1'
DEFAULT_LISTEN_PORT = 6443
WEBSOCKET_URL = 'ws://localhost:9999'


async def handle_client(socket_reader, socket_writer):
    socket_id = random.randint(0, 9000)


    async with websockets.connect(WEBSOCKET_URL) as websocket:
        try:
            print(f"New client connected socket {socket_id}")
            m = conn.WSMsg(socket_id, conn.MsgType.CONNECT)
            print(f'TCP>WS: {m}')
            await websocket.send(m.to_bytes())

            # Forwarding data from client to WebSocket
            async def client_to_websocket():
                while True:
                    data = await socket_reader.read(2024)
                    if not data:
                        c = conn.WSMsg(socket_id, conn.MsgType.DISCONNECT)
                        print(f"Client {socket_id} disconnected")
                        print(f'TCP>WS: {c}')
                        await websocket.send(c.to_bytes())
                        break

                    c = conn.WSMsg(socket_id, conn.MsgType.DATA, data)
                    print(f'TCP>WS: {c}')
                    await websocket.send(c.to_bytes())

            # Forwarding data from WebSocket to client
            async def websocket_to_client():
                while True:
                    message = await websocket.recv()
                    c = conn.WSMsg.from_bytes(message)

                    # XXX this is ugly, because it means that the data is sent twice or more if 2+ connections..
                    print('c.socketid', c.socketid, 'socket_id', socket_id)
                    if c.socketid == socket_id:
                        print('ours')
                        if c.msg == conn.MsgType.DISCONNECT:
                            print(f"Client {socket_id} disconnected")
                            break
                        elif c.msg == conn.MsgType.CONNECT:
                            ## This shouldn't really happen‽
                            break
                        else:
                            print(f'WS>TCP: {c}')
                            socket_writer.write(c.payload)
                            await socket_writer.drain()
                    else:
                        print('not ours')
                        print(f'WS>TCP@{socket_id}: ', hashlib.md5(message).hexdigest(), 'skipping')


            # Run both tasks concurrently
            await asyncio.gather(client_to_websocket(), websocket_to_client())
            print(f">>>> Client {socket_id} disconnected")

        finally:
            print(f">>>>>>>>>> Closing client {socket_id}")
            m = conn.WSMsg(socket_id, conn.MsgType.DISCONNECT)
            await websocket.send(m.to_bytes())

            socket_writer.close()
            await socket_writer.wait_closed()




def get_config():
    KUBE_API_PORT = os.environ.get('KUBE_API_PORT', DEFAULT_LISTEN_PORT)

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <websocket_url>")
        sys.exit(1)

    ws_url = sys.argv[1]
    global WEBSOCKET_URL
    # Yeah, I know this is fugly
    WEBSOCKET_URL = ws_url

    return {
        'kube_api_port': KUBE_API_PORT,
        'websocket_url': ws_url,
    }


async def main():
    cfg = get_config()

    try:
        server = await asyncio.start_server(handle_client, LOCALHOST, cfg['kube_api_port'])
    except OSError as e:
        print(e)
        print(f"There already is a client listening on port {cfg['kube_api_port']}")
        sys.exit(1)

    async with server:
        print(f"Server started on {LOCALHOST} port {cfg['kube_api_port']}")
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())



