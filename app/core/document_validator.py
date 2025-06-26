import os

'''
Checks if the given path is valid and file exists
'''
def path_is_valid(path: str) -> bool:
    return os.path.exists(path)