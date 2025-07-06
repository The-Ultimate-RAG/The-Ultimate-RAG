import pytest
from unittest.mock import MagicMock
from app.backend.schemas import SUser
from app.core.utils import construct_collection_name, get_pdf_path, lines_to_markdown, protect_chat, extend_context
from app.backend.models.users import User


# Tests for SUser schema (app/backend/schemas)

# Tests password validation fails when no digit is present.
def test_password_no_digit():
    with pytest.raises(ValueError, match="Password must contain at least one number."):
        SUser(email="test@example.ru", password="NoDi@gitPassword!")


# Tests password validation fails when password is too short (<8 characters).
def test_password_too_short():
    with pytest.raises(ValueError, match="String should have at least 8 characters"):
        SUser(email="test@example.ru", password="P1@Sal!")


# Tests password validation fails when password is too long (>32 characters).
def test_password_too_long():
    with pytest.raises(ValueError, match="String should have at most 32 characters"):
        SUser(
            email="test@example.ru",
            password="Strong.Password123!Strong.Password123!Strong.Password123!Strong.Password123!Strong.Passwor",
        )


# Tests email validation fails when email format is invalid.
def test_email():
    with pytest.raises(ValueError, match="value is not a valid email address"):
        SUser(email="test.test", password="SoMeGrE@tPa22WoRd!")


# Tests successful creation of SUser with valid email and password.
def test_valid_password():
    user = SUser(email="test@example.ru", password="Strong.Password123!")
    assert user.email == "test@example.ru"
    assert user.password == "Strong.Password123!"


# Tests for app/core/utils

# Tests that construct_collection_name formats user ID and chat ID correctly.
def test_construct_collection_name():
    user = User(id=1)
    chat_id = 2
    result = construct_collection_name(user, chat_id)
    expected = "user_id_1_chat_id_2"
    assert result == expected


# Tests get_pdf_path extracts correct path segment or returns empty string.
def test_get_pdf_path():
    # Case 1: Path contains "chats_storage"
    path_with = "/app/chats_storage/user_id=1/chat_id=2/documents/file.pdf"
    expected_with = "chats_storage/user_id=1/chat_id=2/documents/file.pdf"
    assert get_pdf_path(path_with) == expected_with

    # Case 2: Path does not contain "chats_storage"
    path_without = "/app/some_other_path/file.pdf"
    assert get_pdf_path(path_without) == ""


# Tests lines_to_markdown converts text lines to HTML correctly.
def test_lines_to_markdown():
    lines = ["Hello **world**", "Another line"]
    result = lines_to_markdown(lines)
    assert len(result) == 2
    assert "<strong>world</strong>" in result[0]  # Check bold formatting
    assert "Another line" in result[1]  # Check plain text conversion


# Tests protect_chat verifies user ownership of a chat correctly.
def test_protect_chat(monkeypatch):
    mock_user = User(id=1)
    chat_id = 2

    # Case 1: User owns the chat
    monkeypatch.setattr("app.core.utils.verify_ownership_rights", lambda user, cid: True)
    assert protect_chat(mock_user, chat_id) == 1

    # Case 2: User does not own the chat
    monkeypatch.setattr("app.core.utils.verify_ownership_rights", lambda user, cid: False)
    assert protect_chat(mock_user, chat_id) == 0


# Tests extend_context adds correct navbar, sidebar, and footer data.
def test_extend_context(monkeypatch):
    mock_request = MagicMock()

    # Case 1: With an authenticated user
    mock_user = User(id=1)
    monkeypatch.setattr("app.core.utils.get_current_user", lambda req: mock_user)
    monkeypatch.setattr("app.core.utils.list_user_chats", lambda uid: [{"id": 1, "name": "Chat1"}])
    context_with_user = {"request": mock_request}
    result_with_user = extend_context(context_with_user)
    assert result_with_user["navbar_context"]["user"]["role"] == "user"
    assert result_with_user["navbar_context"]["user"]["instance"] == mock_user
    assert result_with_user["sidebar_context"]["chat_groups"] == [{"id": 1, "name": "Chat1"}]

    # Case 2: Without a user (guest)
    monkeypatch.setattr("app.core.utils.get_current_user", lambda req: None)
    context_without_user = {"request": mock_request}
    result_without_user = extend_context(context_without_user)
    assert result_without_user["navbar_context"]["user"]["role"] == "guest"
    assert result_without_user["navbar_context"]["user"]["instance"] is None
    assert result_without_user["sidebar_context"]["chat_groups"] == []
