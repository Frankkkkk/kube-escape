import asyncio
import socket
import websockets
import hashlib

HOST = '192.168.21.30'
PORT = 6443
WEBSOCKET_URL = 'ws://localhost:9999/data'

async def handle_client(tcpreader, tcpwriter, ws):
    print(f"New client connected: {tcpreader} {tcpwriter}")
    try:
        # Forwarding data from client to WebSocket
        async def tcp_to_websocket():
            print("tcp_to_websocket...")
            while True:
                data = await tcpreader.read(2024)
                print('TCP>WS: ', hashlib.md5(data).hexdigest())
                if not data:
                    break
                await ws.send(data)
        
        # Forwarding data from WebSocket to client
        async def websocket_to_tcp():
            print("websocket_to_tcp...")
            while True:
                message = await ws.recv()
                print('WS>TCP: ', hashlib.md5(message).hexdigest())
                tcpwriter.write(message)
                await tcpwriter.drain()

        print("Running both tasks concurrently...")
        # Run both tasks concurrently
        await asyncio.gather(tcp_to_websocket(), websocket_to_tcp())
        print('done')

    except Exception as e:
        print(f"ASYNCIOD Error: {e}")

async def main():
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((HOST, PORT))


    tcpreader, tcpwriter = await asyncio.open_connection(HOST, PORT)

    ws = await websockets.connect(WEBSOCKET_URL)

    await handle_client(tcpreader, tcpwriter, ws)

if __name__ == "__main__":
    asyncio.run(main())



