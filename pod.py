import asyncio
import socket
import websockets
import hashlib

import conn

HOST = '192.168.21.30'
PORT = 6443
WEBSOCKET_URL = 'ws://localhost:9999/data'

async def handle_client(tcpreader, tcpwriter, ws):
    sockets = {}

    print(f"New client connected: {tcpreader} {tcpwriter}")
    try:
        # Forwarding data from client to WebSocket
        async def tcp_to_websocket():
            print("tcp_to_websocket...")
            while True:
                data = await tcpreader.read(2024)
                c = conn.Conn(0, data)
                socketid = c.socketid
                print(f'TCP@{socketid}>WS: ', hashlib.md5(data).hexdigest())
                if not data:
                    break
                await ws.send(c.to_ws_bytes())
        
        # Forwarding data from WebSocket to client
        async def websocket_to_tcp():
            print("websocket_to_tcp...")
            while True:
                message = await ws.recv()
                c = conn.Conn.from_ws_bytes(message)
                socketid = c.socketid
                print(f'WS>TCP@{socketid}: ', hashlib.md5(message).hexdigest())
                tcpwriter.write(c.data)
                await tcpwriter.drain()

        print("Running both tasks concurrently...")
        # Run both tasks concurrently
        await asyncio.gather(tcp_to_websocket(), websocket_to_tcp())
        print('done')

    except Exception as e:
        print(f"ASYNCIOD Error: {e}")


async def handle_socket_read(socketid, tcpreader, ws):
    try:
        print(f"New socket: {socketid}. Waiting on recv")
        print(tcpreader)
        while True:
            data = await tcpreader.read(2024)
            print('GOT DATA', data) 
            if data == b'':
                print(f"Connection closed: {socketid}")
                break

            print(f'TCP@{socketid}>WS: RAW', data)
            c = conn.Conn(socketid, data)
            print(f'TCP@{socketid}>WS: ', hashlib.md5(data).hexdigest())
            await ws.send(c.to_ws_bytes())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


async def handle_ws_incoming(ws, sockets):
    data = await ws.recv()

    c = conn.Conn.from_ws_bytes(data)
    socketid = c.socketid

    if socketid not in sockets:
        print(f"New socket: {socketid}")
        tcpreader, tcpwriter = await asyncio.open_connection(HOST, PORT)
        sockets[socketid] = (tcpreader, tcpwriter)
        print(f'TCPR: {tcpreader}')
        asyncio.create_task(handle_socket_read(socketid, tcpreader, ws))
    else:
        tcpreader, tcpwriter = sockets[socketid]

    print(f'WS@{socketid}>TCP: ', hashlib.md5(data).hexdigest())
    print(tcpwriter)

    tcpwriter.write(c.data)



async def main():
    tcpreader, tcpwriter = await asyncio.open_connection(HOST, PORT)

    ws = await websockets.connect(WEBSOCKET_URL)


    sockets = {}
    while True:
        await handle_ws_incoming(ws, sockets)
    

    #await handle_client(tcpreader, tcpwriter, ws)

if __name__ == "__main__":
    asyncio.run(main())



