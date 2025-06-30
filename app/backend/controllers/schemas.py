import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class SUser(BaseModel):
    email: EmailStr
    password: str = Field(default=..., min_length=8, max_length=32)

    @field_validator("password", mode="before")
    def validate_password(cls, password_to_validate):
        """
        Validates the strength of the password.

        The password **must** contain:
            - At least one digit
            - At least one special character
            - At least one uppercase character
            - At least one lowercase character
        """

        if not re.search(r"\d", password_to_validate):
            raise ValueError("Password must contain at least one number.")

        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};:\'\",.<>?`~]", password_to_validate):
            raise ValueError("Password must contain at least one special symbol.")

        if not re.search(r"[A-Z]", password_to_validate):
            raise ValueError("Password must contain at least one uppercase letter.")

        if not re.search(r"[a-z]", password_to_validate):
            raise ValueError("Password must contain at least one lowercase letter.")

        return password_to_validate
