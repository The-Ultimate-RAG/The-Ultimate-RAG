from app.settings import api_config, base_path
import uvicorn
import os
from app.backend.models.db_service import automigrate

def initialize_system() -> bool:
    path = os.path.dirname(base_path)
    temp_storage_path = os.path.join(path, os.path.join("app", "temp_storage"))
    temp_storage_path_pdf = os.path.join(path, os.path.join("app", "temp_storage", "pdfs"))
    database_path = os.path.join(path, "database")

    try:
        os.makedirs(temp_storage_path, exist_ok=True)
        os.makedirs(database_path, exist_ok=True)
        os.makedirs(temp_storage_path_pdf, exist_ok=True)
    except Exception:
        raise RuntimeError("Not all required directories were initialized")
    
    try:
        # os.system(f"pip install -r {os.path.join(base_path, 'requirements.txt')}")
        pass
    except Exception:
        raise RuntimeError("Not all package were downloaded")
    

def main():
    # automigrate() # Note: it will drop all existing dbs and create a new ones
    initialize_system()
    uvicorn.run(**api_config)


if __name__ == '__main__':
    # ATTENTION: run from base dir ---> python -m app.main
    main()
