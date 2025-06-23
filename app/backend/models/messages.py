from app.backend.models.base_model import Base
from sqlalchemy import Integer, String, Column, ForeignKey, Text
from sqlalchemy.orm import relationship, Session
from app.backend.controllers.base_controller import engine

class Message(Base):
    __tablename__ = "messages"
    id = Column("id", Integer, autoincrement=True, primary_key=True, unique=True)
    content = Column("text", Text)
    sender = Column("role", String)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    chat = relationship("Chat", back_populates="messages")


def new_message(chat_id: int, sender: str, content: str):
    with Session(autoflush=False, bind=engine) as db:
        db.add(Message(
            content=content,
            sender=sender,
            chat_id=chat_id
        ))
        db.commit()

def get_messages_by_chat_id(id: int) -> list[Message]:
    with Session(autoflush=False, bind=engine) as db:
        return db.query(Message).filter(Message.chat_id==id)