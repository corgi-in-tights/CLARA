import asyncio
import websockets
import wave
import json
import os

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
DEEPGRAM_WS_URL = "wss://api.deepgram.com/v1/listen"

TEST_FILE = "recording.wav"





# Task to receive and print transcription
async def receive_transcripts(ws, wav_path):
    print("Starting receiver")
    try:
        async for message in ws:
            print("Received message:", message)
            response = json.loads(message)
            if "channel" in response:
                transcript = response["channel"]["alternatives"][0]["transcript"]
                if transcript:
                    print(f"📝 Transcript: {transcript}")
    except websockets.exceptions.ConnectionClosedOK:
        print("🔌 Connection closed normally (receive)")

# Task to send audio stream
async def send_audio(ws, wav_path):
    try:
        with wave.open(wav_path, "rb") as wf:
            chunk_size = 1024
            while True:
                data = wf.readframes(chunk_size)
                if not data:
                    break
                await ws.send(data)
                await asyncio.sleep(0.032)  # pacing
        # Tell Deepgram we're done sending audio
        await ws.send(json.dumps({"type": "CloseStream"}))
    except Exception as e:
        print(f"⚠️ Error sending audio: {e}")
                
                
                
async def stream_wav_to_deepgram(wav_path: str):
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
    }

    async with websockets.connect(DEEPGRAM_WS_URL, additional_headers=headers) as ws:
        print("🎤 Connected to Deepgram")


        # Run both tasks, but exit receive task gracefully
        await asyncio.gather(send_audio(ws, wav_path), receive_transcripts(ws, wav_path))

        print("📡 Audio sent and transcription received.")
        

async def main():
    if not os.path.exists(TEST_FILE):
        print(f"❗ Test file '{TEST_FILE}' not found.")
        return

    await stream_wav_to_deepgram(TEST_FILE)
    
if __name__ == "__main__":
    asyncio.run(main())