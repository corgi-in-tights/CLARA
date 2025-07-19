import asyncio
import websockets
import json
import os

WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", "ws://localhost:8001/ws")

async def send_request(sentence, url=WEBSOCKET_URL):
    async with websockets.connect(url) as websocket:
        data = {
            "sentence": sentence
        }
        await websocket.send(json.dumps(data))
        response = await websocket.recv()
        return json.loads(response)

asyncio.run("Hello world")