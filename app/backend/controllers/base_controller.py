from sqlalchemy import create_engine
from app.settings import settings

postgres_config = settings.postgres.model_dump()
db_url = settings.postgres.url.get_secret_value() # This is the crucial line
postgres_config['url'] = db_url
engine = create_engine(**postgres_config)