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
import aiofiles
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
        print("<>" * 100)
        user = await get_current_user(request)
        print("<><><><><><><>User<><><><><><><>", user)
        authorized = True
        if user is None:
            authorized = False
            user = await create_user()

        print(f"User in Context ----> {user.id}\n")

        request.state.current_user = user
        response = await call_next(request)

        if authorized:
            await refresh_cookie(request=request, response=response)
        else:
            await authorize_user(response, user)
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
        user = await extract_user_from_context(request)
        print("-" * 100, "User ---->", user, "-" * 100, "\n\n")
        collection_name = await construct_collection_name(user, chat_id)
        print(f"Received message -------> {prompt}")
        await register_message(content=prompt, sender="user", chat_id=chat_id)

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
    async with aiofiles.open(os.path.join(BASE_DIR, "response.txt"), "w") as f:
        await f.write(data.get("message", ""))
    updated_message = await add_links(data.get("message", ""))
    await register_message(
        content=updated_message, sender="assistant", chat_id=data.get("chat_id")
    )
    return JSONResponse({"updated_message": updated_message})


@api.get("/viewer")
async def show_document(
    request: Request,
    path: str,
    page: Optional[int] = 1,
    lines: Optional[str] = "1-1",
    start: Optional[int] = 0,
):
    if not await path_is_valid(path):
        return HTTPException(status_code=404, detail="Document not found")

    ext = path.split(".")[-1]
    if ext == "pdf":
        return await PDFHandler(request, path=path, page=page, templates=templates)
    elif ext in ("txt", "csv", "md", "json"):
        return await TextHandler(request, path=path, lines=lines, templates=templates)
    elif ext in ("docx", "doc"):
        return await TextHandler(
            request, path=path, lines=lines, templates=templates
        )
    else:
        return FileResponse(path=path)


# <--------------------------------- Get --------------------------------->
@api.get("/cookie_test")
async def test_cookie(request: Request):
    return await check_cookie(request)


@api.get("/test")
async def test(request: Request):
    user = await get_current_user()
    return {
        "user": {
            "id": user.id,
        }
    }


@api.get("/chats/id={chat_id}")
async def show_chat(request: Request, chat_id: str):
    current_template = "pages/chat.html"

    chat = await get_chat_with_messages(chat_id)
    user = await extract_user_from_context(request)

    await update_title(chat["chat_id"])

    if not await protect_chat(user, chat_id):
        raise HTTPException(401, "Yod do not have rights to use this chat!")

    context = await extend_context({"request": request, "user": user}, selected=chat_id)
    context.update(chat)

    return templates.TemplateResponse(current_template, context)


@api.get("/")
async def last_user_chat(request: Request):
    user = await extract_user_from_context(request)
    chat = await get_latest_chat(user)
    url = None

    if chat is None:
        print("new_chat")
        new_chat = await create_new_chat("new chat", user)
        url = new_chat.get("url")
        try:
            await create_collection(user, new_chat.get("chat_id"), rag)
        except Exception as e:
            raise HTTPException(500, e)

    else:
        url = f"/chats/id={chat.id}"

    return RedirectResponse(url, status_code=303)


# <--------------------------------- Post --------------------------------->
@api.post("/new_chat")
async def create_chat(
    request: Request,
    title: Optional[str] = "new chat",
):
    user = await extract_user_from_context(request)
    new_chat = await create_new_chat(title, user)
    url = new_chat.get("url")
    chat_id = new_chat.get("chat_id")

    if url is None or chat_id is None:
        raise HTTPException(500, "New chat was not created")

    try:
        await create_collection(user, chat_id, rag)
    except Exception as e:
        raise HTTPException(500, e)

    return RedirectResponse(url, status_code=303)
