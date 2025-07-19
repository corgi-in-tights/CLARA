import asyncio
import websockets
import json
import pyaudio
import time
import logging
import os

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
DEEPGRAM_WS_URL = "wss://api.deepgram.com/v1/listen?punctuate=true&interim_results=true"

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CLARA-transcriber")


class DeepgramTranscriber:
    def __init__(self):
        self.audio_interface = pyaudio.PyAudio()
        self.stream = None
        self.ws = None
        self.silence_start = None
        self.speech_start = None
        self.transcribing = False

    async def _send_audio(self):
        while self.transcribing:
            data = self.stream.read(CHUNK, exception_on_overflow=False)
            await self.ws.send(data)

    async def _receive_transcripts(self):
        async for message in self.ws:
            res = json.loads(message)

            # Deepgram V1 transcript partial or final
            if "channel" in res and "alternatives" in res["channel"]:
                transcript = res["channel"]["alternatives"][0].get("transcript", "")
                is_final = res["is_final"] if "is_final" in res else False

                # stop if 200ms of silence is detected
                if transcript.strip() == "":
                    if self.silence_start is None:
                        self.silence_start = time.time()
                    elif time.time() - self.silence_start > 0.2:
                        logger.info("Pause detected. Stopping transcription.")
                        self.transcribing = False
                        break
                else:
                    self.silence_start = None
                    if self.speech_start is None:
                        self.speech_start = time.time()

                logger.info("Transcript: %s", transcript)

                # stop after 3 seconds
                if self.speech_start and time.time() - self.speech_start > 3.0:
                    logger.info("3 seconds of speech reached. Stopping transcription.")
                    self.transcribing = False
                    break

    async def start_transcription(self):
        self.stream = self.audio_interface.open(
            format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
        )
        headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
        async with websockets.connect(DEEPGRAM_WS_URL, extra_headers=headers) as websocket:
            self.ws = websocket
            self.transcribing = True
            logger.info("Started transcription...")

            send_task = asyncio.create_task(self._send_audio())
            receive_task = asyncio.create_task(self._receive_transcripts())

            await asyncio.wait([send_task, receive_task], return_when=asyncio.FIRST_COMPLETED)

            self.transcribing = False
            self.stream.stop_stream()
            self.stream.close()
            logger.info("Transcription stopped.")


async def turn_on_transcription():
    transcriber = DeepgramTranscriber()
    await transcriber.start_transcription()


if __name__ == "__main__":
    asyncio.run(turn_on_transcription())
