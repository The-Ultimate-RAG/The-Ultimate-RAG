from app.backend.models.users import User  # noqa: F401
from app.backend.models.chats import Chat  # noqa: F401
from app.backend.models.messages import Message  # noqa: F401
import os
from uuid import uuid4

import httpx

from app.backend.models.messages import get_messages_by_chat_id
from app.settings import BASE_DIR

# BASE_DIR = os.path.dirname(base_path)

# BASE_URL = os.environ.get("HF1_URL")
BASE_URL = os.environ.get('HF1_URL')


def test_create_artificial_user() -> dict:
    email = "Test" + str(uuid4()) + "@test.com"
    password = "Goida123!"
    payload = {"email": email, "password": password}

    # Create user via API
    response = httpx.post(url=BASE_URL + "/new_user", json=payload, timeout=30.0)
    print(f"New user response: {response.status_code} - {response.text}")
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to create artificial user: {response.status_code} - {response.text}"
        )

    # Log in to get access token
    response = httpx.post(url=BASE_URL + "/login", json=payload, timeout=30.0)
    print(f"Login response: {response.status_code} - {response.text}")
    if response.status_code != 200:
        raise RuntimeError(f"Login failed: {response.status_code} - {response.text}")

    access_token = response.cookies.get("access_token") or response.json().get(
        "access_token"
    )
    if not access_token:
        raise RuntimeError("No access token received from login")

    return {"email": email, "password": password, "access_token": access_token}


# ATTENTION - KOSTYLY - returns newly created chat id and cookie (it is so to avoid another "useful" method for artificial chat creation)
def test_validate_chat_creation() -> dict:
    user = test_create_artificial_user()
    print(f"Created user: {user['email']}")

    # Log in to get a valid token
    payload = {"email": user["email"], "password": user["password"]}
    response = httpx.post(url=BASE_URL + "/login", json=payload, timeout=30.0)
    print(f"Login response: {response.status_code} - {response.text}")
    if response.status_code != 200:
        raise RuntimeError(f"Login failed: {response.status_code} - {response.text}")
    access_token = response.cookies.get("access_token") or response.json().get(
        "access_token"
    )
    if not access_token:
        raise RuntimeError("No access token received from login")
    cookie = {"access_token": access_token}
    print(f"Access token: {access_token}")

    # Create chat
    response = httpx.post(url=BASE_URL + "/new_chat", timeout=30.0, cookies=cookie)
    print(
        f"New chat response: {response.status_code} - {response.headers.get('location')}"
    )
    if response.status_code != 303:
        raise RuntimeError(
            f"Error while trying to create chat: {response.status_code} - {response.text}"
        )

    redirect_to = response.headers.get("location")
    if not redirect_to or "login" in redirect_to:
        raise RuntimeError(f"Authentication failed, redirected to: {redirect_to}")

    # Follow redirect
    response = httpx.get(url=BASE_URL + redirect_to, cookies=cookie)
    print(f"Redirect response: {response.status_code}")
    if response.status_code != 200:
        raise RuntimeError(
            f"Error while accessing chat: {response.status_code} - {response.text}"
        )

    try:
        chat_id = int(redirect_to.split("/")[-1].split("id=")[-1])
        print(f"Parsed chat_id: {chat_id}")
    except ValueError as e:
        raise RuntimeError(f"Failed to parse chat_id from URL: {redirect_to} - {e}")

    return {
        "chat_id": chat_id,
        "cookie": cookie,
    }


def test_validate_message_sending():
    data = test_validate_chat_creation()
    if data is None:
        raise RuntimeError("validate_chat_creation returned None")

    payload = {"prompt": "How is your day?", "chat_id": data["chat_id"]}
    response = httpx.post(
        url=BASE_URL + "/message_with_docs",
        cookies=data["cookie"],
        data=payload,
        timeout=180,
    )
    print(f"Message sending response: {response.status_code} - {response.text}")

    try:
        assert response.status_code == 200
    except Exception as e:
        raise RuntimeError(
            f"Error while trying to send message - status: {response.status_code} - error: {e}"
        )


def test_validate_docs_uploading():
    data = test_validate_chat_creation()
    file_path = os.path.join(BASE_DIR, "app", "tests", "integration", "testfile.txt")

    # Create a test file if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("This is a test file for validation.")

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


def test_validate_message_registration():
    data = test_validate_chat_creation()
    initial = get_messages_by_chat_id(data["chat_id"]).count()

    payload = {"prompt": "How is your day?", "chat_id": data["chat_id"]}
    response = httpx.post(
        url=BASE_URL + "/message_with_docs",
        cookies=data["cookie"],
        data=payload,
        timeout=180,
    )
    print(f"Message sending response: {response.status_code} - {response.text}")

    try:
        assert response.status_code == 200
    except Exception as e:
        raise RuntimeError(
            f"Error while trying to send message - status: {response.status_code} - error: {e}"
        )

    after_sending = get_messages_by_chat_id(data["chat_id"]).count()
    print(after_sending, initial)
    try:
        assert after_sending - initial == 2
    except Exception as e:
        raise RuntimeError(
            f"Error while trying to registrate new message - status: {response.status_code} - error: {e}"
        )


# if __name__ == '__main__':
#     try:
#         test_validate_user_creation()
#         test_validate_chat_creation()
#         test_validate_message_sending()
#         test_validate_docs_uploading()
#     except Exception as e:
#         print(f"Test failed: {str(e)}")
#         raise
