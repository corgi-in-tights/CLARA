import logging

from fastapi import FastAPI
from fastapi import WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocketDisconnect

from .intents_store import load_intents_and_samples

app = FastAPI()

logger = logging.getLogger("CLARA-assistant")

# allow all for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = set()
background_tasks = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            logger.debug("Received data: %r", data)
            if not data or not isinstance(data, dict):
                continue
            if "sentence" not in data:
                await websocket.send_text("Invalid data format. Expected 'sentence' key.")
                continue

            await process_item(websocket, data)
            await websocket.send_text(f"Received: {data['sentence']}")

    except WebSocketDisconnect:
        logger.debug("Client disconnected")
    finally:
        clients.remove(websocket)



def process_item(websocket, data):
    pass


@app.on_event("startup")
async def on_startup():
    await load_intents_and_samples()
