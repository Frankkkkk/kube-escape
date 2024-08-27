import asyncio
import websockets
import hashlib


import conn


LOCALHOST = '127.0.0.1'
PORT = 8443
WEBSOCKET_URL = 'ws://localhost:9999/data'

ALREADY_DONE = False
socket_id = -1

async def handle_client(client_reader, client_writer):
    global socket_id
    socket_id += 1

    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # Forwarding data from client to WebSocket
            async def client_to_websocket():
                while True:
                    data = await client_reader.read(2024)
                    print(f'TCP{socket_id}>WS: ', hashlib.md5(data).hexdigest())
                    if not data:
                        break
                    c = conn.Conn(socket_id, data)
                    await websocket.send(c.to_ws_bytes())
            
            # Forwarding data from WebSocket to client
            async def websocket_to_client():
                while True:
                    message = await websocket.recv()
                    c = conn.Conn.from_ws_bytes(message)
                    if c.socketid == socket_id:
                        # XXX this is ugly, because it means that the data is sent twice or more if 2+ connections..
                        print(f'WS>TCP@{socket_id}: ', hashlib.md5(message).hexdigest())
                        client_writer.write(c.data)
                        await client_writer.drain()
            
            # Run both tasks concurrently
            await asyncio.gather(client_to_websocket(), websocket_to_client())

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client_writer.close()
        await client_writer.wait_closed()

async def main():
    port = PORT
    while True:
        try:
            server = await asyncio.start_server(handle_client, LOCALHOST, port)
            break
        except OSError:
            port += 1
    async with server:
        print(f"Server started on {LOCALHOST}:{port}")
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())



