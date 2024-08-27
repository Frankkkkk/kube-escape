import asyncio
import websockets
import hashlib

LOCALHOST = '127.0.0.1'
PORT = 8443
WEBSOCKET_URL = 'ws://localhost:9999/data'

ALREADY_DONE = False

async def handle_client(client_reader, client_writer):
    global ALREADY_DONE
    if ALREADY_DONE:
        print('Will ret a 2nd time')
        return
    ALREADY_DONE = True

    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # Forwarding data from client to WebSocket
            async def client_to_websocket():
                while True:
                    data = await client_reader.read(2024)
                    print('TCP>WS: ', hashlib.md5(data).hexdigest())
                    if not data:
                        break
                    await websocket.send(data)
            
            # Forwarding data from WebSocket to client
            async def websocket_to_client():
                while True:
                    message = await websocket.recv()
                    print('WS>TCP: ', hashlib.md5(message).hexdigest())
                    client_writer.write(message)
                    await client_writer.drain()
            
            # Run both tasks concurrently
            await asyncio.gather(client_to_websocket(), websocket_to_client())

    except Exception as e:
        print(f"Error: {e}")
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



