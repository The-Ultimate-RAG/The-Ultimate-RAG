from sqlalchemy import inspect
from app.backend.controllers.base_controller import engine
from app.backend.models.base_model import Base
from app.backend.models.chats import Chat
from app.backend.models.messages import Message
from app.backend.models.users import User


def table_exists(name: str) -> bool:
    return inspect(engine).has_table(name)


def create_tables() -> None:
    Base.metadata.create_all(engine)


def drop_tables() -> None:
    # List tables in the correct order for dropping (considering dependencies)
    tables = [Message.__table__, Chat.__table__, User.__table__]

    for table in tables:
        if table_exists(table.name):
            try:
                table.drop(engine)
                print(f"Dropped table {table.name}")
            except Exception as e:
                print(f"Error dropping table {table.name}: {e}")
        else:
            print(f"Table {table.name} does not exist, skipping drop")


def automigrate() -> None:
    print("Starting automigration...")
    drop_tables()
    create_tables()
    print("Automigration completed.")