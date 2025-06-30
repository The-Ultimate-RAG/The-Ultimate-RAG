from sqlalchemy import create_engine

from app.settings import postgres_client_config

engine = create_engine(**postgres_client_config)
