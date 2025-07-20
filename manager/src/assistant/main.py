import json
import asyncio
import logging
import openai

from .intent_mappings import map_intent_to_skill
import websockets

from ..arduino import eye

openai.api_key = "sk-..."

logger = logging.getLogger("CLARA-assistant")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

CLASSIFIER_URL = "ws://localhost:8099/ws"

ws = None

async def setup_classifier_ws():
    print("Setting up WebSocket connection to classifier...")
    
    global ws
    ws = await websockets.connect(CLASSIFIER_URL)
    print("Classifier WebSocket connection established")


# async def get_response(sentence: str) -> str:
#     try:
#         response = await openai.ChatCompletion.acreate(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": "Respond to what the user said within 20 words, confirming that you will reply if it is a question "},
#                 {"role": "user", "content": sentence},
#             ],
#             temperature=0.7,
#             max_tokens=500,
#         )
#         return response["choices"][0]["message"]["content"].strip()
#     except Exception as e:
#         return f"Error: {e}"


async def get_slots_response_from_sentence(sentence, intent_schema):
    return {}, "Sure! I can help with that, let me add it for you."


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

    return intent_names


async def process_item(target_url, sentence):
    if not sentence:
        logger.warning("Received empty sentence")
        return None

    # send MODE_THINKING to arduino
    
    print(f"Processing sentence: {sentence}")

    eye.thinking()

    # sentence = "What is a sublingual tablet?"  # for testing

    # get list of intents from the sentence
    intent, response = await classify_sentence(sentence)
    # intent, response = {
    #     "intent_name": "question/internet",
    #     "slots": {}
    # }, "Okay! Let me just look that up for you."

    if not intent:
        logger.warning("No intent found in sentence")
        return None

    # query intent name to skill name mapping then run skill
    intent_name = intent.get("intent_name")

    skill = map_intent_to_skill(intent_name)
    
    if not skill or not skill[0]:
        logger.warning("No skill found for intent: %s", intent_name)
        return None
    
    skill_func = skill[0]
    print(f"Mapped skill func: {skill_func.__name__} for intent: {intent_name}")

    # run skill (function) with slots as kwargs
    try:
        logger.info(f"Running skill: {skill_func.__name__} with slots: {intent.get('slots', {})}")
        await skill_func(target_url, sentence, response, **intent.get("slots", {}))
    except Exception:
        logger.exception("Error occurred while running skill")