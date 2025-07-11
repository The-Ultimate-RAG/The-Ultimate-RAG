from sqlalchemy import inspect
from app.backend.controllers.base_controller import engine
from app.backend.models.base_model import Base
from app.backend.models.chats import Chat
from app.backend.models.messages import Message
from app.backend.models.users import User


async def table_exists(name: str) -> bool:
    async with engine.begin() as conn:
        inspector = inspect(conn)
        tables = await conn.run_sync(inspector.get_table_names)
        return name in tables


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Message.__table__.drop)
        await conn.run_sync(Chat.__table__.drop)
        await conn.run_sync(User.__table__.drop)


async def automigrate() -> None:
    try:
        await drop_tables()
    except Exception as e:
        print(f"Error during drop_tables: {e}")

    await create_tables()
