from .skills.timer import start_timer, stop_timer
from .skills.general import cancel
# from .skills.medication_logging import start_transcribing, stop_transcribing
from .skills.contact import send_to_contact, list_contacts

data = {
    "check_in_timer/start": [start_timer],
    "check_in_timer/stop": [stop_timer],
    "general/cancel": [cancel],
    # "medication_logging/start": [start_transcribing],
    # "medication_logging/finish": [stop_transcribing],
    "emergency_contacts/contact": [send_to_contact],
    "emergency_contacts/list": [list_contacts],
}

def map_intent_to_skill(intent):
    # Dummy mapping for demonstration
    return data.get(intent, None)
