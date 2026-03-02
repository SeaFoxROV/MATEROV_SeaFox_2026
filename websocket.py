import asyncio
import websockets

clients = set()

async def handler(websocket):
    clients.add(websocket)
    try:
        async for message in websocket:
            print("Mensaje recibido:", message)
            # reenviar a todos
            for client in clients:
                if client != websocket:
                    await client.send(message)
    finally:
        clients.remove(websocket)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 3001):
        print("Servidor WebSocket escuchando en puerto 3001")
        await asyncio.Future()

asyncio.run(main())