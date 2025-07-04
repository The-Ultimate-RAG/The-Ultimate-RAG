from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import Session, relationship

from app.backend.controllers.base_controller import engine
from app.backend.models.base_model import Base


class Message(Base):
    __tablename__ = "messages"
    id = Column("id", String, primary_key=True, unique=True)
    content = Column("text", Text)
    sender = Column("role", String)
    chat_id = Column(String, ForeignKey("chats.id"))
    chat = relationship("Chat", back_populates="messages")


def add_new_message(id: str, chat_id: str, sender: str, content: str):
    with Session(autoflush=False, bind=engine) as db:
        new_message = Message(id=id, content=content, sender=sender, chat_id=chat_id)
        db.add(new_message)
        db.commit()


def get_messages_by_chat_id(id: str) -> list[Message]:
    with Session(autoflush=False, bind=engine) as db:
        return db.query(Message).filter(Message.chat_id == id)
