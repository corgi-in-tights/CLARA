import asyncio
import logging
import os

from .main import process_item

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Global state
logger = logging.getLogger(__name__)

# Persistent objects
cancel_event = None
dg_connection = None
microphone = None

# Accumulated interim results
is_finals = []


config = DeepgramClientOptions(options={"keepalive": "true"})
deepgram = DeepgramClient(DEEPGRAM_API_KEY, config)
dg_connection = deepgram.listen.asyncwebsocket.v("1")

utterence_end_event = asyncio.Event()

options = LiveOptions(
    model="nova-3",
    language="en-US",
    smart_format=True,
    encoding="linear16",
    channels=1,
    sample_rate=16000,
    interim_results=True,
    utterance_end_ms="1000",
    vad_events=True,
    endpointing=300,
)
addons = {"no_delay": "true"}


async def on_open(self, open, **kwargs):
    logger.debug("Connection Open")


async def on_transcript(self, result, **kwargs):
    if cancel_event and cancel_event.is_set():
        return

    sentence = result.channel.alternatives[0].transcript
    if not sentence:
        return
    
    print("Recieved transcript:", sentence, result.is_final)

    if result.is_final:
        is_finals.append(sentence)
        logger.debug(f"Final transcript: {sentence}")
        
        transcription_result = " ".join(is_finals)
        
        print("Dispatching transcription result")
        asyncio.create_task(process_item("", transcription_result))
        
        utterence_end_event.set()


# async def on_utterance_end(self, *_args, **_kwargs):
#     print("Utterance End Detected")
#     if is_finals:
#         transcription_result = " ".join(is_finals)
#         logger.debug(f"Utterance End: {transcription_result}")
        
#         is_finals.clear()
#         utterence_end_event.set()
        
#         # Must dispatch async calls explicitly
#         logger.debug("Dispatching transcription result")
#         asyncio.create_task(process_item({"sentence": transcription_result}))
#         logger.debug("Moving on")
# dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)


dg_connection.on(LiveTranscriptionEvents.Open, on_open)
dg_connection.on(LiveTranscriptionEvents.Transcript, on_transcript)




async def connect_to_dg():    
    logger.debug("Connecting to Deepgram...")
    response = await dg_connection.start(options, addons=addons)
    
    if not response:
        raise RuntimeError("Failed to connect to Deepgram")

    logger.debug("Successfully connected to Deepgram...")
    return dg_connection, utterence_end_event
