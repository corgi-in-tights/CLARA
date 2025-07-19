# v load the intents json file
import json
from pathlib import Path
import pandas as pd

# idk paren stuff
INTENT_DIR = Path(__file__).parent.parent / "intents"

intent_definitions = []
intent_samples = []

def get_intent_definitions():
    if not intent_definitions:
        load_intents_and_samples()
    return intent_definitions.copy()  # same thing as below (non chronological order heresy)

def get_intent_samples():
    if not intent_samples:
        load_intents_and_samples()
    return intent_samples.copy()  # COPY to avoid mutation


# stuff for RAG?
def load_intents_and_samples():
    # definitions are like, metadata
    # samples are the.. samples, utterances, whatever
    # GLOBAL BAD WAHHHHHHHH fuck you
    global intent_definitions, intent_samples
    intent_definitions = []
    intent_samples = []

    for path in INTENT_DIR.rglob("*.json"):
        with open(path, "r", encoding="utf-8") as f:
            intent_data = json.load(f)

        intent_name = path.relative_to(INTENT_DIR).with_suffix("")  # e.g. check_in_timer/start

        # definitions
        intent_definitions.append(
            {
                "intent": str(intent_name),
                "description": intent_data.get("description", ""),
                "slot_schema": intent_data.get("slots", {}),
            }
        )

        # samples
        for utterance, slot_values in intent_data.get("samples", {}).items():
            intent_samples.append({"text": utterance, "intent": str(intent_name), "slots": slot_values})

    return intent_definitions, intent_samples


if __name__ == "__main__":
    load_intents_and_samples()
    print("Definitions:", json.dumps(intent_definitions[:1], indent=2))
    print("Samples:", json.dumps(intent_samples[:2], indent=2))
    
    
    df = pd.DataFrame(intent_samples)

    # Keep only text and intent columns
    df = df[["text", "intent"]]

    print(df.head())

    df.to_csv("intent_dataset.csv", index=False)
