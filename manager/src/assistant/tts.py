import asyncio

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    SpeakWSOptions,
)

from ..arduino import eye



config: DeepgramClientOptions = DeepgramClientOptions(
    options={
        # "auto_flush_speak_delta": "500",
        "speaker_playback": "true"
    },
)
deepgram: DeepgramClient = DeepgramClient("", config)

dg_connection = deepgram.speak.asyncwebsocket.v("1")

options = SpeakWSOptions(
    model="aura-2-thalia-en",
    encoding="linear16",
    sample_rate=16000,
)

tts_queue = asyncio.Queue()
is_speaking = False


async def process_tts_queue():
    global is_speaking
    while True:
        print("Waiting for text in TTS queue...")
        text = await tts_queue.get()
        print("Got text for TTS:", text)
        is_speaking = True
        try:
            await start_streaming(text)
        finally:
            is_speaking = False
            tts_queue.task_done()



async def enqueue_speech_task(text: str):
    await tts_queue.put(text)

async def on_startup():
    
    # if await dg_connection.start(options) is False:
    #     raise RuntimeError("Failed to start Deepgram TTS connection")
    if await dg_connection.start(options) is False:
        print("Failed to start Deepgram TTS connection")
        return
    
    asyncio.create_task(process_tts_queue())

    

async def start_streaming(text: str):
    print("starting streaming TTS", text)
    eye.talking()

    # https://github.com/deepgram/deepgram-python-sdk/blob/main/examples/text-to-speech/websocket/async_simple/main.py
    # # send the text to Deepgram
    await dg_connection.send_text(text)

    # if auto_flush_speak_delta is not used, you must flush the connection by calling flush()
    await dg_connection.flush()

    # Indicate that we've finished
    await dg_connection.wait_for_complete()

    if tts_queue.empty():
        eye.asleep()