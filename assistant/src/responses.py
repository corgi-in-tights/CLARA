import logging

logger = logging.getLogger("CLARA-assistant")


def send_text_response(websocket, message):
    try:
        await websocket.send_json({"type": "text", "text": message})

    except Exception as e:
        logger.error(f"Error sending text response: {e}")


def send_log_response(websocket, on=True):
    try:
        await websocket.send_json({"type": "log_on" if on else "log_off"})

    except Exception as e:
        logger.error(f"Error sending log response: {e}")
