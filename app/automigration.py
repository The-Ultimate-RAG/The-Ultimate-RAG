from app.backend.models.db_service import automigrate
import asyncio

if __name__ == "__main__":
    asyncio.run(automigrate())
