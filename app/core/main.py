from app.settings import settings, BASE_DIR, logger, setup_logger
from app.backend.models.db_service import automigrate
import aiofiles.os
import uvicorn
import asyncio
import os
import multiprocessing


multiprocessing.set_start_method("spawn", force=True)


async def initialize_system() -> bool:
    path = BASE_DIR
    chats_storage_path = os.path.join(path, "chats_storage")
    database_path = os.path.join(path, "database")

    try:
        await aiofiles.os.makedirs(database_path, exist_ok=True)
        await aiofiles.os.makedirs(chats_storage_path, exist_ok=True)
    except Exception:
        raise RuntimeError("Not all required directories were initialized")

    try:
        # os.system(f"pip install -r {os.path.join(base_path, 'requirements.txt')}")
        pass
    except Exception:
        raise RuntimeError("Not all package were downloaded")


async def main():
    await setup_logger(logger)
    await logger.info("App started!")

    await automigrate()  # Note: it will drop all existing dbs and create a new ones
    await initialize_system()

    config = uvicorn.Config(**settings.api.model_dump())
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
