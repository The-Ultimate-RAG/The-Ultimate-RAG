from app.backend.controllers.base_controller import engine
from app.backend.models.base_model import Base
from app.backend.models.chats import Chat
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, joinedload
from sqlalchemy import Column, String
from sqlalchemy.future import select

class User(Base):
    '''
    Base model for users table
    '''
    __tablename__ = "users"
    id = Column("id", String, primary_key=True, unique=True)
    language = Column("language", String, default="English", nullable=False)
    theme = Column("theme", String, default="light", nullable=False)
    chats = relationship("Chat", back_populates="user", lazy="selectin")


async def add_new_user(id: str) -> User:
    async with AsyncSession(engine, expire_on_commit=False) as db:
        new_user = User(id=id)
        db.add(new_user)
        await db.commit()
        return new_user


async def find_user_by_id(id: str) -> User | None:
    async with AsyncSession(engine) as db:
        result = await db.execute(select(User).where(User.id == id))
        return result.scalar_one_or_none()


async def update_user(user: User, language: str = None, theme: str = None) -> None:
    async with AsyncSession(engine) as db:
        user = await db.merge(user)
        if language:
            user.language = language
        if theme:
            user.theme = theme
        await db.commit()

async def get_user_chats(id: str) -> list[Chat]:
    async with AsyncSession(autoflush=False, bind=engine) as db:
        result = await db.execute(
            select(Chat).filter(Chat.user_id == id)
        )
        return result.scalars().all()

async def get_user_last_chat(user: User) -> Chat | None:
    if user is None:
        return None
    async with AsyncSession(engine) as db:
        result = await db.execute(
            select(Chat)
            .where(Chat.user_id == user.id)
            .order_by(Chat.created_at.desc())
            .limit(1)
        )
        chat = result.scalars().first()
        return chat
