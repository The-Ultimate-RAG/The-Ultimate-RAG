from sqlalchemy import create_engine
from app.settings import settings

postgres_config = settings.postgres.model_dump()
engine = create_engine(**postgres_config)
