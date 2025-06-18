from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import DateTime, Column
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    __abstract__ = True
    created_at = Column("created_at", DateTime, default=func.now())
    deleted_at = Column("deleted_at", DateTime, nullable=True)
    updated_at = Column("updated_at", DateTime, nullable=True)
