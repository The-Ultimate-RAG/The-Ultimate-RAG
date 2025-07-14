from app.settings import BASE_DIR
from app.settings import logging
import os


def initialize_system() -> bool:
    success = True
    path = BASE_DIR
    temp_storage_path = os.path.join(path, "app", "temp_storage")
    pdfs_path = os.path.join(path, "app", "temp_storage", "pdfs")
    models_io_path = os.path.join(path, "models_io")
    database_path = os.path.join(path, "database")
    chats_storage_path = os.path.join(path, "chats_storage")

    logging.info("Base path: {BASE_DIR}")
    logging.info(f"Parent path: {path}")
    logging.info(f"Temp storage path: {temp_storage_path}")
    logging.info(f"PDFs path: {pdfs_path}")
    logging.info(f"Model's i/o path: {models_io_path}")
    logging.info(f"Database path: {database_path}")
    logging.info(f"Database path: {chats_storage_path}")

    try:
        os.makedirs(temp_storage_path, exist_ok=True)
        logging.info("Created temp_storage_path")
        os.makedirs(pdfs_path, exist_ok=True)
        logging.info("Created pdfs_path")
        os.makedirs(database_path, exist_ok=True)
        logging.info("Created database_path")
        os.makedirs(models_io_path, exist_ok=True)
        logging.info("Created models_io_path")
        os.makedirs(chats_storage_path, exist_ok=True)
        logging.info("Created chats_storage_path")
    except Exception as e:
        success = False
        logging.info(f"Error creating directories: {str(e)}")

    return success


if __name__ == "__main__":
    logging.warning("Start system initialization")
    logging.info("Initialization - " + "SUCCESS" if initialize_system() else "FAIL")
    logging.warning("End system initialization\n\n")
