import os

from app.settings import BASE_DIR


def initialize_system() -> bool:
    success = True
    path = BASE_DIR
    database_path = os.path.join(path, "database")

    print(f"Base path: {BASE_DIR}")
    print(f"Parent path: {path}")
    print(f"Database path: {database_path}")

    try:
        os.makedirs(database_path, exist_ok=True)
        print("Created database_path")
    except Exception as e:
        success = False
        print(f"Error creating directories: {str(e)}")

    try:
        # os.system(f"pip install -r {os.path.join(BASE_DIR, 'app', 'requirements.txt')}")
        pass
    except Exception as e:
        success = False
        print(f"Error installing packages: {str(e)}")

    return success

if __name__ == '__main__':
    print(1111111111111111111111111111111111111111111111)
    print(initialize_system())
    print(2222222222222222222222222222222222222222222222)