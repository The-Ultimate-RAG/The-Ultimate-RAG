from app.settings import settings
from sqlalchemy import create_engine

postgres_config = settings.postgres.model_dump()
engine = create_engine(**postgres_config)
