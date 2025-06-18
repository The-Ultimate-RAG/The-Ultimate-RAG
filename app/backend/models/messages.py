from app.backend.models.base_model import Base
from sqlalchemy import Integer, String, Column, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.backend.controllers.base_controller import engine

class Message(Base):
    __tablename__ = "messages"
    id = Column("id", Integer, autoincrement=True, primary_key=True, unique=True)
    content = Column("text", Text)
    sender = Column("role", String)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    chat = relationship("Chat", back_populates="messages")