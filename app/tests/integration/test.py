from app.backend.models.users import User  # noqa: F401
from app.backend.models.chats import Chat  # noqa: F401
from app.backend.models.messages import Message  # noqa: F401
import os
from uuid import uuid4
import httpx
import pytest
from app.backend.models.messages import get_messages_by_chat_id
from app.settings import BASE_DIR

BASE_URL = os.environ.get('HF1_URL')


# --- Fixtures for Setup ---

@pytest.fixture
def artificial_user():
    """Fixture to create and log in an artificial user, returning user data."""
    email = f"Test{uuid4()}@test.com"
    password = "Goida123!"
    payload = {"email": email, "password": password}

    with httpx.Client(verify=False) as client:
        # Create user
        response = client.post(url=BASE_URL + "/new_user", json=payload, timeout=30.0)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to create artificial user: {response.status_code} - {response.text}")

        # Log in to get access token
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = client.post(url=BASE_URL + "/login", json=payload, headers=headers, timeout=30.0)
        if response.status_code != 200:
            raise RuntimeError(f"Login failed: {response.status_code} - {response.text}")

        # Extract access token from set-cookie header
        set_cookie_header = response.headers.get("set-cookie")
        access_token = None
        if set_cookie_header and "access_token=" in set_cookie_header:
            access_token = set_cookie_header.split("access_token=")[1].split(";")[0]

        if not access_token:
            raise RuntimeError("No access token received from login")

        return {"email": email, "password": password, "access_token": access_token}


@pytest.fixture
def chat_data(artificial_user):
    """Fixture to create a chat for the artificial user, returning chat data."""
    cookie = {"access_token": artificial_user["access_token"]}
    with httpx.Client(verify=False, cookies=cookie) as client:
        # Create chat
        response = client.post(url=BASE_URL + "/new_chat", timeout=30.0)
        if response.status_code != 303:
            raise RuntimeError(f"Error while trying to create chat: {response.status_code} - {response.text}")

        redirect_to = response.headers.get("location")
        if not redirect_to or "login" in redirect_to:
            raise RuntimeError(f"Authentication failed, redirected to: {redirect_to}")

        # Follow redirect
        response = client.get(url=BASE_URL + redirect_to)
        if response.status_code != 200:
            raise RuntimeError(f"Error while accessing chat: {response.status_code} - {response.text}")

        try:
            chat_id = int(redirect_to.split("/")[-1].split("id=")[-1])
        except ValueError as e:
            raise RuntimeError(f"Failed to parse chat_id from URL: {redirect_to} - {e}")

        return {"chat_id": chat_id, "cookie": cookie}


# --- Test Functions ---

def test_create_artificial_user(artificial_user):
    """Test that an artificial user can be created and logged in."""
    assert artificial_user["email"] is not None
    assert artificial_user["password"] == "Goida123!"
    assert artificial_user["access_token"] is not None


def test_validate_chat_creation(chat_data):
    """Test that a chat can be created successfully."""
    assert chat_data["chat_id"] > 0
    assert "access_token" in chat_data["cookie"]


def test_validate_message_sending(chat_data):
    """Test that a message can be sent to the chat."""
    with httpx.Client(verify=False, cookies=chat_data["cookie"]) as client:
        payload = {"prompt": "How is your day?", "chat_id": chat_data["chat_id"]}
        response = client.post(
            url=BASE_URL + "/message_with_docs",
            data=payload,
            timeout=180,
        )
        assert response.status_code == 200, f"Failed to send message: {response.status_code} - {response.text}"


def test_validate_docs_uploading(chat_data):
    """Test that a document can be uploaded with a message."""
    file_path = os.path.join(BASE_DIR, "app", "tests", "integration", "testfile.txt")

    # Create a test file if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("This is a test file for validation.")

    with httpx.Client(verify=False, cookies=chat_data["cookie"]) as client:
        with open(file_path, "rb") as f:
            form_fields = {
                "prompt": "How is your day?",
                "chat_id": str(chat_data["chat_id"]),
            }
            files = [("files", ("testfile.txt", f, "text/plain"))]
            response = client.post(
                url=BASE_URL + "/message_with_docs",
                data=form_fields,
                files=files,
                timeout=180,
            )
        assert response.status_code == 200, f"Failed to upload docs: {response.status_code} - {response.text}"


def test_validate_message_registration(chat_data):
    """Test that a sent message is registered in the chat."""
    with httpx.Client(verify=False, cookies=chat_data["cookie"]) as client:
        initial = get_messages_by_chat_id(chat_data["chat_id"]).count()

        payload = {"prompt": "How is your day?", "chat_id": chat_data["chat_id"]}
        response = client.post(
            url=BASE_URL + "/message_with_docs",
            data=payload,
            timeout=180,
        )
        assert response.status_code == 200, f"Failed to send message: {response.status_code} - {response.text}"

        after_sending = get_messages_by_chat_id(chat_data["chat_id"]).count()
        assert after_sending - initial == 1, "Message was not registered"
