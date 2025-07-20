import time
import asyncio
import pvporcupine
import pyaudio
import struct
import logging
import os

from .assistant.stt import transcribe

logger = logging.getLogger(__name__)

porcupine = pvporcupine.create(keyword_paths=["config/clara-mac.ppn"], access_key=os.getenv("PORCUPINE_ACCESS_KEY"))

pa = pyaudio.PyAudio()

stream = None

def start_microphone():
    global stream
    logger.debug("Starting microphone...")
    
    if stream is None:
        stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
        )

    logger.debug("Waiting for microphone to start... %s", stream)
    time.sleep(0.2)  # give some time for the stream to start
    logger.debug("Microphone stream opened %s.", stream)

    if not stream.is_active():
        stream.start_stream()

    timeout = time.time() + 2 # wait upto 2s to avoid race conditions
    while not stream.is_active():
        if time.time() > timeout:
            raise RuntimeError("Microphone stream failed to start")
        time.sleep(0.01)

    logger.debug("Microphone started.")

    
def stop_microphone():
    global stream
    logger.debug("Stopping microphone...")
    if not stream:
        return
    
    if stream.is_active():
        stream.stop_stream()
    stream.close()
    pa.terminate()
    logger.debug("Microphone fully stopped and released.")
    
    
async def listen_keyword():
    logger.info("Starting to listen for keyword...")

    try:
        start_microphone()
        while True:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                stop_microphone()
                await transcribe(timeout=10)
                start_microphone()
                # send OLED to turn to 'awake'

    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()


if __name__ == "__main__":
    asyncio.run(listen_keyword())