from app.settings import settings, BASE_DIR
import uvicorn
import os
from app.backend.models.db_service import automigrate


def initialize_system() -> bool:
    path = BASE_DIR
    chats_storage_path = os.path.join(path, "chats_storage")
    database_path = os.path.join(path, "database")

    try:
        os.makedirs(database_path, exist_ok=True)
        os.makedirs(chats_storage_path, exist_ok=True)
    except Exception:
        raise RuntimeError("Not all required directories were initialized")

    try:
        # os.system(f"pip install -r {os.path.join(base_path, 'requirements.txt')}")
        pass
    except Exception:
        raise RuntimeError("Not all package were downloaded")


def main():
    automigrate()  # Note: it will drop all existing dbs and create a new ones
    initialize_system()
    uvicorn.run(**settings.api.model_dump())


if __name__ == "__main__":
    # ATTENTION: run from base dir ---> python -m app.main
    main()
