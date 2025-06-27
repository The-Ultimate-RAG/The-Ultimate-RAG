import os
import shutil
import subprocess
import sys
import time
import app.settings
from app.settings import settings
from app.backend.create_admin import create_admin_user


def main():
    os.chdir(app.settings.BASE_DIR)

    db_path = os.path.join(app.settings.BASE_DIR, "database")
    
    try:
        shutil.rmtree(db_path)
    except Exception as e:
        print(e)

    os.makedirs(db_path, exist_ok=True)


    qdrant_container_name = "qdrant_instance"
    check_exists_cmd = ["docker", "ps", "-a", "--filter", f"name={qdrant_container_name}", "--format", "{{.ID}}"]
    container_id_result = subprocess.run(check_exists_cmd, capture_output=True, text=True, check=True)
    container_id = container_id_result.stdout.strip()
    if container_id:
        subprocess.run(["docker", "stop", qdrant_container_name], check=False, capture_output=True)
        subprocess.run(["docker", "rm", qdrant_container_name], check=True)

    qdrant_docker_command = [
        "docker", "run",
        "--publish", f"{settings.qdrant.port}:{settings.qdrant.port}",
        "--volume", db_path + ":/qdrant/storage",
        "qdrant/qdrant"
    ]

    qdrant_process = subprocess.Popen(qdrant_docker_command,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      text=True)
    time.sleep(10)

    subprocess.run([sys.executable, "-m", "app.core.automigration"], check=True)

    uvicorn_command = [
        "python", "-m", "app.core.main"
    ]

    subprocess.run(uvicorn_command, check=True)

    create_admin_user()

    qdrant_process.terminate()
    qdrant_process.wait(timeout=5)
    qdrant_process.kill()


if __name__ == "__main__":
    main()
