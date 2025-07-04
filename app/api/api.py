from app.backend.controllers.messages import register_message
from app.core.document_validator import path_is_valid
from app.core.response_parser import add_links
from app.backend.models.users import User
from app.settings import BASE_DIR
from app.backend.controllers.chats import (
    get_chat_with_messages,
    create_new_chat,
    update_title,
)
from app.backend.controllers.users import (
    extract_user_from_context,
    get_current_user,
    get_latest_chat,
    refresh_cookie,
    authorize_user,
    check_cookie,
    create_user
)
from app.core.utils import (
    construct_collection_name,
    create_collection,
    extend_context,
    initialize_rag,
    save_documents,
    protect_chat,
    TextHandler,
    PDFHandler,
)

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import (
    HTTPException,
    UploadFile,
    Request,
    Depends,
    FastAPI,
    Form,
    File,
)
from fastapi.responses import (
    StreamingResponse,
    RedirectResponse,
    FileResponse,
    JSONResponse,
)

from typing import Optional
import os


# <------------------------------------- API ------------------------------------->
api = FastAPI()
rag = initialize_rag()

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


# <--------------------------------- Middleware --------------------------------->
@api.middleware("http")
async def require_user(request: Request, call_next):
    print("&" * 40, "START MIDDLEWARE", "&" * 40)
    try:
        print(f"Path ----> {request.url.path}, Method ----> {request.method}, Port ----> {request.url.port}\n")

        stripped_path = request.url.path.strip("/")

        if (
            stripped_path.startswith("pdfs")
            or "static/styles.css" in stripped_path
            or "favicon.ico" in stripped_path
        ):
            return await call_next(request)

        user = get_current_user(request)
        authorized = True
        if user is None:
            authorized = False
            user = create_user()

        print(f"User in Context ----> {user.id}\n")

        request.state.current_user = user
        response = await call_next(request)

        if authorized:
            refresh_cookie(request=request, response=response)
        else:
            authorize_user(response, user)
        return response

    except Exception as exception:
        raise exception
    finally:
        print("&" * 40, "END MIDDLEWARE", "&" * 40, "\n\n")

# <--------------------------------- Common routes --------------------------------->
@api.post("/message_with_docs")
async def send_message(
    request: Request,
    files: list[UploadFile] = File(None),
    prompt: str = Form(...),
    chat_id: str =Form(None),
) -> StreamingResponse:
    status = 200
    try:
        user = extract_user_from_context(request)
        print("-" * 100, "User ---->", user, "-" * 100, "\n\n")
        collection_name = construct_collection_name(user, chat_id)

        register_message(content=prompt, sender="user", chat_id=chat_id)

        await save_documents(
            collection_name, files=files, RAG=rag, user=user, chat_id=chat_id
        )

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
        content=updated_message, sender="assistant", chat_id=data.get("chat_id")
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
            "id": user.id,
        }
    }


@api.get("/chats/id={chat_id}")
def show_chat(request: Request, chat_id: str):
    current_template = "pages/chat.html"

    chat = get_chat_with_messages(chat_id)
    user = extract_user_from_context(request)

    update_title(chat["chat_id"])

    if not protect_chat(user, chat_id):
        raise HTTPException(401, "Yod do not have rights to use this chat!")

    context = extend_context({"request": request, "user": user}, selected=chat_id)
    context.update(chat)

    return templates.TemplateResponse(current_template, context)


@api.get("/")
def last_user_chat(request: Request):
    user = extract_user_from_context(request)
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
@api.post("/new_chat")
def create_chat(
    request: Request,
    title: Optional[str] = "new chat",
):
    user = extract_user_from_context(request)
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
