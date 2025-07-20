# import numpy as np
# import asyncio
# import pyaudio
# import logging
# import wave
# import struct
# import pvporcupine
# import os
# from scipy.signal import resample_poly

# wake_word_detected = asyncio.Event()

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())

# SAMPLE_RATE = 48000            # Samples per second (Hz)
# CHANNELS = 1                   # Mono audio
# SAMPLE_WIDTH = 2               # Bytes per sample (16-bit = 2 bytes)

# target_16k_samples = 512
# upsample_ratio = 3  # 48k / 16k
# FRAMES_PER_BUFFER = target_16k_samples * upsample_ratio  # 512 * 3 = 1536



# wav_file = wave.open("filtered_audio.wav", "wb")
# wav_file.setnchannels(1)  # mono audio
# wav_file.setsampwidth(2)  # 16-bit audio = 2 bytes per sample
# wav_file.setframerate(16000)  # sample rate (Hz)



# def audio_gate(audio_chunk, threshold=1000):
#     # audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
#     # avg_amplitude = np.mean(np.abs(audio_array))
    
#     # return avg_amplitude > threshold
#     return True

# # def audio_gate(audio_chunk, peak_thresh=500, rms_thresh=300):
# #     print(len(audio_chunk))
# #     audio = np.frombuffer(audio_chunk, dtype=np.int16)
# #     if audio.size == 0:
# #         return False
# #     peak = np.max(np.abs(audio))
# #     rms = np.sqrt(np.mean(audio.astype(np.float32) ** 2))
# #     return peak > peak_thresh and rms > rms_thresh

# def downsample_48k_to_16k(audio_chunk_48k):
#     audio_array = np.frombuffer(audio_chunk_48k, dtype=np.int16)
#     audio_16k = resample_poly(audio_array, up=1, down=3)
#     return audio_16k.astype(np.int16).tobytes()


# def read_audio_stream(pa, stream, **kwargs):
#     audio_chunk_48k = stream.read(FRAMES_PER_BUFFER, **kwargs)
#     if audio_gate(audio_chunk_48k):
#         return downsample_48k_to_16k(audio_chunk_48k)
#     return None

# async def wake_word_listener(wake_word_event, pa, stream, porcupine):
#     logger.info("Starting to listen for wake word...")

#     try:
#         while True:
#             # Read audio frame from the stream (blocking call)
#             # pcm_bytes = stream.read(porcupine.frame_length, exception_on_overflow=False)
#             filtered_chunk_16k = read_audio_stream(pa, stream, exception_on_overflow=False)
#             if filtered_chunk_16k is None:
#                 continue
            
#             wav_file.writeframes(filtered_chunk_16k)
            
#             pcm = struct.unpack_from("h" * porcupine.frame_length, filtered_chunk_16k)

#             # Process frame for wake word detection
#             keyword_index = porcupine.process(pcm)

#             if keyword_index >= 0:
#                 logger.info("Wake word detected!")

#                 # Notify that wake word was detected
#                 wake_word_event.set()

#                 # Wait for the main loop or transcription to clear event
#                 while wake_word_event.is_set():
#                     await asyncio.sleep(0.1)
                    
#                 logger.debug("Wake word detection handled.")

#             # Yield control to event loop to avoid blocking
#             await asyncio.sleep(0)

#     except asyncio.CancelledError:
#         logger.info("Wake word listener cancelled")
#     except Exception as e:
#         logger.error(f"Error in wake_word_listener: {e}")
#     finally:
#         if stream.is_active():
#             stream.stop_stream()
#         stream.close()
#         pa.terminate()
#         porcupine.delete()
#         logger.debug("Wake word listener stopped and resources released.")



# async def deepgram_transcriber(pa, stream, dg_connection, utterence_end_event):
#     # Reset the utterance end event when this task starts
#     utterence_end_event.clear()

#     # Transcription loop, exits early if event is set or timeout hits
#     start = asyncio.get_event_loop().time()

#     try:
#         # Keep transcribing audio chunks until the utterance event is set
#         while not utterence_end_event.is_set():
            
#             if asyncio.get_event_loop().time() - start > 8:
#                 logger.debug("⏱️ 8-second transcription timeout reached.")
#                 break
            
#             if utterence_end_event.is_set():
#                 logger.debug("✅ Utterance end detected.")
#                 break
            
            
#             filtered_chunk_16k = read_audio_stream(pa, stream)
            
#             if filtered_chunk_16k is not None:
#                 logger.debug("Transcribing...")
#                 wav_file.writeframes(filtered_chunk_16k)

#                 # Send to Deepgram connection
#                 await dg_connection.send(filtered_chunk_16k)
                
#             await asyncio.sleep(0) 
#     except asyncio.CancelledError:
#         logger.debug("Transcription task was cancelled.")
#     finally:
#         await dg_connection.finish()  # gracefully kill
#         logger.debug("Finished transcribing event.")


# async def main():
#     logger.info("Starting audio streaming to Deepgram and Porcupine...")
#     porcupine = pvporcupine.create(keyword_paths=["config/clara-mac.ppn"], access_key=os.getenv("PORCUPINE_ACCESS_KEY"))

#     pa = pyaudio.PyAudio()

#     stream = pa.open(
#         format=pyaudio.paInt16,         
#         channels=CHANNELS,
#         rate=SAMPLE_RATE,
#         input=True,
#         frames_per_buffer=FRAMES_PER_BUFFER,
#         input_device_index=0
#     )

#     from .transcription import connect_to_dg
    
#     dg_connection, utterence_end_event = await connect_to_dg()
    
#     logger.info("Starting main loop for dual audio stream...\n")
    
    
#     asyncio.create_task(wake_word_listener(wake_word_detected, pa, stream, porcupine))
#     transcription_task = None

#     while True:
#         logger.debug("Waiting on wake word in main loop!")
#         await wake_word_detected.wait()

#         # if there is transcription happening, cancel it and start a new one
#         if transcription_task and not transcription_task.done():
#             transcription_task.cancel()

#         wake_word_detected.clear()
#         logger.debug("Cleared wake word event %s, state:", wake_word_detected.is_set())

#         # Start a new transcription task
#         # Continues till interrupted, cancelled or naturally finished
#         logger.debug("Starting transcription task after wake word detected...")
#         transcription_task = asyncio.create_task(deepgram_transcriber(pa, stream, dg_connection, utterence_end_event))
        
#         # yield back control before looping
#         # await asyncio.sleep(0)

#     try:
#         stream.stop_stream()
#         stream.close()
#         pa.terminate()
#         porcupine.delete()
#     except Exception as cleanup_err:
#         logger.error(f"Error during cleanup: {cleanup_err}")

from .assistant.main import process_item

async def main():
    print(await process_item({"sentence": "Hello, how are you?"}))
    