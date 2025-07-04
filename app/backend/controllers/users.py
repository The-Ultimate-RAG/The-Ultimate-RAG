from app.backend.models.users import (
    User,
    add_new_user,
    get_user_last_chat,
    find_user_by_id
)
from app.backend.models.chats import Chat
from app.settings import settings
import jwt
from datetime import datetime, timedelta
from fastapi import Response, Request
from uuid import uuid4

# A vot nado bilo izuchat kak web dev rabotaet

"""
Creates a jwt token by access string

Param:
access_string - randomly (safe methods) generated string (by default - 16 len)
expires_delta - time in seconds, defines a token lifetime

Returns:
string with 4 sections (valid jwt token)
"""


def create_access_token(
    user_id: str, expires_delta: timedelta = settings.max_cookie_lifetime
) -> str:
    token_payload = {
        "user_id": user_id,
    }

    token_payload.update({"exp": datetime.now() + expires_delta})
    encoded_jwt: str = jwt.encode(
        token_payload, settings.secret_pepper, algorithm=settings.jwt_algorithm
    )

    return encoded_jwt

"""
Hashes access string using hmac and sha256

We can not use the same methods as we do to save password
since we need to know a salt to get similar hash, but since
we put a raw string (non-hashed) we won't be able to guess
salt
"""


"""
Creates a new user and sets a cookie with jwt token

Params:
response - needed to set a cookie
...

Returns:
Dict to send a response in JSON
"""


def create_user(response: Response) -> dict:

    new_user_id = str(uuid4())

    add_new_user(
        id=new_user_id
    )

    access_token: str = create_access_token(user_id=new_user_id)
    response.set_cookie(
        key="access_token",
        value=access_token,
        path="/",
        max_age=settings.max_cookie_lifetime,
        httponly=True,
        # secure=True,
        samesite='lax'
    )

    return {"status": "ok"}



"""
Get user from token stored in cookies
"""


def get_current_user(request: Request) -> User | None:
    print("------------------------------------------------------------")
    user = None
    token: str | None = request.cookies.get("access_token")
    if not token:
        return None

    try:
        user_id = jwt.decode(
            jwt=bytes(token, encoding="utf-8"),
            key=settings.secret_pepper,
            algorithms=[settings.jwt_algorithm],
        ).get("user_id")
        user = find_user_by_id(id=user_id)
        print(user if user is not None else '!' * 100)
    except Exception as e:
        print(e)

    if not user:
        return None

    return user


"""
Checks if cookie with access token is present
"""


def check_cookie(request: Request) -> dict:
    result = {"token": "No token is present"}
    token = request.cookies.get("access_token")
    if token:
        result["token"] = token
    return result


def clear_cookie(response: Response) -> dict:
    response.set_cookie(key="access_token", value="", httponly=True)
    return {"status": "ok"}


def get_latest_chat(user: User) -> Chat | None:
    return get_user_last_chat(user)
