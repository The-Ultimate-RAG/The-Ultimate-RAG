from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Response, Request, Depends
import uuid
from app.backend.models.users import User
from fastapi.staticfiles import StaticFiles
import os
from app.rag_generator import RagSystem
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from app.settings import base_path, url_user_not_required
from typing import Optional
from app.response_parser import add_links
from app.document_validator import path_is_valid
from app.backend.controllers.users import create_user, authenticate_user, check_cookie, clear_cookie, get_current_user
from app.backend.controllers.schemas import SUser
from app.backend.controllers.chats import create_new_chat

# TODO: implement a better TextHandler
# TODO: optionally implement DocHandler

api = FastAPI()
rag = None
api.mount("/pdfs", StaticFiles(directory=os.path.join(base_path, "temp_storage", "pdfs")), name="pdfs")


def initialize_rag() -> RagSystem:
    global rag
    if rag is None:
        rag = RagSystem()
    return rag


def PDFHandler(path: str, page: int) -> HTMLResponse:
    template = ""
    with open(os.path.join(base_path, "frontend", "templates", "show_pdf.html"), "r") as f:
        template = f.read()

    filename = os.path.basename(path)
    url_path = f"/pdfs/{filename}"

    template = template.replace("PAGE", str(page or 1)).replace("PATH", url_path)

    return HTMLResponse(content=template)


def TextHandler(path: str, lines: str) -> HTMLResponse:
    text = ""
    with open(os.path.join(base_path, "frontend", "templates", "show_text.html"), "r") as f:
        text = f.read()

    file_content = ""
    with open(path, "r") as f:
        file_content = f.read()

    start_line, end_line = map(int, lines.split('-'))

    content = []
    anchor_added = False
    for index, line in enumerate(file_content.split('\n')):
        if start_line <= index + 1 <= end_line:
            if not anchor_added:
                anchor_added = True
                content.append("<a name='anchor'></a>")
            content.append(f'<span style="background-color: green;">{ line }</span>')
        else:
            content.append(line)

    text = text.replace("CONTENT", "<pre>" + '\n'.join(content) + "</pre>")
    
    return HTMLResponse(content=text)


'''
Optional handler
'''
def DocHandler():
    pass


# <--------------------------------- Middleware --------------------------------->
# NOTE: to avoid infinite redirects add main routs to this list

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

    if stripped_path in url_user_not_required or stripped_path.startswith("pdfs"):
        return await call_next(request)

    user = get_current_user(request)
    if user is None:
        return await awaitable_response
    
    response = await call_next(request)
    return response


# <--------------------------------- Common routes --------------------------------->
@api.get("/")
def root():
    content = None
    with open(os.path.join(base_path, "frontend", "templates", "form.html")) as f:
        content = f.read()

    return HTMLResponse(content=content)


@api.post("/message_with_docs")
async def create_prompt(files: list[UploadFile] = File(...), prompt: str = Form(...)):
    docs = []
    rag = initialize_rag()

    try:

        for file in files:
            content = await file.read()
            temp_storage = os.path.join(base_path, "temp_storage")
            os.makedirs(temp_storage, exist_ok=True)

            if file.filename.endswith('.pdf'):
                saved_file = os.path.join(temp_storage, "pdfs", str(uuid.uuid4()) + ".pdf")
            else:
                saved_file = os.path.join(temp_storage, str(uuid.uuid4()) + "." + file.filename.split('.')[-1])

            with open(saved_file, "wb") as f:
                f.write(content)

            docs.append(saved_file)

        if len(files) > 0:
            rag.upload_documents(docs)

        response_raw = rag.generate_response(user_prompt=prompt)
        response = add_links(response_raw)

        return {"response": response, "status": 200}

    except Exception as e:
        print("!!!ERROR!!!")
        print(e)

    # finally:
    #     for file in files:
    #         temp_storage = os.path.join(base_path, "temp_storage")
    #         saved_file = os.path.join(temp_storage, file.filename)
    #         os.remove(saved_file)


@api.get("/viewer")
def show_document(path: str, page: Optional[int] = 1, lines: Optional[str] = "1-1", start: Optional[int] = 0):
    if not path_is_valid(path):
        return HTTPException(status_code=404, detail="Document not found")

    ext = path.split(".")[-1]
    if ext == 'pdf':
        return PDFHandler(path=path, page=page)
    elif ext in ('txt', 'csv', 'md'):
        return TextHandler(path=path, lines=lines)
    elif ext in ('docx', 'doc'):
        return TextHandler(path=path, lines=lines)  # should be a bit different handler
    else:
        return FileResponse(path=path)


# <--------------------------------- Get --------------------------------->
@api.get("/new_user")
def new_user():
    template = ''
    with open(os.path.join(base_path, "frontend", "templates", "registration.html")) as f:
        template = f.read()

    return HTMLResponse(content=template)


@api.get("/login")
def login():
    template = ''
    with open(os.path.join(base_path, "frontend", "templates", "login.html")) as f:
        template = f.read()

    return HTMLResponse(content=template)


@api.get("/cookie_test")
def test_cookie(request: Request):
    return check_cookie(request)


'''
Use only for testing. For now, provides user info for logged ones, and redirects to
login in other case
'''
@api.get("/test")
def test(request: Request, user: User = Depends(get_current_user)):
    # if user is None:
    #     return RedirectResponse("/login")
    return {
        "user": {
            "email": user.email,
            "password_hash": user.password_hash,
            # "chats": user.chats, # Note: it will rise error since due to the optimization associated fields are not loaded
            # it is just a reference, but the session is closed, however you are trying to get access to the data through this session
            }
        }


@api.get("/chats/id={chat_id}")
def show_chat(chat_id: int):
    return {"chat_id": chat_id}


# <--------------------------------- Post --------------------------------->
@api.post("/new_user")
def new_user(response: Response, user: SUser):
    return create_user(response, user.email, user.password)



@api.post("/login")
def login(response: Response, user: SUser):
    return authenticate_user(response, user.email, user.password)


@api.get("/logout")
def logout(response: Response):
    return clear_cookie(response)


@api.post("/new_chat")
def create_chat(request: Request, title: Optional[str] = "new chat", user: User = Depends(get_current_user)):
    url = create_new_chat(title, user)
    return RedirectResponse(url, status_code=303)