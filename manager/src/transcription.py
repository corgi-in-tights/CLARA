import os
import asyncio
import websockets
import pyaudio
import json
import time


FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024


ws = None
p = None

DEEPGRAM_URL = "wss://api.deepgram.com/v1/listen?"
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

MAX_TRANSCRIPTION_DURATION_SECONDS = 5

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

# for silence detection
last_speech_time = time.time()
is_transcribing = False
SILENCE_TIMEOUT_DURATION_SECONDS = 1

transcript_buffer = ""

p = pyaudio.PyAudio()


async def send_audio(ws):
    global last_speech_time
    
    # open audio stream
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("🎙️ Started recording")
    while is_transcribing:
        data = stream.read(CHUNK, exception_on_overflow=False)
        
        # write audio stream chunks to deepgram
        await ws.send(data)

        # check silence timeout
        if time.time() - last_speech_time > SILENCE_TIMEOUT_DURATION_SECONDS:
            print("🛑 No speech detected for", SILENCE_TIMEOUT_DURATION_SECONDS, "seconds")
            break

    # stop and close the stream
    stream.stop_stream()
    stream.close()
    await ws.close()
    print("🎤 Audio stream closed")


async def receive_transcripts(ws):
    global last_speech_time, transcript_buffer
    
    # receive transcripts from deepgram
    async for message in ws:
        data = json.loads(message)
        
        if "channel" in data and "alternatives" in data["channel"]:
            alt = data["channel"]["alternatives"][0]
            transcript = alt.get("transcript", "")
            if transcript.strip():
                last_speech_time = time.time()
                print("📝 Transcript:", transcript)
                transcript_buffer += transcript

        if data.get("is_final"):
            print("✅ Final transcript")
            print("Final Transcript:", transcript_buffer)


async def start_transcription():
    global transcribing, last_speech_time
    transcribing = True
    last_speech_time = time.time()

    # send and recieve audio in async
    send_task = asyncio.create_task(send_audio(ws))
    receive_task = asyncio.create_task(receive_transcripts(ws))

    # or timeout in X seconds
    timeout_task = asyncio.create_task(asyncio.sleep(MAX_TRANSCRIPTION_DURATION_SECONDS))

    # whichever finishes first
    done, pending = await asyncio.wait(
        [send_task, receive_task, timeout_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()
        
    transcribing = False


async def on_startup():
    global ws, p
    ws = await websockets.connect(DEEPGRAM_URL + f"access_token={DEEPGRAM_API_KEY}",)
    p = pyaudio.PyAudio()
    

if __name__ == "__main__":
    asyncio.run(on_startup())
    asyncio.run(start_transcription())
