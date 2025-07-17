from sqlalchemy import Column, ForeignKey, String, Text, Integer
from sqlalchemy.orm import Session, relationship

from app.backend.controllers.base_controller import engine
from app.backend.models.base_model import Base


class Document(Base):
    __tablename__ = "documents"
    id = Column('id', String, primary_key=True, unique=True)
    name = Column('name', String, nullable=False)
    path = Column('path', String, nullable=False)
    size = Column('size', Integer, nullable=False)
    message_id = Column("message_id", ForeignKey("messages.id"))
    message = relationship("Message", back_populates="documents")


def add_new_document(id: str, name: str, path: str, message_id: str, size: int):
    with Session(autoflush=False, bind=engine) as db:
        new_doc = Document(id=id, name=name, path=path, message_id=message_id, size=size)
        db.add(new_doc)
        db.commit()