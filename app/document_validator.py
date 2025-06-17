import os

def path_is_valid(path: str) -> bool:
    return os.path.exists(path)