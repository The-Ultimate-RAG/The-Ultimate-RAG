import api
from settings import api_config, base_path
import uvicorn
import os

def initialize_system() -> bool:
    success = True
    path = os.path.dirname(base_path)
    temp_storage_path = os.path.join(path, os.path.join("app", "temp_storage"))
    temp_storage_path_pdf = os.path.join(path, os.path.join("app", "temp_storage", "pdfs"))
    database_path = os.path.join(path, "database")

    try:
        os.makedirs(temp_storage_path, exist_ok=True)
        os.makedirs(database_path, exist_ok=True)
        os.makedirs(temp_storage_path_pdf, exist_ok=True)
    except Exception:
        success = False
        print("Not all required directories were initialized")
    
    try:
        # os.system(f"pip install -r {os.path.join(base_path, 'requirements.txt')}")
        pass
    except Exception:
        success = False
        print("Not all package were downloaded")

    return success


def main():
    # if not initialize_system():
    #     return
    
    uvicorn.run(**api_config)


if __name__ == '__main__':
    main()
