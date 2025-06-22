from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Response, Request, Depends
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.backend.controllers.users import create_user, authenticate_user, check_cookie, clear_cookie, get_current_user, get_latest_chat
from app.backend.controllers.chats import create_new_chat, get_chat_with_messages
from app.backend.controllers.messages import register_message
from app.backend.controllers.schemas import SUser
from app.backend.models.users import User

from app.utils import TextHandler, PDFHandler, protect_chat, extend_context, initialize_rag, save_documents
from app.settings import base_path, url_user_not_required
from app.document_validator import path_is_valid
from app.response_parser import add_links

from typing import Optional
import os

# TODO: implement a better TextHandler
# TODO: optionally implement DocHandler

api = FastAPI()

api.mount("/pdfs", StaticFiles(directory=os.path.join(base_path, "temp_storage", "pdfs")), name="pdfs")
api.mount("/static", StaticFiles(directory=os.path.join(base_path, "frontend", "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(base_path, "frontend", "templates"))


# NOTE: carefully read documentation to require_user
# <--------------------------------- Middleware --------------------------------->
'''
Special class to have an opportunity to redirect user to login page in middleware
'''
class AwaitableResponse:
    def __init__(self, response: Response):
        self.response = response

    def __await__(self):
        yield
        return self.response


'''
TODO: remove KOSTYLY -> find better way to skip requesting to login while showing pdf

Middleware that requires user to log in into the system before accessing any utl

NOTE: For now it is applied to all routes, but if you want to skip any, add it to the
url_user_not_required list in settings.py (/ should be removed)
'''
@api.middleware("http")
async def require_user(request: Request, call_next):
    print(request.url.path, request.method)

    awaitable_response = AwaitableResponse(RedirectResponse("/login", status_code=303))
    stripped_path = request.url.path.strip('/')

    if stripped_path in url_user_not_required \
        or stripped_path.startswith("pdfs") \
        or "static/styles.css" in stripped_path \
        or "favicon.ico" in stripped_path:
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
    return templates.TemplateResponse(current_template, extend_context({"request": request}))


@api.post("/message_with_docs")
async def send_message(request: Request, files: list[UploadFile] = File(None), prompt: str = Form(...), chat_id = Form(None)):
    rag = initialize_rag()
    response = ""

    try:
        register_message(content=prompt, sender="user", chat_id=int(chat_id))
        
        await save_documents(files=files, RAG=rag)

        response_raw = rag.generate_response(user_prompt=prompt)
        response = add_links(response_raw)

        register_message(content=response, sender="assistant", chat_id=int(chat_id))

    except Exception as e:
        print(e)

    return {"response": response, "status": 200}


@api.get("/viewer")
def show_document(request: Request, path: str, page: Optional[int] = 1, lines: Optional[str] = "1-1", start: Optional[int] = 0):
    if not path_is_valid(path):
        return HTTPException(status_code=404, detail="Document not found")

    ext = path.split(".")[-1]
    if ext == 'pdf':
        return PDFHandler(request, path=path, page=page, templates=templates)
    elif ext in ('txt', 'csv', 'md'):
        return TextHandler(request, path=path, lines=lines, templates=templates)
    elif ext in ('docx', 'doc'):
        return TextHandler(request, path=path, lines=lines, templates=templates)  # should be a bit different handler
    else:
        return FileResponse(path=path)


# <--------------------------------- Get --------------------------------->
@api.get("/new_user")
def new_user(request: Request):
    current_template = "pages/registration.html"
    return templates.TemplateResponse(current_template, extend_context({"request": request}))


@api.get("/login")
def login(request: Request):
    current_template = "pages/login.html"
    return templates.TemplateResponse(current_template, extend_context({"request": request}))


@api.get("/cookie_test")
def test_cookie(request: Request):
    return check_cookie(request)


'''
Use only for testing. For now, provides user info for logged ones, and redirects to
login in other case
'''
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


@api.get("/chats/id={chat_id}")
def show_chat(request: Request, chat_id: int):
    current_template = "pages/chat.html"

    chat = get_chat_with_messages(chat_id)
    user = get_current_user(request)

    if not protect_chat(user, chat_id):
        raise HTTPException(401, "Yod do not have rights to use this chat!")

    context = extend_context({
        "request": request, 
        "user": user
        })
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
        url = create_new_chat("new chat", user)
    else:
        url = f"/chats/id={chat.id}"

    return RedirectResponse(url, status_code=303)


# <--------------------------------- Post --------------------------------->
@api.post("/new_user")
def new_user(response: Response, user: SUser):
    return create_user(response, user.email, user.password)


@api.post("/login")
def login(response: Response, user: SUser):
    return authenticate_user(response, user.email, user.password)


@api.post("/new_chat")
def create_chat(request: Request, title: Optional[str] = "new chat", user: User = Depends(get_current_user)):
    url = create_new_chat(title, user)
    return RedirectResponse(url, status_code=303)
