import logging
from .tts import enqueue_speech_task

logger = logging.getLogger("CLARA-assistant")


async def send_text_response(target_url, message):
    print("Text response sent to target:", message)
    
    await enqueue_speech_task(message)

    # convert message into speech via Deepgram.. again
    