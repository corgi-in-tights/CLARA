
import logging
import asyncio
from dotenv import load_dotenv

logger = logging.getLogger("CLARA-manager")

async def run():
    from src.app import run as app_run
    
    try:
        await app_run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        exit() # not graceful lol

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run())