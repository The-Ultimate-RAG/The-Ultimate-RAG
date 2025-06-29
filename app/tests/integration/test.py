import pytest
import httpx
from app.backend.models.users import find_user_by_email, add_new_user
from app.backend.models.chats import get_chat_by_id
from app.backend.controllers.users import hash_access_string, create_access_token
from app.api import get_latest_chat
from uuid import uuid4
from app.utils import initialize_rag
import os
from app.settings import base_path

BASE_DIR = os.path.dirname(base_path)

BASE_URL = os.environ.get('HF1_URL')


def create_artificial_user() -> dict:
    access_string = "Goida123!"
    access_string_hash = hash_access_string(access_string)
    access_token = create_access_token(access_string)
    email = "Test" + str(uuid4()) + "@test.com"
    password = "Goida123!"
    password_hash = "Goida123!"

    try:
        add_new_user(email=email, password_hash=password_hash, access_string_hash=access_string_hash)
    except:
        raise RuntimeError("Failed to create artificial user")
    
    return {
        "email": email,
        "password": password,
        "password_hash": password_hash,
        "access_string": access_string,
        "access_token": access_token,
        "access_string_hash": access_string_hash
    }


def validate_user_creation():
    payload = {
        "email": "Test1@test.com",
        "password": "Test1@test.com",
    }
    response = httpx.post(url=BASE_URL + '/new_user', json=payload, timeout=30.0)
    try:
        assert response.status_code == 200
    except Exception as e:
        raise RuntimeError(f"Error while trying to create user: Error with API response - status code - {response.status_code} - msg: {e}")

    try:
        assert find_user_by_email("Test1@test.com") is not None
    except Exception as e:
        raise RuntimeError(f"Error while trying to create user: Error with DB response - msg: {e}")
    

# ATTENTION - KOSTYLY - returns newly created chat id and cookie (it is so to avoid another "useful" method for artificial chat creation)
def validate_chat_creation() -> dict:
    user = create_artificial_user()
    cookie = {"access_token": user["access_token"]}

    response = httpx.post(url=BASE_URL + '/new_chat', timeout=30.0, cookies=cookie)
    try:
        assert response.status_code == 303
    except Exception as e:
        raise RuntimeError(f"Error while trying to create chat: Error with API response - status code - {response.status_code} - msg: {e}")

    redirect_to = response.headers.get("location")
    print(redirect_to)

    response = httpx.get(url=BASE_URL + redirect_to, cookies=cookie)
    try:
        assert response.status_code == 200
    except Exception as e:
        raise RuntimeError(f"Error while trying to create chat: Error with API response - status code - {response.status_code} - msg: {e}")
    
    return {
        "chat_id": int(redirect_to.split('/')[-1].split('id=')[-1]),
        "cookie": cookie,
        }


def validate_message_sending():
    data = validate_chat_creation()
    payload = {
        "prompt": "How is your day?",
        "chat_id": data["chat_id"]
    }
    response = httpx.post(url=BASE_URL + "/message_with_docs", cookies=data["cookie"], data=payload, timeout=180)

    try:
        assert response.status_code == 200
    except Exception as e:
        raise RuntimeError(f"Error while trying to send message - error - {e}")


def validate_docs_uploading():
    data = validate_chat_creation()
    file_path = os.path.join(BASE_DIR, "app", "tests", "integration", "testfile.txt")

    with open(file_path, "rb") as f:
        form_fields = {
            "prompt": "How is your day?",
            "chat_id": str(data["chat_id"]),  # must be str, as in form data
        }
        files = [
            ("files", ("testfile.txt", f, "text/plain")),
        ]

        response = httpx.post(
            url=BASE_URL + "/message_with_docs",
            cookies=data["cookie"],
            data=form_fields,
            files=files,
            timeout=180,
        )

    try:
        assert response.status_code == 200
    except Exception as e:
        raise RuntimeError(f"Error while trying to send docs - error - {e}")

if __name__ == '__main__':
    validate_user_creation()
    validate_chat_creation()
    validate_message_sending()
    validate_docs_uploading()