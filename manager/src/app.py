# from .transcription import setup_deepgram
# from .wake_word import listen_keyword
# import logging

# logger = logging.getLogger("CLARA-manager")

# async def run():
#     await setup_deepgram()
#     logger.info("Deepgram setup complete")

#     # start wake word listening
#     await listen_keyword()



import asyncio
import pyaudio
import logging
import struct
import pvporcupine
import os


wake_word_detected = asyncio.Event()

logger = logging.getLogger("CLARA-manager")
logger.setLevel(logging.DEBUG)

async def wake_word_listener(wake_word_event, stream, porcupine):
    logger.info("Starting to listen for wake word...")

    try:
        while True:
            # Read audio frame from the stream (blocking call)
            pcm_bytes = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm_bytes)

            # Process frame for wake word detection
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                logger.info("Wake word detected!")

                # Notify that wake word was detected
                wake_word_event.set()

                # Wait for the main loop or transcription to clear event
                while wake_word_event.is_set():
                    await asyncio.sleep(0.1)

                # After handling, clear event and restart mic
                wake_word_event.clear()

            # Yield control to event loop to avoid blocking
            await asyncio.sleep(0)

    except asyncio.CancelledError:
        logger.info("Wake word listener cancelled")
    except Exception as e:
        logger.error(f"Error in wake_word_listener: {e}")


async def deepgram_transcriber(stream, websocket):
    try:
        while not wake_word_detected.is_set():
            audio_chunk = stream.read(512)
            await websocket.send(audio_chunk)
        # Wake word detected, stop transcription
    except asyncio.CancelledError:
        pass
    finally:
        await websocket.close()


async def main():
    porcupine = pvporcupine.create(keyword_paths=["config/clara-mac.ppn"], access_key=os.getenv("PORCUPINE_ACCESS_KEY"))

    

    pa = pyaudio.PyAudio()

    stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length,
    )
    
    while True:
        wake_word_detected.clear()

        # Listen for wake word (blocking here or in separate task)
        await wake_word_listener(stream, porcupine)

        # When wake word detected, start deepgram transcription task
        transcription_task = asyncio.create_task(deepgram_transcriber(stream, websocket))

        # Wait for wake word event (interrupt transcription)
        await wake_word_detected.wait()

        # Cancel transcription immediately on wake word
        transcription_task.cancel()
        try:
            await transcription_task
        except asyncio.CancelledError:
            pass

        # yield back control before looping
        await asyncio.sleep(0)

    try:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()
    except Exception as cleanup_err:
        logger.error(f"Error during cleanup: {cleanup_err}")


asyncio.run(main())