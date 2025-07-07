from fastapi import (
    FastAPI,
    UploadFile,
    Form,
    File,
    HTTPException,
    Response,
    Request,
    Depends,
)
from fastapi.responses import (
    FileResponse,
    RedirectResponse,
    StreamingResponse,
    JSONResponse,
)
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.backend.controllers.users import (
    create_user,
    authenticate_user,
    check_cookie,
    clear_cookie,
    get_current_user,
    get_latest_chat,
)
from app.backend.controllers.chats import (
    create_new_chat,
    get_chat_with_messages,
    update_title,
)
from app.backend.controllers.messages import register_message
from app.backend.schemas import SUser
from app.backend.models.users import User

from app.core.utils import (
    TextHandler,
    PDFHandler,
    protect_chat,
    extend_context,
    initialize_rag,
    save_documents,
    construct_collection_name,
    create_collection,
)
from app.settings import BASE_DIR, url_user_not_required
from app.core.document_validator import path_is_valid
from app.core.response_parser import add_links
from typing import Optional
import os

# TODO: implement a better TextHandler
# TODO: optionally implement DocHandler

api = FastAPI()

api.mount(
    "/chats_storage",
    StaticFiles(directory=os.path.join(BASE_DIR, "chats_storage")),
    name="chats_storage",
)
api.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "app", "frontend", "static")),
    name="static",
)
templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "app", "frontend", "templates")
)
rag = initialize_rag()

# NOTE: carefully read documentation to require_user
# <--------------------------------- Middleware --------------------------------->
"""
Special class to have an opportunity to redirect user to login page in middleware
"""


class AwaitableResponse:
    def __init__(self, response: Response):
        self.response = response

    def __await__(self):
        yield
        return self.response


"""
TODO: remove KOSTYLY -> find better way to skip requesting to login while showing pdf

Middleware that requires user to log in into the system before accessing any utl

NOTE: For now it is applied to all routes, but if you want to skip any, add it to the
url_user_not_required list in settings.py (/ should be removed)
"""


@api.middleware("http")
async def require_user(request: Request, call_next):
    print(request.url.path, request.method, request.url.port)

    awaitable_response = AwaitableResponse(RedirectResponse("/login", status_code=303))
    stripped_path = request.url.path.strip("/")

    if (
        stripped_path in url_user_not_required
        or stripped_path.startswith("pdfs")
        or "static/styles.css" in stripped_path
        or "favicon.ico" in stripped_path
    ):
        return await call_next(request)

    user = get_current_user(request)
    if user is None:
        return await awaitable_response

    response = await call_next(request)
    return response


# <--------------------------------- Common routes --------------------------------->
@api.get("/")
def root(request: Request):
    current_template = "pages/main.html"
    return templates.TemplateResponse(
        current_template, extend_context({"request": request})
    )


@api.post("/message_with_docs")
async def send_message(
    request: Request,
    files: list[UploadFile] = File(None),
    prompt: str = Form(...),
    chat_id=Form(None),
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    # response = ""
    status = 200
    try:
        collection_name = construct_collection_name(user, chat_id)

        register_message(content=prompt, sender="user", chat_id=int(chat_id))

        await save_documents(
            collection_name, files=files, RAG=rag, user=user, chat_id=chat_id
        )

        # response = rag.generate_response_stream(collection_name=collection_name, user_prompt=prompt, stream=True)
        # async def stream_response():
        #     async for chunk in response:
        #         yield chunk.json()

        return StreamingResponse(
            rag.generate_response_stream(
                collection_name=collection_name, user_prompt=prompt, stream=True
            ),
            status,
            media_type="text/event-stream",
        )
    except Exception as e:
        status = 500
        print(e)


@api.post("/replace_message")
async def replace_message(request: Request):
    data = await request.json()
    updated_message = add_links(data.get("message", ""))
    register_message(
        content=updated_message, sender="assistant", chat_id=int(data.get("chat_id", 0))
    )
    return JSONResponse({"updated_message": updated_message})


@api.get("/viewer")
def show_document(
    request: Request,
    path: str,
    page: Optional[int] = 1,
    lines: Optional[str] = "1-1",
    start: Optional[int] = 0,
):
    if not path_is_valid(path):
        return HTTPException(status_code=404, detail="Document not found")

    ext = path.split(".")[-1]
    if ext == "pdf":
        return PDFHandler(request, path=path, page=page, templates=templates)
    elif ext in ("txt", "csv", "md", "json"):
        return TextHandler(request, path=path, lines=lines, templates=templates)
    elif ext in ("docx", "doc"):
        return TextHandler(
            request, path=path, lines=lines, templates=templates
        )  # should be a bit different handler
    else:
        return FileResponse(path=path)


# <--------------------------------- Get --------------------------------->
@api.get("/new_user")
def new_user_post(request: Request):
    current_template = "pages/registration.html"
    return templates.TemplateResponse(
        current_template, extend_context({"request": request})
    )


@api.get("/login")
def login_get(request: Request):
    current_template = "pages/login.html"
    return templates.TemplateResponse(
        current_template, extend_context({"request": request})
    )


@api.get("/cookie_test")
def test_cookie(request: Request):
    return check_cookie(request)


"""
Use only for testing. For now, provides user info for logged ones, and redirects to
login in other case
"""


@api.get("/test")
def test(request: Request, user: User = Depends(get_current_user)):
    return {
        "user": {
            "email": user.email,
            "password_hash": user.password_hash,
            # "chats": user.chats, # Note: it will rise error since due to the optimization associated fields are not loaded
            # it is just a reference, but the session is closed, however you are trying to get access to the data through this session
        }
    }

@api.post("/chats/id={chat_id}/history")
def show_chat_history(request: Request, chat_id: int):
    chat = get_chat_with_messages(chat_id)
    user = get_current_user(request)

    update_title(chat["chat_id"])

    if not protect_chat(user, chat_id):
        raise HTTPException(401, "Yod do not have rights to use this chat!")

    context = chat

    return context

@api.get("/chats/id={chat_id}")
def show_chat(request: Request, chat_id: int):
    current_template = "pages/chat.html"

    chat = get_chat_with_messages(chat_id)
    user = get_current_user(request)

    update_title(chat["chat_id"])

    if not protect_chat(user, chat_id):
        raise HTTPException(401, "Yod do not have rights to use this chat!")

    context = extend_context({"request": request, "user": user}, selected=chat_id)
    context.update(chat)

    return templates.TemplateResponse(current_template, context)


@api.get("/logout")
def logout(response: Response):
    return clear_cookie(response)


@api.get("/last_user_chat")
def last_user_chat(request: Request, user: User = Depends(get_current_user)):
    chat = get_latest_chat(user)
    url = None

    if chat is None:
        print("new_chat")
        new_chat = create_new_chat("new chat", user)
        url = new_chat.get("url")

        try:
            create_collection(user, new_chat.get("chat_id"), rag)
        except Exception as e:
            raise HTTPException(500, e)

    else:
        url = f"/chats/id={chat.id}"

    return RedirectResponse(url, status_code=303)


# <--------------------------------- Post --------------------------------->
@api.post("/new_user")
def new_user(response: Response, user: SUser):
    return create_user(response, user.email, user.password)


# TODO: remove admin validation as troubleshooting ends


class LoginData(BaseModel):
    email: str
    password: str


@api.post("/login")
def login_post(response: Response, user_data: LoginData):
    try:
        # Validate the user data against the SUser schema for regular users
        # This enforces email format and password complexity for non-admins
        user_schema = SUser(email=user_data.email, password=user_data.password)
    except ValueError as e:
        # If validation fails, return a detailed error
        raise HTTPException(status_code=422, detail=f"Validation error: {e}")

    # If validation passes, proceed with the standard authentication process
    return authenticate_user(response, user_schema.email, user_schema.password)


@api.post("/new_chat")
def create_chat(
    request: Request,
    title: Optional[str] = "new chat",
    user: User = Depends(get_current_user),
):
    new_chat = create_new_chat(title, user)
    url = new_chat.get("url")
    chat_id = new_chat.get("chat_id")

    if url is None or chat_id is None:
        raise HTTPException(500, "New chat was not created")

    try:
        create_collection(user, chat_id, rag)
    except Exception as e:
        raise HTTPException(500, e)

    return RedirectResponse(url, status_code=303)


if __name__ == "__main__":
    pass
