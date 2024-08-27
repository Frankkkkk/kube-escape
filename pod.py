#!/usr/bin/env python3
import asyncio
import websockets
import uuid
import os
import pathlib
from urllib.parse import urlparse
import colorful

import conn



async def handle_socket_read(socketid, tcpreader, ws):
    try:
        print(f"New socket: {socketid}. Waiting on recv")
        while True:
            data = await tcpreader.read(2024)
            print(f"TCP@{socketid} Received {len(data)} bytes")
            if data == b'':
                print(f"TCP@{socketid} Connection closed")
                c = conn.WSMsg(socketid, conn.MsgType.DISCONNECT)
                await ws.send(c.to_bytes())
                break

            c = conn.WSMsg(socketid, conn.MsgType.DATA, data)
            print(f'TCP>WS: {c}')
            await ws.send(c.to_bytes())

    except Exception as e:
        print(f"{socketid} Error: {e}")
        import traceback
        traceback.print_exc()


async def handle_ws_incoming(cfg, ws, sockets):
    data = await ws.recv()

    c = conn.WSMsg.from_bytes(data)
    socketid = c.socketid

    if c.msg == conn.MsgType.CONNECT:
        if socketid in sockets:
            print(f"Socket {socketid} already connected")
            return
        else:
            print(f"New socket: {socketid}")
            tcpreader, tcpwriter = await asyncio.open_connection(cfg['kube_api_host'], cfg['kube_api_port'])
            sockets[socketid] = (tcpreader, tcpwriter)
            asyncio.create_task(handle_socket_read(socketid, tcpreader, ws))

    elif c.msg == conn.MsgType.DISCONNECT:
        if socketid not in sockets:
            print(f"Socket {socketid} not connected")
            return
        else:
            print(f"Socket {socketid} disconnected")
            tcpreader, tcpwriter = sockets[socketid]
            del sockets[socketid]
            tcpwriter.close()
            await tcpwriter.wait_closed()

    elif c.msg == conn.MsgType.DATA:
        tcpreader, tcpwriter = sockets[socketid]
        print(f'WS>TCP: {c}')
        tcpwriter.write(c.payload)
        print('written')


def get_config():
    KUBERNETES_PORT = os.environ.get('KUBERNETES_PORT', 'http://localhost:6443')
    kube_api = urlparse(KUBERNETES_PORT)

    WEBSOCKET_ROOT_URL = os.environ.get('WEBSOCKET_ROOT_URL', 'ws://localhost:9999')


    WS_ID = os.environ.get('WS_ID', None)

    ws_id = WS_ID
    if ws_id is None:
        HOSTNAME = os.environ.get('HOSTNAME')
        # We want to name it as the replicaset, so it's somehow random, but doesn't
        # change on every pod restart
        if HOSTNAME.count('-') < 2:
            ws_id = uuid.uuid4().hex
        else:
            ws_id = ''.join(HOSTNAME.split('-')[:2])



    websocket_full_url = str(pathlib.Path(WEBSOCKET_ROOT_URL) / ws_id)

    # Pathlib replaces `ws://` into `ws:/`. This "fixes" it. lul
    websocket_full_url = websocket_full_url.replace('s:/', 's://')

    return {
        'kube_api_host': kube_api.hostname,
        'kube_api_port': kube_api.port,
        'websocket_url': websocket_full_url,
    }


async def main():

    config = get_config()
    print(\
f""" === KUBE-ESCAPE ===

A Kube API proxy over WebSockets

Websocket URL: {colorful.bold_coral(config['websocket_url'])}
Kube API Host: {config['kube_api_host']}
Kube API Port: {config['kube_api_port']}

Enjoy and fuck Citrix and VDIs!""")


    ws = await websockets.connect(config['websocket_url'])

    sockets = {}
    while True:
        await handle_ws_incoming(config, ws, sockets)

if __name__ == "__main__":
    asyncio.run(main())



