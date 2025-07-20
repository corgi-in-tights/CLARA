from motor.motor_asyncio import AsyncIOMotorClient
import os

# Global client and collection
mongo_client = None
logs_collection = None

def get_logs_collection():
    return logs_collection

MONGO_URI = os.getenv("MONGO_URI")


async def setup_mongodb(uri=MONGO_URI, db_name="6ix", collection_name="corgino"):
    global mongo_client, logs_collection
    mongo_client = AsyncIOMotorClient(uri)
    logs_collection = mongo_client[db_name][collection_name]
    print("MongoDB connected")

    await list_databases_and_collections(mongo_client)


async def list_databases_and_collections(client):
    print("Databases and collections:")
    db_names = await client.list_database_names()

    for db_name in db_names:
        db = client[db_name]
        collection_names = await db.list_collection_names()
        print(f"- {db_name}")
        for col in collection_names:
            print(f"    • {col}")