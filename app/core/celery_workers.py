
# worker_start.py (your worker entry point)
import multiprocessing
import os

# MUST BE FIRST - before any imports!
os.environ["PYTHON_MULTIPROCESSING_START_METHOD"] = "spawn"
multiprocessing.set_start_method("spawn", force=True)

from app.settings import app  # Your Celery app import

if __name__ == "__main__":
    app.worker_main([
        "worker",
        "--loglevel=info",
        "-Q", "default,high_priority"
    ])