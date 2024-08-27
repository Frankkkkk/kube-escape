import asyncio
import websockets
import hashlib


import conn


LOCALHOST = '127.0.0.1'
PORT = 8443
WEBSOCKET_URL = 'ws://localhost:9999/data'

ALREADY_DONE = False
socket_id = -1

async def handle_client(socket_reader, socket_writer):
    global socket_id
    socket_id += 1


    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:

            print(f"New client connected socket {socket_id}: {socket_reader} {socket_writer}")
            m = conn.WSMsg(socket_id, conn.MsgType.CONNECT)
            await websocket.send(m.to_bytes())

            # Forwarding data from client to WebSocket
            async def client_to_websocket():
                while True:
                    data = await socket_reader.read(2024)
                    print(f'TCP{socket_id}>WS: ', hashlib.md5(data).hexdigest())
                    if not data:
                        break
                    c = conn.WSMsg(socket_id, conn.MsgType.DATA, data)
                    await websocket.send(c.to_bytes())

            # Forwarding data from WebSocket to client
            async def websocket_to_client():
                while True:
                    message = await websocket.recv()
                    c = conn.WSMsg.from_bytes(message)

                    # XXX this is ugly, because it means that the data is sent twice or more if 2+ connections..
                    if c.socketid == socket_id:
                        if c.msg == conn.MsgType.DISCONNECT:
                            print(f"Client {socket_id} disconnected")
                            break
                        else:
                            print(f'WS>TCP@{socket_id}: ', hashlib.md5(message).hexdigest())
                            socket_writer.write(c.payload)
                            await socket_writer.drain()
                    else:
                        print(f'WS>TCP@{socket_id}: ', hashlib.md5(message).hexdigest(), 'skipping')


            # Run both tasks concurrently
            await asyncio.gather(client_to_websocket(), websocket_to_client())
            print(f">>>> Client {socket_id} disconnected")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f">>>>>>>>>> Closing client {socket_id}")
        m = conn.WSMsg(socket_id, conn.MsgType.DISCONNECT)
        await websocket.send(m.to_bytes())

        socket_writer.close()
        await socket_writer.wait_closed()

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



