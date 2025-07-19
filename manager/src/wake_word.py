import pvporcupine
import pyaudio
import struct
import logging
import os

from .transcription import start_transcription

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CLARA-manager")

porcupine = pvporcupine.create(keyword_paths=["config/clara.ppn"], access_key=os.getenv("PORCUPINE_ACCESS_KEY"))

pa = pyaudio.PyAudio()

stream = pa.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length,
)

    
def listen_keyword():
    logger.info("Starting to listen for keyword...")
    
    try:
        while True:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                logger.info("Wake word detected!")
                await start_transcription()
                # send OLED to turn to 'awake'

    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()


if __name__ == "__main__":
    listen_keyword()
