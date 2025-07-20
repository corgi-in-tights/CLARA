from .skills.timer import start_timer, stop_timer
from .skills.general import cancel
from .skills.reports import add_to_logs
from .skills.contact import send_to_contact, list_contacts
from .skills.question import internet_question, local_question

data = {
    # "check_in_timer/start": [start_timer],
    # "check_in_timer/stop": [stop_timer],
    # "general/cancel": [cancel],
    "logging/log_my_day": [add_to_logs],
    # "emergency_contacts/contact": [send_to_contact],
    # "emergency_contacts/list": [list_contacts],
    "question/internet": [internet_question],
    # "question/about_assistant": [local_question],
}

def map_intent_to_skill(intent):
    return data.get(intent, None)
