import json
import asyncio
import logging

from .intent_mappings import map_intent_to_skill
import websockets

logger = logging.getLogger("CLARA-assistant")
logger.addHandler(logging.StreamHandler())

CLASSIFIER_URL = "ws://localhost:8011/ws"

ws = None

async def on_startup():
    logger.info("Assistant startup complete")
    
    global ws
    ws = await websockets.connect(CLASSIFIER_URL)
    logger.info("WebSocket connection established")


async def get_slots_response_from_sentence(sentence, intent_schema):
    pass


async def classify_sentence(sentence):
    logger.info(f"Classifying sentence: {sentence}")
    
    await ws.send(sentence)
    try:
        response = await asyncio.wait_for(ws.recv(), timeout=8)
        logger.info(f"Received response: {response}")
        intent_name = response.strip()

        slots, response = await get_slots_response_from_sentence(sentence, intent_name)

        logger.info(f"Slots extracted: {slots}")
        intent = {
            "intent_name": intent_name,
            "slots": slots,
        }

        return intent, response

    except asyncio.TimeoutError:
        logger.warning("Timeout waiting for classifier response")
        intent_names = []
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        intent_names = []
    except websockets.WebSocketException as e:
        logger.error(f"WebSocket error: {e}")
        intent_names = []

    # return []


async def process_item(data):
    sentence = data.get("sentence", "")
    if not sentence:
        logger.warning("Received empty sentence")
        return None

    # send MODE_THINKING to arduino
    
    print(f"Processing sentence: {sentence}")

    # get list of intents from the sentence
    intents = await classify_sentence(sentence)
    if len(intents) == 0:
        logger.warning("No intents found in sentence")
        return None

    # query intent name to skill name mapping then run skill
    for intent in intents:
        intent_name = intent.get("intent")
        
        skill = map_intent_to_skill(intent_name)
        if not skill:
            logger.warning("No skill found for intent: %s", intent_name)
            continue

        # run skill (function) with slots as kwargs
        try:
            await skill(**intent.get("slots", {}))
        except Exception as e:
            logger.exception("Error occurred while running skill")
            continue