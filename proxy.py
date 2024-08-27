import asyncio
import websockets
import hashlib

# List to store connected clients
connected_clients = set()

async def handler(websocket, path):
    # Register the new client
    print(f"New client connected: {websocket}")
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            # Forward the message to all connected clients
            for client in connected_clients:
                if client != websocket:
                    print(f"WS>WS: ", hashlib.md5(message).hexdigest())
                    await client.send(message)

    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    finally:
        # Unregister the client
        connected_clients.remove(websocket)

async def main():
    # Start the WebSocket server
    server = await websockets.serve(handler, "localhost", 9999)
    print("WebSocket server listening on ws://localhost:9999")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
