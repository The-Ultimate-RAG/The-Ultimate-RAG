from sqlalchemy import Column, String
from sqlalchemy.orm import relationship, Session

from app.backend.models.base_model import Base
from app.backend.controllers.base_controller import engine
from app.backend.models.chats import Chat


class User(Base):
    __tablename__ = "users"
    id = Column("id", String, primary_key=True, unique=True)
    language = Column("language", String, default="English", nullable=False)
    theme = Column("theme", String, default="light", nullable=False)
    chats = relationship("Chat", back_populates="user")


def add_new_user(id: str) -> None:
    with Session(autoflush=False, bind=engine) as db:
        db.add(
            User(id=id)
        )
        db.commit()


def find_user_by_id(id: str) -> User | None:
    with Session(autoflush=False, bind=engine) as db:
        return db.query(User).where(User.id == id).first()


def update_user(
    user: User, language: str = None, theme: str = None) -> None:
    with Session(autoflush=False, bind=engine) as db:
        user = db.merge(user)
        if language:
            user.language = language
        if theme:
            user.theme = theme
        db.commit()


def get_user_chats(user: User) -> list[Chat]:
    with Session(autoflush=False, bind=engine) as db:
        user = db.get(User, user.id)
        return user.chats


def get_user_last_chat(user: User) -> Chat | None:
    with Session(autoflush=False, bind=engine) as db:
        user = db.get(User, user.id)

        chats = user.chats

        if chats is not None and len(chats):
            return chats[-1]

        return None
