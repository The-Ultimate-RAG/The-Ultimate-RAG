from app.backend.models.base_model import Base
from sqlalchemy import Integer, String, Column, ForeignKey
from sqlalchemy.orm import relationship

class Chat(Base):
    __tablename__ = "chats"
    id = Column("id", Integer, autoincrement=True, primary_key=True, unique=True)
    title = Column("title", String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat")