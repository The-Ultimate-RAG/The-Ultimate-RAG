import os
from uuid import uuid4
import re
import httpx
import pytest
import pytest_asyncio
from app.backend.models.users import User  # noqa: F401
from app.backend.models.chats import Chat  # noqa: F401
from app.backend.models.messages import Message, get_messages_by_chat_id  # noqa: F401
from app.settings import BASE_DIR

BASE_URL = os.environ.get('HF1_URL')


# --- Async Fixtures for Setup ---
@pytest_asyncio.fixture
async def artificial_user():
    """Fixture to create and log in an artificial user, returning user data."""
    email = f"Test{uuid4()}@test.com"
    password = "Goida123!"
    payload = {"email": email, "password": password}

    async with httpx.AsyncClient(verify=False) as client:
        # Create user
        response = await client.post(url=BASE_URL + "/new_user", json=payload, timeout=30.0)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to create artificial user: {response.status_code} - {response.text}")

        id = response.json().get("id", -1)

        # Log in to get access token
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = await client.post(url=BASE_URL + "/login", json=payload, headers=headers, timeout=30.0)
        if response.status_code != 200:
            raise RuntimeError(f"Login failed: {response.status_code} - {response.text}")

        # Extract access token from set-cookie header
        set_cookie_header = response.headers.get("set-cookie")
        access_token = None
        if set_cookie_header and "access_token=" in set_cookie_header:
            access_token = set_cookie_header.split("access_token=")[1].split(";")[0]

        if not access_token:
            raise RuntimeError("No access token received from login")

        return {"id": id, "email": email, "password": password, "access_token": access_token}


@pytest_asyncio.fixture
async def chat_data(artificial_user):
    """Fixture to create a chat for the artificial user, returning chat data."""
    cookie = {"access_token": artificial_user["access_token"]}
    async with httpx.AsyncClient(verify=False, cookies=cookie) as client:
        # Create chat
        response = await client.post(url=BASE_URL + "/new_chat", timeout=30.0)
        if response.status_code != 303:
            raise RuntimeError(f"Error while trying to create chat: {response.status_code} - {response.text}")

        redirect_to = response.headers.get("location")
        if not redirect_to or "login" in redirect_to:
            raise RuntimeError(f"Authentication failed, redirected to: {redirect_to}")

        # Follow redirect
        response = await client.get(url=BASE_URL + redirect_to)
        if response.status_code != 200:
            raise RuntimeError(f"Error while accessing chat: {response.status_code} - {response.text}")

        try:
            chat_id = int(redirect_to.split("/")[-1].split("id=")[-1])
        except ValueError as e:
            raise RuntimeError(f"Failed to parse chat_id from URL: {redirect_to} - {e}")

        res = {"chat_id": chat_id, "user": artificial_user, "cookie": cookie}
        print(res)
        return res


# --- Async Test Functions ---
@pytest.mark.asyncio
async def test_create_artificial_user(artificial_user):
    """Test that an artificial user can be created and logged in."""
    assert artificial_user["email"] is not None
    assert artificial_user["password"] == "Goida123!"
    assert artificial_user["access_token"] is not None


@pytest.mark.asyncio
async def test_validate_chat_creation(chat_data):
    """Test that a chat can be created successfully."""
    assert chat_data["chat_id"] > 0
    assert "access_token" in chat_data["cookie"]


@pytest.mark.asyncio
async def test_validate_message_sending(chat_data):
    """Test that a message can be sent to the chat."""
    async with httpx.AsyncClient(verify=False, cookies=chat_data["cookie"]) as client:
        payload = {"prompt": "How is your day?", "chat_id": chat_data["chat_id"]}
        response = await client.post(
            url=BASE_URL + "/message_with_docs",
            data=payload,
            timeout=180,
        )
        assert response.status_code == 200, f"Failed to send message: {response.status_code} - {response.text}"


@pytest.mark.asyncio
async def test_validate_docs_uploading(chat_data):
    """Test that a document can be uploaded with a message."""
    file_path = os.path.join(BASE_DIR, "app", "tests", "integration", "testfile.txt")

    # Create a test file if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("This is a test file for validation.")

    async with httpx.AsyncClient(verify=False, cookies=chat_data["cookie"]) as client:
        with open(file_path, "rb") as f:
            form_fields = {
                "prompt": "How is your day?",
                "chat_id": str(chat_data["chat_id"]),
            }
            files = [("files", ("testfile.txt", f, "text/plain"))]
            response = await client.post(
                url=BASE_URL + "/message_with_docs",
                data=form_fields,
                files=files,
                timeout=180,
            )
        assert response.status_code == 200, f"Failed to upload docs: {response.status_code} - {response.text}"


@pytest.mark.asyncio
async def test_validate_message_registration(chat_data):
    """Test that a sent message is registered in the chat."""
    async with httpx.AsyncClient(verify=False, cookies=chat_data["cookie"]) as client:
        initial = get_messages_by_chat_id(chat_data["chat_id"]).count()

        payload = {"prompt": "How is your day?", "chat_id": chat_data["chat_id"]}
        response = await client.post(
            url=BASE_URL + "/message_with_docs",
            data=payload,
            timeout=180,
        )
        assert response.status_code == 200, f"Failed to send message: {response.status_code} - {response.text}"

        after_sending = get_messages_by_chat_id(chat_data["chat_id"]).count()
        assert after_sending - initial == 1, "Message was not registered"


@pytest.mark.asyncio
async def test_document_creation(chat_data):
    """Test that local storage is created properly and document is saved right to it."""
    file_path = os.path.join(BASE_DIR, "app", "tests", "integration", "testfile.txt")
    # Create a test file if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("This is a test file for validation.")

    path_to_storage = os.path.join(BASE_DIR, "chats_storage", f"user_id={chat_data['user']['id']}", f"chat_id={chat_data['chat_id']}", "documents")
    before_request = len(os.listdir(path_to_storage))

    async with httpx.AsyncClient(verify=False, cookies=chat_data["cookie"]) as client:
        with open(file_path, "rb") as f:
            form_fields = {
                "prompt": "How is your day?",
                "chat_id": str(chat_data["chat_id"]),
            }
            files = [("files", ("testfile.txt", f, "text/plain"))]
            response = await client.post(
                url=BASE_URL + "/message_with_docs",
                data=form_fields,
                files=files,
                timeout=180,
            )
        assert response.status_code == 200, f"Failed to upload docs: {response.status_code} - {response.text}"

    after_request = len(os.listdir(path_to_storage))
    assert after_request - before_request == 2


@pytest.mark.asyncio
async def test_document_content(chat_data):
    """Test that document that was sent is the same with the stored one."""
    file_path = os.path.join(BASE_DIR, "app", "tests", "integration", "testfile.txt")
    # Create a test file if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("This is a test file for validation.")

    path_to_storage = os.path.join(BASE_DIR, "chats_storage", f"user_id={chat_data['user']['id']}", f"chat_id={chat_data['chat_id']}", "documents")
    before_request = len(os.listdir(path_to_storage))

    async with httpx.AsyncClient(verify=False, cookies=chat_data["cookie"]) as client:
        with open(file_path, "rb") as f:
            form_fields = {
                "prompt": "How is your day?",
                "chat_id": str(chat_data["chat_id"]),
            }
            files = [("files", ("testfile.txt", f, "text/plain"))]
            response = await client.post(
                url=BASE_URL + "/message_with_docs",
                data=form_fields,
                files=files,
                timeout=180,
            )
        assert response.status_code == 200, f"Failed to upload docs: {response.status_code} - {response.text}"

    after_request = len(os.listdir(path_to_storage))
    assert after_request - before_request == 2

    file_name = [file for file in os.listdir(path_to_storage) if "pdfs" not in file][0]
    with open(os.path.join(path_to_storage, file_name), "r") as stored:
        stored_content = stored.read()

    with open(file_path, "r") as stored:
        posted_content = stored.read()

    assert posted_content == stored_content


@pytest.mark.asyncio
async def test_document_uploading_speed(chat_data):
    """Test that document uploading meets timeout requirements."""
    file_path = os.path.join(BASE_DIR, "app", "tests", "integration", "testfile2.txt")
    # Create a test file if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("This is a test file for validation.\n" * 1000000)

    async with httpx.AsyncClient(verify=False, cookies=chat_data["cookie"]) as client:
        with open(file_path, "rb") as f:
            form_fields = {
                "prompt": "How is your day?",
                "chat_id": str(chat_data["chat_id"]),
            }
            files = [("files", ("testfile2.txt", f, "text/plain"))]
            try:
                response = await client.post(
                    url=BASE_URL + "/message_with_docs",
                    data=form_fields,
                    files=files,
                    timeout=50,
                )
                assert response.status_code == 200, f"Failed to upload docs: {response.status_code} - {response.text}"
            except httpx.TimeoutException:
                raise RuntimeError("The loading speed of large documents is too slow")


@pytest.mark.asyncio
async def test_xss_protection(chat_data):
    """Test that messages are protected from XSS attacks."""
    async with httpx.AsyncClient(verify=False, cookies=chat_data["cookie"]) as client:
        payload = {"prompt": "<script>How is your day?<script>", "chat_id": chat_data["chat_id"]}
        response = await client.post(
            url=BASE_URL + "/message_with_docs",
            data=payload,
            timeout=180,
        )
        assert response.status_code == 200, f"Failed to send message: {response.status_code} - {response.text}"

    async with httpx.AsyncClient(verify=False, cookies=chat_data["cookie"]) as client:
        payload = {"chat_id": chat_data["chat_id"]}
        response = await client.post(
            url=BASE_URL + f"/chats/id={chat_data['chat_id']}/history",
            data=payload,
            timeout=180,
        )
        response_json = response.json()
        for message in response_json.get("history", [None]):
            if message and "script" in message.get("content", ""):
                raise RuntimeError("Messages are not protected from XSS attacks")


@pytest.mark.asyncio
async def test_source_citation(chat_data):
    """Test that a document can be uploaded with a message and cited."""
    file_path = os.path.join(BASE_DIR, "app", "tests", "integration", "testfile3.txt")

    # Create a test file if it doesn't exist
    if os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("How is your day: My day is good.")

    async with httpx.AsyncClient(verify=False, cookies=chat_data["cookie"]) as client:
        with open(file_path, "rb") as f:
            form_fields = {
                "prompt": "How is your day? CITE THE DOCUMENT THAT WILL BE ATTACHED!",
                "chat_id": str(chat_data["chat_id"]),
            }
            files = [("files", ("testfile3.txt", f, "text/plain"))]
            response = await client.post(
                url=BASE_URL + "/message_with_docs",
                data=form_fields,
                files=files,
                timeout=180,
            )
        assert response.status_code == 200, f"Failed to upload docs: {response.status_code} - {response.text}"
        text = ""
        async for chunk in response.aiter_text():
            text += chunk
        with open(file_path, "w") as f:
            f.write(text)
        citation_format = r"\[Source:\s*([^,]+?)\s*,\s*Page:\s*(\d+)\s*,\s*Lines:\s*(\d+\s*-\s*\d+)\s*,\s*Start:?\s*(\d+)\]"
        assert re.search(citation_format, text) is not None
