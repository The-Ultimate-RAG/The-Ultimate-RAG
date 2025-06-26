from app.backend.models.base_model import Base
from sqlalchemy import Integer, String, Column, ForeignKey
from sqlalchemy.orm import relationship, Session
from app.backend.controllers.base_controller import engine
from app.backend.models.messages import Message

class Chat(Base):
    __tablename__ = "chats"
    id = Column("id", Integer, autoincrement=True, primary_key=True, unique=True)
    title = Column("title", String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat")


def new_chat(title: str | None, user) -> int:
    id = None
    with Session(autoflush=False, bind=engine) as db:
        user = db.merge(user)
        new_chat = Chat(user_id=user.id, user=user)
        if title:
            new_chat.title = title
        db.add(new_chat)
        db.commit()
        id = new_chat.id
    return id


def get_chat_by_id(id: int) -> Chat | None:
    with Session(autoflush=False, bind=engine) as db:
        return db.query(Chat).where(Chat.id==id).first()


def get_chats_by_user_id(id: int) -> list[Chat]:
    with Session(autoflush=False, bind=engine) as db:
        return db.query(Chat).filter(Chat.user_id==id).order_by(Chat.created_at.desc())
    

def refresh_title(chat_id: int) -> bool:
    with Session(autoflush=False, bind=engine) as db:
        chat = db.get(Chat, chat_id)
        messages = chat.messages

        if messages is None or len(messages) == 0:
            return False
        
        chat.title = messages[0].content[:47]
        if len(messages[0].content) > 46:
            chat.title += "..."
        
        db.commit()
        return True