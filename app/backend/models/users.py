from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship, Session

from app.backend.models.base_model import Base
from app.backend.controllers.base_controller import engine
from app.backend.models.chats import Chat


class User(Base):
    __tablename__ = "users"
    id = Column("id", Integer, autoincrement=True, primary_key=True, unique=True)
    email = Column("email", String, unique=True, nullable=False)
    password_hash = Column("password_hash", String, nullable=False)
    language = Column("language", String, default="English", nullable=False)
    theme = Column("theme", String, default="light", nullable=False)
    access_string_hash = Column("access_string_hash", String, nullable=True)
    chats = relationship("Chat", back_populates="user")


def add_new_user(email: str, password_hash: str, access_string_hash: str) -> int | None:
    with Session(autoflush=False, bind=engine, expire_on_commit=False) as db:
        user = User(
            email=email,
            password_hash=password_hash,
            access_string_hash=access_string_hash,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id


def find_user_by_id(id: int) -> User | None:
    with Session(autoflush=False, bind=engine) as db:
        return db.query(User).where(User.id == id).first()


def find_user_by_email(email: str) -> User | None:
    with Session(autoflush=False, bind=engine) as db:
        return db.query(User).where(User.email == email).first()


def find_user_by_access_string(access_string_hash: str) -> User | None:
    with Session(autoflush=False, bind=engine, expire_on_commit=False) as db:
        user = (
            db.query(User).where(User.access_string_hash == access_string_hash).first()
        )
        return user


def update_user(
    user: User, language: str = None, theme: str = None, access_string_hash: str = None
) -> None:
    with Session(autoflush=False, bind=engine) as db:
        user = db.merge(user)
        if language:
            user.language = language
        if theme:
            user.theme = theme
        if access_string_hash:
            user.access_string_hash = access_string_hash
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
