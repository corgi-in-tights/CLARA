from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Global client and collection
mongo_client = None
logs_collection = None


# Setup MongoDB connection
async def setup_mongodb(uri="mongodb://localhost:27017", db_name="mylogs", collection_name="transcripts"):
    global mongo_client, logs_collection
    mongo_client = AsyncIOMotorClient(uri)
    logs_collection = mongo_client[db_name][collection_name]
    print("MongoDB connected")


# Add a transcript log entry
async def add_to_logs(target_url, sentence, initial_response):
    global logs_collection
    if logs_collection is None:
        raise RuntimeError("MongoDB not initialized. Call setup_mongodb() first.")

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    log_entry = {"time": time_str, "transcript": sentence, "target": target_url, "response": initial_response}

    # Update the document for today, appending to the log list
    await logs_collection.update_one({"_id": date_str}, {"$push": {"logs": log_entry}}, upsert=True)

    print("Log entry added:", log_entry)
