from motor.motor_asyncio import AsyncIOMotorClient
import os

# Global client and collection
mongo_client = None
logs_collection = None

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")


async def setup_mongodb(uri=MONGO_URI, db_name="6ix", collection_name="corgino"):
    global mongo_client, logs_collection
    mongo_client = AsyncIOMotorClient(uri)
    logs_collection = mongo_client[db_name][collection_name]
    print("MongoDB connected")
