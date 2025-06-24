import os
from app.settings import base_path

def initialize_system() -> bool:
    success = True
    path = os.path.dirname(base_path)
    temp_storage_path = os.path.join(path, "app", "temp_storage")
    pdfs_path = os.path.join(path, "app", "temp_storage", "pdfs")
    database_path = os.path.join(path, "database")

    print(f"Base path: {base_path}")
    print(f"Parent path: {path}")
    print(f"Temp storage path: {temp_storage_path}")
    print(f"PDFs path: {pdfs_path}")
    print(f"Database path: {database_path}")

    try:
        os.makedirs(temp_storage_path, exist_ok=True)
        print("Created temp_storage_path")
        os.makedirs(pdfs_path, exist_ok=True)
        print("Created pdfs_path")
        os.makedirs(database_path, exist_ok=True)
        print("Created database_path")
    except Exception as e:
        success = False
        print(f"Error creating directories: {str(e)}")

    try:
        # os.system(f"pip install -r {os.path.join(base_path, 'requirements.txt')}")
        pass
    except Exception as e:
        success = False
        print(f"Error installing packages: {str(e)}")

    return success

if __name__ == '__main__':
    print(1111111111111111111111111111111111111111111111)
    print(initialize_system())
    print(2222222222222222222222222222222222222222222222)