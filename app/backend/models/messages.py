from sqlalchemy import Column, ForeignKey, String, Text, select
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.controllers.base_controller import engine
from app.backend.models.base_model import Base


class Message(Base):
    __tablename__ = "messages"
    id = Column("id", String, primary_key=True, unique=True)
    content = Column("text", Text)
    sender = Column("role", String)
    chat_id = Column(String, ForeignKey("chats.id"))
    chat = relationship("Chat", back_populates="messages")


async def add_new_message(id: str, chat_id: str, sender: str, content: str):
    async with AsyncSession(engine) as db:
        new_message = Message(id=id, content=content, sender=sender, chat_id=chat_id)
        db.add(new_message)
        await db.commit()


async def get_messages_by_chat_id(id: str) -> list[Message]:
    async with AsyncSession(engine) as db:
        result = await db.execute(
            select(Message).where(Message.chat_id == id)
        )
        return result.scalars().all()
