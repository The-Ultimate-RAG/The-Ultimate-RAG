import pytest
from app.backend.controllers.schemas import SUser


def test_password_no_digit():
    with pytest.raises(ValueError, match="Password must contain at least one number."):
        SUser(email="test@example.ru", password="NoDi@gitPassword!")


def test_password_too_short():
    with pytest.raises(ValueError, match="String should have at least 8 characters"):
        SUser(email="test@example.ru", password="P1@Sal!")


def test_password_too_long():
    with pytest.raises(ValueError, match="String should have at most 32 characters"):
        SUser(
            email="test@example.ru",
            password="Strong.Password123!Strong.Password123!Strong.Password123!Strong.Password123!Strong.Passwor",
        )


def test_email():
    with pytest.raises(ValueError, match="value is not a valid email address"):
        SUser(email="test.test", password="SoMeGrE@tPa22WoRd!")


def test_valid_password():
    user = SUser(email="test@example.ru", password="Strong.Password123!")
    assert user.email == "test@example.ru"
    assert user.password == "Strong.Password123!"
