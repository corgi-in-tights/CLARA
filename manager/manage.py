
import logging
import asyncio
from dotenv import load_dotenv

logger = logging.getLogger("CLARA-manager")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

async def run():
    from src.app import main as app_run
    
    try:
        logger.debug("Starting CLARA Manager...")
        await app_run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        exit() # not graceful lol

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run())