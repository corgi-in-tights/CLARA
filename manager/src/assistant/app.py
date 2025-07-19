import logging

# from fastapi import FastAPI
# from fastapi import WebSocket
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.websockets import WebSocketDisconnect

# app = FastAPI()
# 
logger = logging.getLogger("CLARA-assistant")

# # allow all for now
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["127.0.0.1, localhost"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# clients = set()
# background_tasks = set()

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     clients.add(websocket)
#     try:
#         while True:
#             data = await websocket.receive_json()
#             if not data or not isinstance(data, dict) or "sentence" not in data:
#                 continue

#             await process_item(websocket, data)

#     except WebSocketDisconnect:
#         logger.debug("Client disconnected")
#     finally:
#         clients.remove(websocket)



async def process_item(data):
    sentence = data.get("sentence", "")
    if not sentence:
        logger.warning("Received empty sentence")
        return

    logger.info(f"Processing sentence: {sentence}")

    # await websocket.send_text("ACCEPTED")
    
    
    
    pass
    
    # classification.classify_sentence(sentence)
    # take in intents w/ their slots
    # query intent name to skill name mapping
    # run skill (function) with slots as kwargs



# @app.on_event("startup")
# async def on_startup():
#     pass
