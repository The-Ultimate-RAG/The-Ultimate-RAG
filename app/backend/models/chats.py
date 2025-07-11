from app.backend.models.base_model import Base
from sqlalchemy import String, Column, ForeignKey
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.controllers.base_controller import engine
from sqlalchemy.future import select

class Chat(Base):
    __tablename__ = "chats"
    id = Column("id", String, primary_key=True, unique=True)
    title = Column("title", String, nullable=True)
    user_id = Column(String, ForeignKey("users.id"))
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", lazy="selectin")


async def add_new_chat(id: str, title: str | None, user) -> None:
    async with AsyncSession(autoflush=False, bind=engine) as db:
        user = await db.merge(user)
        new_chat = Chat(id=id, user_id=user.id, user=user)
        if title:
            new_chat.title = title
        db.add(new_chat)
        await db.commit()


async def get_chat_by_id(id: str) -> Chat | None:
    async with AsyncSession(autoflush=False, bind=engine) as db:
        result = await db.execute(select(Chat).where(Chat.id == id))
        return result.scalar_one_or_none()


async def get_chats_by_user_id(id: str) -> list[Chat]:
    async with AsyncSession(autoflush=False, bind=engine) as db:
        result = await db.execute(
            select(Chat).filter(Chat.user_id == id).order_by(Chat.created_at.desc())
        )
        return result.scalars().all()


async def refresh_title(chat_id: str) -> bool:
    async with AsyncSession(autoflush=False, bind=engine) as db:
        result = await db.execute(
            select(Chat)
            .options(selectinload(Chat.messages))
            .where(Chat.id == chat_id)
        )
        chat = result.scalar_one_or_none()

        if not chat or not chat.messages:
            return False

        chat.title = chat.messages[0].content[:47]
        if len(chat.messages[0].content) > 46:
            chat.title += "..."

        await db.commit()
        return True
