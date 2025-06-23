from app.backend.models.users import User
from app.backend.models.chats import Chat
from app.backend.models.messages import Message
from app.backend.controllers.base_controller import engine
from app.backend.models.base_model import Base


def table_exists(name: str) -> bool:
    return engine.dialect.has_table(engine, name)

def create_tables() -> None:
    Base.metadata.create_all(engine)

def drop_tables() -> None:
    # for now the order matters, so
    # TODO: add cascade deletion for models
    Message.__table__.drop(engine)
    Chat.__table__.drop(engine)
    User.__table__.drop(engine)

def automigrate() -> None:
    try:
        drop_tables()
    except Exception as e:
        print(e)

    create_tables()