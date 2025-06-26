import hashlib
import hmac
from secrets import token_urlsafe
import jwt
from datetime import datetime, timedelta
import bcrypt
from app.settings import settings


def create_access_token(access_string: str, expires_delta: timedelta = settings.max_cookie_lifetime) -> str:
    token_payload = {
        "access_string": access_string,
    }

    token_payload.update({"exp": datetime.now() + expires_delta})
    encoded_jwt: str = jwt.encode(token_payload, settings.secret_pepper.get_secret_value(),
                                  algorithm=settings.jwt_algorithm)

    return encoded_jwt


def create_access_string() -> str:
    return token_urlsafe(16)


def hash_access_string(string: str) -> str:
    return hmac.new(
        key=settings.secret_pepper.encode(),
        msg=string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()


def verify_access_string_hash(plain_string: str, hashed_string: str) -> bool:
    return hmac.compare_digest(hash_access_string(plain_string), hashed_string)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
