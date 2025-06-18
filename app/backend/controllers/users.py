from app.backend.models.users import User, add_new_user, find_user_by_email
from bcrypt import gensalt, hashpw, checkpw
from app.settings import very_secret_pepper, jwt_algorithm
from fastapi import HTTPException
import jwt
from datetime import datetime, timedelta
from fastapi import Response, Request
from fastapi.responses import JSONResponse

def create_access_token(email: str, expires_delta: timedelta | None = None):
    token_payload = {
        "email":  email,
    }

    if expires_delta:
        expires = expires_delta
    else:
        expires = datetime.now() + timedelta(minutes=5)

    token_payload.update({"exp": expires})
    encoded_jwt = jwt.encode(token_payload, very_secret_pepper, algorithm=jwt_algorithm)

    return encoded_jwt
        

def create_user(response: Response, email: str, password: str):

    user: User = find_user_by_email(email=email)
    if user is not None:
        print("-"*100)
        return HTTPException(418, "The user with similar email already exists")
    
    salt = gensalt(rounds=16)
    password_hashed = hashpw(password.encode("utf-8"), salt).decode("utf-8")

    add_new_user(email=email, password_hash=password_hashed)

    access_token = create_access_token(email)
    response.set_cookie(key="access_token", value=access_token, path='/', max_age=300, httponly=True)

    return JSONResponse({"status": "ok"})


def authenticate_user(response: Response, email: str, password: str):
    user: User = find_user_by_email(email=email)
    print(user)
    if not user:
        return HTTPException(418, "User does not exists")
    
    print(123)
    if not checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return HTTPException(418, "Wrong credentials")
    print(123)

    access_token = create_access_token(email)
    print(access_token)
    response.set_cookie(key="access_token", value=access_token, path='/', max_age=300, httponly=True)

    return {"status": "ok"}


def check_cookie(request: Request):
    token = request.cookies.get("access_token")
    print(request.cookies)
    print(token)
    user_email = jwt.decode(
            jwt=bytes(token, encoding='utf-8'),
            key=very_secret_pepper,
            algorithms=['HS256']
        ).get('email')

    user = find_user_by_email(user_email)

    return {"user" : {"email": user.email, "id": user.id, "password": user.password_hash}}



    


