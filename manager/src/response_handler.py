# types of responses
# TYPE: TEXT
# TYPE: LOG_ON
# TYPE: LOG_OFF


def handle_incoming_response(response):
    if not response or not isinstance(response, dict) or "type" not in response:
        print("Invalid response format: 'type' key is missing.")
        return None

    if response["type"] == "TEXT":
        return handle_text_response(response)
    elif response["type"] == "LOG_ON":
        return handle_log_on_response(response)
    elif response["type"] == "LOG_OFF":
        return handle_log_off_response(response)
    else:
        print(f"Unknown response type: {response['type']}")
        return None


def handle_text_response(response):
    if "text" not in response:
        print("Invalid TEXT response format: 'text' key is missing.")
        return None

    text = response["text"]

    print(f"Text response: {text}")
    # HANDLE STUFF HERE

    return text


def handle_log_on_response(response):
    print("Log ON")
    # HANDLE STUFF HER


def handle_log_off_response(response):
    print("Log OFF")
    # HANDLE STUFF HERE

