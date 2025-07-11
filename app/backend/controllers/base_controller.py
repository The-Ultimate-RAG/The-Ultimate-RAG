from app.settings import settings
from sqlalchemy.ext.asyncio import create_async_engine

postgres_config = settings.postgres.model_dump()

engine = create_async_engine(
    "postgresql+asyncpg://postgres:1121@localhost:5432/exp",
    echo=False
)
