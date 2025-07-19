import gc
import asyncio
import logging
import os

from .assistant.main import process_item

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Global state
logger = logging.getLogger("CLARA-speech-to-text")
logger.setLevel(logging.DEBUG)

# Persistent objects
transcription_event = None
transcription_result = None
cancel_event = None
dg_connection = None
microphone = None

# Accumulated interim results
is_finals = []


config = DeepgramClientOptions(options={"keepalive": "true"})
deepgram = DeepgramClient(DEEPGRAM_API_KEY, config)
dg_connection = deepgram.listen.asyncwebsocket.v("1")


@dg_connection.on(LiveTranscriptionEvents.UtteranceEnd)
async def on_utterance_end(self, *_args, **_kwargs):
    global transcription_result
    if is_finals:
        transcription_result = " ".join(is_finals)
        logger.debug(f"Utterance End: {transcription_result}")
        is_finals.clear()
        
        if transcription_event:
            transcription_event.set()
            
        await process_item({"sentence": transcription_result})

@dg_connection.on(LiveTranscriptionEvents.Open)
async def on_open(self, open, **kwargs):
    logger.debug("Connection Open")


async def setup_deepgram():
    global dg_connection, microphone

    config = DeepgramClientOptions(options={"keepalive": "true"})
    deepgram = DeepgramClient(DEEPGRAM_API_KEY, config)
    dg_connection = deepgram.listen.asyncwebsocket.v("1")

    # Register events
    async def on_open(self, open, **kwargs):
        logger.debug("Connection Open")

    async def on_close(self, close, **kwargs):
        logger.debug("Connection Closed")

    async def on_error(self, error, **kwargs):
        logger.error(f"Handled Error: {error}")

    async def on_speech_started(self, speech_started, **kwargs):
        logger.debug("Speech Started")

    async def on_unhandled(self, unhandled, **kwargs):
        logger.warning(f"Unhandled Websocket Message: {unhandled}")

    dg_connection.on(LiveTranscriptionEvents.Open, on_open)
    dg_connection.on(LiveTranscriptionEvents.Close, on_close)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)
    dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
    dg_connection.on(LiveTranscriptionEvents.Unhandled, on_unhandled)

    async def on_message(self, result, **kwargs):
        global is_finals, transcription_result
        if cancel_event and cancel_event.is_set():
            return

        sentence = result.channel.alternatives[0].transcript
        if not sentence:
            return

        if result.is_final:
            is_finals.append(sentence)

            if result.speech_final:
                transcription_result = " ".join(is_finals)
                logger.debug(f"Speech Final: {transcription_result}")
                is_finals = []
                if transcription_event:
                    transcription_event.set()

    async def on_utterance_end(self, *_args, **_kwargs):
        global transcription_result
        if is_finals:
            transcription_result = " ".join(is_finals)
            logger.debug(f"Utterance End: {transcription_result}")
            is_finals.clear()
            
            if transcription_event:
                transcription_event.set()
                
            await process_item({"sentence": transcription_result})

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)

    # Start connection
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

    response = await dg_connection.start(options, addons=addons)
    
    if not response:
        raise RuntimeError("Failed to connect to Deepgram")

    # Start microphone
    microphone = Microphone(dg_connection.send)


async def transcribe(timeout: float = 5.0) -> str | None:
    """
    Starts a new transcription task. Returns final string or None on timeout or cancellation.
    """
    microphone.start()
    
    global transcription_event, transcription_result, cancel_event
    transcription_event = asyncio.Event()
    cancel_event = asyncio.Event()
    transcription_result = None
    logger.info("🎤 Listening...")

    try:
        await asyncio.wait_for(transcription_event.wait(), timeout=timeout)
        return transcription_result
    except asyncio.TimeoutError:
        logger.warning("⏱️ Transcription timed out")
        return None
    finally:
        if microphone:
            try:
                microphone.finish()
            except Exception as e:
                logger.warning(f"Error closing microphone: {e}")
        
        if transcription_event:
            transcription_event.clear()
        if cancel_event:
            cancel_event.clear()

        logger.debug("🎤 Stopped listening")

def cancel_transcription():
    """
    Cancels current transcription attempt.
    """
    global cancel_event, transcription_event
    if cancel_event:
        cancel_event.set()
    if transcription_event and not transcription_event.is_set():
        transcription_event.set()
    logger.debug("❌ Transcription cancelled")


async def shutdown():
    if microphone:
        microphone.finish()
    if dg_connection:
        await dg_connection.finish()


async def run():
    await setup_deepgram()

    print("Say something...")

    result = await transcribe(timeout=10)
    if result:
        print(f"You said: {result}")
    else:
        print("No speech detected or timeout.")

    await shutdown()

if __name__ == "__main__":
    asyncio.run(run())