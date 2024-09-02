#!/usr/bin/env python3
import asyncio
import websockets
import hashlib
import os

import websockets.asyncio.server

# List to store connected clients
connected_clients: dict[str, set] = dict()

async def handler(websocket):
    # Register the new client
    print(f"New client connected: {websocket}")
    print(f"WRP: {websocket.request.path}")
    if websocket.request.path not in connected_clients:
        connected_clients[websocket.request.path] = set()
    connected_clients[websocket.request.path].add(websocket)

    try:
        async for message in websocket:
            # Forward the message to all connected clients on the same path
            for client in connected_clients[websocket.request.path]:
                if client != websocket:
                    print(f"WS>WS: ", hashlib.md5(message).hexdigest())
                    await client.send(message)

    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    finally:
        # Unregister the client
        connected_clients.get(websocket.request.path, set()).remove(websocket)

async def main():
    # Start the WebSocket server
    ws_port = os.environ.get("WS_PORT", 9999)
    server = await websockets.asyncio.server.serve(handler, "", ws_port)
    print(f"WebSocket server listening on ws://[::]:{ws_port}")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
