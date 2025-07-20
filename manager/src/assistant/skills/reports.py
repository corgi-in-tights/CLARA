from datetime import datetime
from ..responses import send_text_response

from src.mongo import get_logs_collection

# Add a transcript log entry
async def add_to_logs(target_url, sentence, initial_response):
    if get_logs_collection() is None:
        raise RuntimeError("MongoDB not initialized. Call setup_mongodb() first.")

    await send_text_response(target_url, initial_response)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    log_entry = {"time": time_str, "transcript": sentence}

    # Update the document for today, appending to the log list
    await get_logs_collection().update_one({"_id": date_str}, {"$push": {"logs": log_entry}}, upsert=True)

    print("Log entry added:", log_entry)
