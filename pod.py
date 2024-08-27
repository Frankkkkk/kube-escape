import asyncio
import socket
import websockets
import hashlib

import conn

HOST = '192.168.21.30'
PORT = 6443
WEBSOCKET_URL = 'ws://localhost:9999/data'


async def handle_socket_read(socketid, tcpreader, ws):
    try:
        print(f"New socket: {socketid}. Waiting on recv")
        while True:
            data = await tcpreader.read(2024)
            if data == b'':
                print(f"TCP@{socketid} Connection closed")
                c = conn.WSMsg(socketid, conn.MsgType.DISCONNECT)
                await ws.send(c.to_bytes())
                break

            c = conn.WSMsg(socketid, conn.MsgType.DATA, data)
            print(f'TCP@{socketid}>WS: ', hashlib.md5(data).hexdigest())
            await ws.send(c.to_bytes())

    except Exception as e:
        print(f"{socketid} Error: {e}")
        import traceback
        traceback.print_exc()


async def handle_ws_incoming(ws, sockets):
    data = await ws.recv()

    c = conn.WSMsg.from_bytes(data)
    print(f'NEW DATA: {c.socketid} {c.msg} {c.payload}')
    socketid = c.socketid

    if c.msg == conn.MsgType.CONNECT:
        if socketid in sockets:
            print(f"Socket {socketid} already connected")
            return
        else:
            print(f"New socket: {socketid}")
            tcpreader, tcpwriter = await asyncio.open_connection(HOST, PORT)
            sockets[socketid] = (tcpreader, tcpwriter)
            asyncio.create_task(handle_socket_read(socketid, tcpreader, ws))

    elif c.msg == conn.MsgType.DISCONNECT:
        if socketid not in sockets:
            print(f"Socket {socketid} not connected")
            return
        else:
            print(f"Socket {socketid} disconnected")
            del sockets[socketid]
            tcpwriter.close()
            await tcpwriter.wait_closed()

    elif c.msg == conn.MsgType.DATA:
        tcpreader, tcpwriter = sockets[socketid]
        print(f'WS@{socketid}>TCP: ', hashlib.md5(data).hexdigest())
        tcpwriter.write(c.payload)



async def main():
    tcpreader, tcpwriter = await asyncio.open_connection(HOST, PORT)

    ws = await websockets.connect(WEBSOCKET_URL)


    sockets = {}
    while True:
        await handle_ws_incoming(ws, sockets)
    

    #await handle_client(tcpreader, tcpwriter, ws)

if __name__ == "__main__":
    asyncio.run(main())



