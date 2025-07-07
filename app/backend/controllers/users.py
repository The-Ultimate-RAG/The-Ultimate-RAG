from app.backend.models.users import (
    User,
    add_new_user,
    find_user_by_email,
    find_user_by_access_string,
    update_user,
    get_user_last_chat,
)
from app.backend.models.chats import Chat
from bcrypt import gensalt, hashpw, checkpw
from app.settings import settings
from fastapi import HTTPException
import jwt
from datetime import datetime, timedelta
from fastapi import Response, Request
from secrets import token_urlsafe
import hmac
import hashlib

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
    access_string: str, expires_delta: timedelta = settings.max_cookie_lifetime
) -> str:
    token_payload = {
        "access_string": access_string,
    }

    token_payload.update({"exp": datetime.now() + expires_delta})
    encoded_jwt: str = jwt.encode(
        token_payload, settings.secret_pepper, algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


"""
Safely creates random string of 16 chars
"""


def create_access_string() -> str:
    return token_urlsafe(16)


"""
Hashes access string using hmac and sha256

We can not use the same methods as we do to save password
since we need to know a salt to get similar hash, but since
we put a raw string (non-hashed) we won't be able to guess
salt
"""


def hash_access_string(string: str) -> str:
    return hmac.new(
        key=str(settings.secret_pepper).encode("utf-8"),
        msg=string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


"""
Creates a new user and sets a cookie with jwt token

Params:
response - needed to set a cookie
...

Returns:
Dict to send a response in JSON
"""


def create_user(response: Response, email: str, password: str) -> dict:
    user: User = find_user_by_email(email=email)
    if user is not None:
        return HTTPException(418, "The user with similar email already exists")

    salt: bytes = gensalt(rounds=16)
    password_hashed: str = hashpw(password.encode("utf-8"), salt).decode("utf-8")

    access_string: str = create_access_string()
    access_string_hashed: str = hash_access_string(string=access_string)

    id = add_new_user(
        email=email,
        password_hash=password_hashed,
        access_string_hash=access_string_hashed,
    )

    print(id)

    access_token: str = create_access_token(access_string=access_string)
    response.set_cookie(
        key="access_token",
        value=access_token,
        path="/",
        max_age=settings.max_cookie_lifetime,
        httponly=True,
    )

    return {"status": "ok", "id": id if id is not None else 0}


"""
Finds user by email. If user is found, sets a cookie with token
"""


def authenticate_user(response: Response, email: str, password: str) -> dict:
    user: User = find_user_by_email(email=email)

    if not user:
        raise HTTPException(418, "User does not exists")

    if not checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        raise HTTPException(418, "Wrong credentials")

    access_string: str = create_access_string()
    access_string_hashed: str = hash_access_string(string=access_string)

    update_user(user, access_string_hash=access_string_hashed)

    access_token = create_access_token(access_string)
    response.set_cookie(
        key="access_token",
        value=access_token,
        path="/",
        max_age=settings.max_cookie_lifetime,
        httponly=True,
    )

    return {"status": "ok"}


"""
Get user from token stored in cookies
"""


def get_current_user(request: Request) -> User | None:
    user = None
    token: str | None = request.cookies.get("access_token")
    if not token:
        return None

    try:
        access_string = jwt.decode(
            jwt=bytes(token, encoding="utf-8"),
            key=settings.secret_pepper,
            algorithms=[settings.jwt_algorithm],
        ).get("access_string")

        user = find_user_by_access_string(hash_access_string(access_string))
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
