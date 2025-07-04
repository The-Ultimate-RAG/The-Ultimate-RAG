from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    '''
    Base model for all others \\
    Defines base for table creation
    '''
    __abstract__ = True
    created_at = Column("created_at", DateTime, default=func.now())
    deleted_at = Column("deleted_at", DateTime, nullable=True)
    updated_at = Column("updated_at", DateTime, nullable=True)
