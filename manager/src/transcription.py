import os
import asyncio
import websockets
import pyaudio
import json
import time
import wave
import contextlib

from .assistant.app import process_item


FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

# DEEPGRAM_URL = "wss://api.deepgram.com/v1/listen"
DEEPGRAM_URL = "ws://localhost:8765" # for local testing
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

MAX_TRANSCRIPTION_DURATION_SECONDS = 5
SILENCE_TIMEOUT_DURATION_SECONDS = 1


ws = None
p = None
current_transcription_task: asyncio.Task | None = None

# for silence detection
last_speech_time = time.time()
is_transcribing = False

transcript_buffer = []


async def on_message(message: str):
    global transcript_buffer

    try:
        data = json.loads(message)

        # Skip metadata messages
        if data.get("type") == "Metadata":
            return

        # Handle actual transcription results
        if "channel" in data and "alternatives" in data["channel"]:
            transcript = data["channel"]["alternatives"][0].get("transcript", "")

            if transcript.strip():
                transcript_buffer.append(transcript)

    except json.JSONDecodeError:
        pass
    except Exception as e:
        print(f"Error processing message: {e}")


async def message_handler():
    """Dedicated message handler coroutine"""
    print("Starting message handler...")
    try:
        async for message in ws:
            print("Received message:", message)
            await on_message(message)
    except asyncio.CancelledError:
        pass  # Expected during shutdown
    except Exception as e:
        print(f"Handler error: {e}")
        

async def start_transcription():
    """Manage both audio streaming and message handling"""
    global is_transcribing
    
    # send MODE_LISTENING to arduino

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    # clear the transcript buffer
    transcript_buffer.clear()

    # handler for messages
    handler_task = asyncio.create_task(message_handler())

    wav_file = wave.open("recording.wav", "wb")
    wav_file.setnchannels(CHANNELS)
    wav_file.setsampwidth(p.get_sample_size(FORMAT))
    wav_file.setframerate(RATE)


    try:
        is_transcribing = True
        while is_transcribing:
            data = stream.read(CHUNK, exception_on_overflow=False)
            await ws.send(data)
            wav_file.writeframes(data)
            await asyncio.sleep(0.01)
    finally:
        handler_task.cancel()  # Signal cancellation
        with contextlib.suppress(asyncio.CancelledError):
            await handler_task 
            
        stream.stop_stream()
        stream.close()
        p.terminate()
        is_transcribing = False


async def finish_logging_transcription():
    pass


async def finish_message_transcription():
    final_string = transcript_buffer.join("")
    transcript_buffer.clear()
    print(f"Final transcript: {final_string}")
    
    await process_item({
        "sentence": final_string
    })


async def on_startup():
    global ws, p
    headers = {
        'Authorization': f"Token {DEEPGRAM_API_KEY}"
    }

    print("🔗 Connecting to Deepgram WebSocket...")
    p = pyaudio.PyAudio()
    ws = await websockets.connect(
        DEEPGRAM_URL,
        additional_headers=headers
    )
    

async def main():
    # 1. Establish connection
    await on_startup()
    
    print("✅ Connected to Deepgram WebSocket", ws)

    # 2. Start transcription (which handles messages)
    await start_transcription()

    # 3. Run until cancelled
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await ws.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")