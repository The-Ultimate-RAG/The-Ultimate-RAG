from app.settings import settings
from sqlalchemy.ext.asyncio import create_async_engine

postgres_config = settings.postgres.model_dump()
engine = create_async_engine(**postgres_config)
