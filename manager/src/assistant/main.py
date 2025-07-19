import logging

from .intent_mappings import map_intent_to_skill

logger = logging.getLogger("CLARA-assistant")

async def classify_sentence(sentence):
    logger.info(f"Classifying sentence: {sentence}")
    return {"intent": "dummy_intent", "slots": {}}


async def process_item(data):
    sentence = data.get("sentence", "")
    if not sentence:
        logger.warning("Received empty sentence")
        return

    # send MODE_THINKING to arduino
    
    logger.info(f"Processing sentence: {sentence}")


    # get list of intents from the sentence
    intents = await classify_sentence(sentence)
    if len(intents) == 0:
        logger.warning("No intents found in sentence")
        return
    
    # query intent name to skill name mapping then run skill
    for intent in intents:
        skill = map_intent_to_skill(intent)
        if not skill:
            logger.warning(f"No skill found for intent: {intent}")
            continue

        # run skill (function) with slots as kwargs
        try:
            await skill(**intent.get("slots", {}))
        except Exception as e:
            logger.error(f"Error occurred while running skill: {e}")
            continue