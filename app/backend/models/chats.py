from app.backend.models.base_model import Base
from app.backend.models.users import User
from sqlalchemy import Integer, String, Column, ForeignKey
from sqlalchemy.orm import relationship, Session
from app.backend.controllers.base_controller import engine

class Chat(Base):
    __tablename__ = "chats"
    id = Column("id", Integer, autoincrement=True, primary_key=True, unique=True)
    title = Column("title", String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat")


def new_chat(title: str | None, user: User) -> int:
    id = None
    with Session(autoflush=False, bind=engine) as db:
        new_chat = Chat(user_id=user.id, user=user)
        if title:
            new_chat.title = title
        db.add(new_chat)
        db.commit()
        id = new_chat.id
    return id