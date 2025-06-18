from sqlalchemy import create_engine
from app.settings import postgers_client_config

engine = create_engine(**postgers_client_config)
