# test_server.py
import asyncio
import websockets
import json
import random


async def mock_deepgram_server(websocket):
    """Improved mock Deepgram server with non-blocking audio handling"""
    # Send initial metadata
    await websocket.send(json.dumps({"type": "Metadata", "request_id": "test_123", "created": "2023-01-01T00:00:00Z"}))

    # Test phrases and state
    test_phrases = [
        "Hello world",
        "This is a test",
        "Audio transcription working",
        "Microphone input detected",
        "Testing testing 123",
    ]

    try:
        while True:
            try:
                # Wait up to 0.1 seconds for a message
                await asyncio.wait_for(websocket.recv(), timeout=0.1)
            except asyncio.TimeoutError:
                # No message received within 0.1s — proceed to maybe send a mock response
                pass

            # Randomly send a transcription
            if random.random() > 0.05:  # 30% chance
                print("Sending mock transcription response")
                response = {
                    "channel": {
                        "alternatives": [
                            {
                                "transcript": random.choice(test_phrases),
                                "confidence": random.random()
                            }
                        ]
                    }
                }
                await websocket.send(json.dumps(response))

            await asyncio.sleep(0.1)  # pacing

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    except Exception as e:
        print(f"Server error: {e}")


async def main():
    async with websockets.serve(mock_deepgram_server, "localhost", 8765):
        print("Test WebSocket server running at ws://localhost:8765")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
