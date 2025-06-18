from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship, Session
from app.backend.models.base_model import Base
from app.backend.controllers.base_controller import engine

class User(Base):
    __tablename__ = "users"
    id = Column("id", Integer, autoincrement=True, primary_key=True, unique=True)
    email = Column("email", String, unique=True, nullable=False)
    password_hash = Column("password_hash", String, nullable=False)
    language = Column("language", String, default="English", nullable=False)
    theme = Column("theme", String, default="light", nullable=False)
    chats = relationship("Chat", back_populates="user")


def add_new_user(email: str, password_hash: str) -> None:
    with Session(autoflush=False, bind=engine) as db:
        db.add(User(email=email, password_hash=password_hash))
        db.commit()


def find_user_by_id(id: int) -> User | None:
    with Session(autoflush=False, bind=engine) as db:
        return db.query(User).where(User.id == id).first()
    

def find_user_by_email(email: str) -> User | None:
    with Session(autoflush=False, bind=engine) as db:
        return db.query(User).where(User.email == email).first()
    

def update_user(user: User, language: str = None, theme: str = None) -> None:
    with Session(autoflush=False, bind=engine) as db:
        if language:
            user.language = language
        if theme:
            user.theme = theme
        db.commit()
