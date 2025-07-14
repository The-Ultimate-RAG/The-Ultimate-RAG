import os
from app.settings import BASE_DIR


def initialize_system() -> bool:
    success = True
    path = BASE_DIR
    temp_storage_path = os.path.join(path, "app", "temp_storage")
    pdfs_path = os.path.join(path, "app", "temp_storage", "pdfs")
    models_io_path = os.path.join(path, "models_io")
    database_path = os.path.join(path, "database")
    chats_storage_path = os.path.join(path, "chats_storage")

    print(f"Base path: {BASE_DIR}")
    print(f"Parent path: {path}")
    print(f"Temp storage path: {temp_storage_path}")
    print(f"PDFs path: {pdfs_path}")
    print(f"Model's i/o path: {models_io_path}")
    print(f"Database path: {database_path}")
    print(f"Chats storage path: {chats_storage_path}")

    try:
        os.makedirs(temp_storage_path, exist_ok=True)
        print("Created temp_storage_path")
        os.makedirs(pdfs_path, exist_ok=True)
        print("Created pdfs_path")
        os.makedirs(database_path, exist_ok=True)
        print("Created database_path")
        os.makedirs(models_io_path, exist_ok=True)
        print("Created models_io_path")
        os.makedirs(chats_storage_path, exist_ok=True)
        print("Created chats_storage_path")
    except Exception as e:
        success = False
        print(f"Error creating directories: {str(e)}")

    return success


if __name__ == "__main__":
    print("Start system initialization")
    result = initialize_system()
    print("Initialization - " + ("SUCCESS" if result else "FAIL"))
    print("End system initialization\n")
