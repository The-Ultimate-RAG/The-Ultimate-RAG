
import multiprocessing
import os

# MUST BE FIRST - before any imports!
os.environ["PYTHON_MULTIPROCESSING_START_METHOD"] = "spawn"
multiprocessing.set_start_method("spawn", force=True)


from app.settings import app


def main():
    app.worker_main([
        "worker",
        "--pool=threads",
        "--concurrency=1",
        "--loglevel=info",
        "-Q", "default,high_priority"
    ])


if __name__ == "__main__":
    main()