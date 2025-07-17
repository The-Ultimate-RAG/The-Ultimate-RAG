from sqlalchemy import Column, ForeignKey, String, Text, asc
from sqlalchemy.orm import Session, relationship, joinedload

from app.backend.controllers.base_controller import engine
from app.backend.models.base_model import Base


class Message(Base):
    __tablename__ = "messages"
    id = Column("id", String, primary_key=True, unique=True)
    content = Column("text", Text)
    sender = Column("role", String)
    chat_id = Column(String, ForeignKey("chats.id"))
    chat = relationship("Chat", back_populates="messages")
    documents = relationship("Document", back_populates="message")


def add_new_message(id: str, chat_id: str, sender: str, content: str) -> str:
    with Session(autoflush=False, bind=engine) as db:
        new_message = Message(id=id, content=content, sender=sender, chat_id=chat_id)
        db.add(new_message)
        db.commit()
    return id


def get_messages_by_chat_id(id: str) -> list[Message]:
    with Session(autoflush=False, bind=engine) as db:
        return db.query(Message).options(joinedload(Message.documents)).filter(Message.chat_id == id).order_by(asc(Message.created_at))
