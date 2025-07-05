from app.backend.models.chats import Chat
from app.settings import settings
from app.backend.models.users import (
    get_user_last_chat,
    find_user_by_id,
    add_new_user,
    User,
)

from fastapi import Response, Request, HTTPException
from datetime import datetime, timedelta, timezone

from uuid import uuid4
import jwt


def extract_user_from_context(request: Request) -> User | None:
    if hasattr(request.state, "current_user"):
        return request.state.current_user
    print("*" * 40, "No attribute 'current_user`", "*" * 40, "\n")
    return None


def create_access_token(user_id: str, expires_delta: timedelta = settings.max_cookie_lifetime) -> str:
    token_payload = {"user_id": user_id,}
    token_payload.update({"exp": datetime.now() + expires_delta})

    try:
        encoded_jwt: str = jwt.encode(
            token_payload, settings.secret_pepper, algorithm=settings.jwt_algorithm
        )
    except Exception:
        raise HTTPException(status_code=500, detail="json encoding error")

    print("^" * 40, "New JWT token was created", "^" * 40)
    print(encoded_jwt)
    print("^" * 105, "\n\n")

    return encoded_jwt


def create_user() -> User | None:
    new_user_id = str(uuid4())
    try:
        user = add_new_user(id=new_user_id)
    except Exception as e:
        raise HTTPException(status_code=418, detail=e)

    print("$" * 40, "New User was created", "$" * 40)
    print("Created user - {user.id}")
    print("$" * 100, "\n\n")

    return user


def authorize_user(response: Response, user: User) -> dict:
    print("%" * 40, "START Authorizing User", "%" * 40)
    try:
        access_token: str = create_access_token(user_id=user.id)
        expires = datetime.now(timezone.utc) + settings.max_cookie_lifetime

        response.set_cookie(
            key="access_token",
            value=access_token,
            path="/",
            expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            max_age=settings.max_cookie_lifetime,
            httponly=True,
            # secure=True,
            samesite='lax'
        )

        return {"status": "ok"}
    finally:
        print("%" * 40, "END Authorizing User", "%" * 40)


def get_current_user(request: Request) -> User | None:
    print("-" * 40, "START Getting User", "-" * 40)
    try:
        user = None
        token: str | None = request.cookies.get("access_token")

        print(f"Token -----> {token if token else 'Empty token!'}\n")

        if not token:
            return None

        try:
            user_id = jwt.decode(
                jwt=bytes(token, encoding="utf-8"),
                key=settings.secret_pepper,
                algorithms=[settings.jwt_algorithm],
            ).get("user_id")

            print(f"User id -----> {user_id if user_id else 'Empty user id!'}\n")

            user = find_user_by_id(id=user_id)

            print(f"Found user -----> {user.id if user else 'No user was found!'}")
        except Exception as e:
            raise e

        if not user:
            return None

        return user
    except HTTPException as exception:
        raise exception
    finally:
        print("-" * 40, "END Getting User", "-" * 40, "\n\n")


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


def refresh_cookie(request: Request, response: Response) -> None:
    print("+" * 40, "START Refreshing cookie", "+" * 40)
    try:
        token: str | None = request.cookies.get("access_token")

        print(f"Token -----> {token if token else 'Empty token!'}\n")

        if token is None:
            return

        try:
            jwt_token = jwt.decode(
                        jwt=bytes(token, encoding="utf-8"),
                        key=settings.secret_pepper,
                        algorithms=[settings.jwt_algorithm],
                    )
            exp_datetime = datetime.fromtimestamp(jwt_token.get("exp"), tz=timezone.utc)
            print(f"Expires -----> {exp_datetime if exp_datetime else 'No expiration date!'}\n")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="jwt signature has expired")
        except jwt.PyJWTError as e:
            raise HTTPException(status_code=500, detail=e)

        diff = exp_datetime - datetime.now(timezone.utc)
        print(f"Difference -----> {diff if diff else 'No difference in date!'}\n")

        if diff.total_seconds()  < 0.2 * settings.max_cookie_lifetime.total_seconds():
            print("<----- Refreshing ----->")
            user = extract_user_from_context(request)
            authorize_user(response, user)
    except HTTPException as exception:
        raise exception
    finally:
        print("+" * 40, "END Refreshing cookie", "+" * 40, "\n\n")
