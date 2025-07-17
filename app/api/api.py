from app.backend.controllers.messages import register_message
from app.core.document_validator import path_is_valid
from app.core.response_parser import add_links
from app.backend.models.users import User
from app.settings import BASE_DIR
from app.backend.controllers.chats import (
    get_chat_with_messages,
    create_new_chat,
    update_title,
    list_user_chats
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
from fastapi.middleware.cors import CORSMiddleware
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

origins = [
    "http://localhost:5173",
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        chat_id: str = Form(None),
) -> StreamingResponse:
    status = 200
    try:
        user = extract_user_from_context(request)
        print("-" * 100, "User ---->", user, "-" * 100, "\n\n")
        collection_name = construct_collection_name(user, chat_id)

        message_id = register_message(content=prompt, sender="user", chat_id=chat_id)

        await save_documents(
            collection_name, files=files, RAG=rag, user=user, chat_id=chat_id, message_id=message_id
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
    with open(os.path.join(BASE_DIR, "response.txt"), "w") as f:
        f.write(data.get("message", ""))
    updated_message = add_links(data.get("message", ""))
    register_message(
        content=updated_message, sender="system", chat_id=data.get("chatId")
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
        )
    else:
        return FileResponse(path=path)


# <--------------------------------- Get --------------------------------->
@api.get("/list_chats")
def list_chats_for_user(request: Request):
    user = extract_user_from_context(request)
    chats = list_user_chats(user.id)
    print(f"Chats for user {user.id}: {chats}")
    return JSONResponse({"chats": chats})


@api.get("/chats/{chat_id}")
def show_chat(request: Request, chat_id: str):
    user = extract_user_from_context(request)

    if not protect_chat(user, chat_id):
        raise HTTPException(401, "Yod do not have rights to use this chat!")

    chat_data = get_chat_with_messages(chat_id)

    print(f"DEBUG: Data for chat '{chat_id}' from get_chat_with_messages: {chat_data}")

    if not chat_data:
        raise HTTPException(status_code=404, detail=f"Chat with id {chat_id} not found.")

    update_title(chat_data["chat_id"])

    return JSONResponse(content=chat_data)


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
        url = f"/chats/{chat.id}"

    return RedirectResponse(url, status_code=303)


# <--------------------------------- Post --------------------------------->
@api.post("/new_chat")
def create_chat(request: Request, title: Optional[str] = "new chat"):
    user = extract_user_from_context(request)
    new_chat_data = create_new_chat(title, user)
    if not new_chat_data.get("id"):
        raise HTTPException(500, "New chat could not be created.")

    create_collection(user, new_chat_data["id"], rag)

    return JSONResponse(new_chat_data)

if __name__ == "__main__":
    pass
