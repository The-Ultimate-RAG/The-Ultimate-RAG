from app.backend.controllers.base_controller import engine
from app.backend.models.messages import Message
from app.backend.models.base_model import Base
from app.settings import logging, bold_text
from app.backend.models.chats import Chat
from app.backend.models.users import User
from sqlalchemy import inspect


async def table_exists(name: str) -> bool:
    async with engine.begin() as conn:
        inspector = inspect(conn)
        tables = await conn.run_sync(inspector.get_table_names)
        return name in tables


async def create_tables() -> None:
    logging.warning("Start creating tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.warning("End creating tables")


async def drop_tables() -> None:
    logging.warning("Start dropping tables")
    async with engine.begin() as conn:
        await conn.run_sync(Message.__table__.drop)
        await conn.run_sync(Chat.__table__.drop)
        await conn.run_sync(User.__table__.drop)
    logging.warning("End dropping tables")


async def automigrate() -> None:
    logging.warning("Start migration")
    try:
        await drop_tables()
    except Exception as e:
        logging.error(bold_text("Error during drop_tables: ") + str(e))
    try:
        await create_tables()
    except Exception as e:
        logging.error(bold_text("Error during create_tables: ") + str(e))
    logging.warning("End migration\n\n")
