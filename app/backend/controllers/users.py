from app.backend.models.users import get_user_last_chat, find_user_by_id, add_new_user, User
from fastapi import Response, Request, HTTPException
from app.settings import settings, logger, BASE_DIR
from datetime import datetime, timedelta, timezone
from app.backend.models.chats import Chat
from uuid import uuid4
import asyncio
import shutil
import jwt
import os


async def remove_user(user_id: str) -> None:
    loop = asyncio.get_event_loop()
    path = os.path.join(BASE_DIR, "chats_storage", f"user_id={user_id}")
    try:
        loop.run_in_executor(None, shutil.rmtree, path)
    except Exception as e:
        await logger.error(f"Error at remove_user: {e}")


async def extract_user_from_context(request: Request) -> User | None:
    if hasattr(request.state, "current_user"):
        return request.state.current_user

    if settings.debug:
        await logger.info("No attribute 'current_user'")

    return None


async def create_access_token(user_id: str, expires_delta: timedelta = settings.max_cookie_lifetime) -> str:
    token_payload = {"user_id": user_id}
    token_payload.update({"exp": datetime.now() + expires_delta})
    loop = asyncio.get_event_loop()

    try:
        encoded_jwt: str = await loop.run_in_executor(
            None,
            jwt.encode,
            token_payload,
            settings.secret_pepper,
            settings.jwt_algorithm
        )
    except Exception:
        raise HTTPException(status_code=500, detail="json encoding error")

    if settings.debug:
        await logger.info(f"New JWT token - {encoded_jwt}")

    return encoded_jwt


async def create_user() -> User | None:
    new_user_id = str(uuid4())
    try:
        user = await add_new_user(id=new_user_id)
    except Exception as e:
        raise HTTPException(status_code=418, detail=e)

    if settings.debug:
        await logger.info(f"Created user - {user.id}")

    return user


async def authorize_user(response: Response, user: User) -> dict:
    if settings.debug:
        await logger.info("START Authorizing User")
    try:
        access_token: str = await create_access_token(user_id=user.id)
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
    except jwt.ExpiredSignatureError:
        await remove_user(user.id)
    finally:
        if settings.debug:
            await logger.info("END Authorizing User")


async def get_current_user(request: Request) -> User | None:
    if settings.debug:
        await logger.info("START Getting User")

    loop = asyncio.get_event_loop()
    try:
        user = None
        token: str | None = request.cookies.get("access_token")

        if settings.debug:
            await logger.info(f"Token -----> {token if token else 'Empty token!'}")

        if not token:
            return None

        try:
            token_data = await loop.run_in_executor(
                None,
                jwt.decode,
                bytes(token, encoding="utf-8"),
                settings.secret_pepper,
                [settings.jwt_algorithm],
            )
            user_id = token_data.get("user_id")

            if settings.debug:
                await logger.info(f"User id -----> {user_id if user_id else 'Empty user id!'}")

            user = await find_user_by_id(id=user_id)

            if settings.debug:
                await logger.info(f"Found user -----> {user.id if user else 'No user was found!'}")
        except Exception as e:
            raise e

        if not user:
            return None

        return user
    except HTTPException as exception:
        raise exception
    finally:
        if settings.debug:
            await logger.info("END Getting User")


async def check_cookie(request: Request) -> dict:
    result = {"token": "No token is present"}
    token = request.cookies.get("access_token")
    if token:
        result["token"] = token
    return result


async def clear_cookie(response: Response) -> dict:
    response.set_cookie(key="access_token", value="", httponly=True)
    return {"status": "ok"}


async def get_latest_chat(user: User) -> Chat | None:
    return await get_user_last_chat(user)


async def refresh_cookie(request: Request, response: Response) -> None:
    if settings.debug:
        await logger.info("START Refreshing cookie")

    loop = asyncio.get_event_loop()
    try:

        token: str | None = request.cookies.get("access_token")

        if settings.debug:
            await logger.info(f"Token -----> {token if token else 'Empty token!'}")

        if token is None:
            return

        try:
            jwt_token = await loop.run_in_executor(
                None,
                jwt.decode,
                bytes(token, encoding="utf-8"),
                settings.secret_pepper,
                [settings.jwt_algorithm],
            )

            exp_datetime = datetime.fromtimestamp(jwt_token.get("exp"), tz=timezone.utc)

            if settings.debug:
                await logger.info(f"Expires -----> {exp_datetime if exp_datetime else 'No expiration date!'}")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="jwt signature has expired")
        except jwt.PyJWTError as e:
            raise HTTPException(status_code=500, detail=e)

        diff = exp_datetime - datetime.now(timezone.utc)

        if settings.debug:
            await logger.info(f"Difference -----> {diff if diff else 'No difference in date!'}")

        if diff.total_seconds() < 0.2 * settings.max_cookie_lifetime.total_seconds():

            if settings.debug:
                await logger.info("Refreshing")

            user = await extract_user_from_context(request)
            await authorize_user(response, user)
    except HTTPException as exception:
        raise exception
    finally:
        if settings.debug:
            await logger.info("END Refreshing cookie")
