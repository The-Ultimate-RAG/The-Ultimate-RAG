from app.backend.controllers.chats import list_user_chats, verify_ownership_rights
from app.backend.controllers.users import get_current_user
from app.settings import BASE_DIR, logger, settings
from fastapi.templating import Jinja2Templates
from app.core.rag_generator import RagSystem
from app.backend.models.users import User
from fastapi import Request, UploadFile
from uuid import uuid4
import markdown
import aiofiles
import asyncio
import shutil
import os


rag = None

def initialize_rag() -> RagSystem:
    global rag
    if rag is None:
        print("Start RAG initialization")
        rag = RagSystem()
    return rag



async def extend_context(context: dict, selected: int = None):
    user = await get_current_user(context.get("request"))
    navbar = {
        "navbar": False,
        "navbar_path": "components/navbar.html",
        "navbar_context": {
            "chats": [],
            "user": {"role": "user" if user else "guest", "instance": user},
        },
    }
    sidebar = {
        "sidebar": True,
        "sidebar_path": "components/sidebar.html",
        "sidebar_context": {
            "selected": selected if selected is not None else None,
            "chat_groups": await list_user_chats(user.id) if user else [],
        },
    }
    footer = {"footer": False, "footer_context": None}

    context.update(**navbar)
    context.update(**footer)
    context.update(**sidebar)

    return context


async def protect_chat(user: User, chat_id: str) -> bool:
    return await verify_ownership_rights(user, chat_id)


async def save_documents(
    files: list[UploadFile],
    user: User,
    chat_id: str,
) -> list[str]:
    storage = os.path.join(
        BASE_DIR,
        "chats_storage",
        f"user_id={user.id}",
        f"chat_id={chat_id}",
        "documents",
    )
    docs = []

    if files is None or len(files) == 0:
        return

    await aiofiles.os.makedirs(os.path.join(storage, "pdfs"), exist_ok=True)

    if settings.debug:
        await logger.info(f"Documents for saving: {len(files)}")

    for file in files:
        content = await file.read()

        if file.filename.endswith(".pdf"):
            saved_file = os.path.join(storage, "pdfs", str(uuid4()) + ".pdf")
        else:
            saved_file = os.path.join(
                storage, str(uuid4()) + "." + file.filename.split(".")[-1]
            )

        async with aiofiles.open(saved_file, "wb") as f:
            await f.write(content)

        docs.append(saved_file)

    return docs


async def get_pdf_path(path: str) -> str:
    parts = path.split("chats_storage")
    if len(parts) < 2:
        return ""
    return "chats_storage" + "".join(parts[1:])


async def construct_collection_name(user: User, chat_id: int) -> str:
    return f"user_id_{user.id}_chat_id_{chat_id}"


async def create_collection(user: User, chat_id: int, RAG: RagSystem) -> None:
    if RAG is None:
        raise RuntimeError("RAG was not initialized")

    await RAG.create_new_collection(await construct_collection_name(user, chat_id))

    if settings.debug:
        for collection in await rag.get_collections_names():
            await logger.info(collection)


async def lines_to_markdown(lines: list[str]) -> list[str]:
    loop = asyncio.get_running_loop()
    return await asyncio.gather(*[
        loop.run_in_executor(None, markdown.markdown, line)
        for line in lines
    ])


# <----------------------- Handlers ----------------------->
async def PDFHandler(
    request: Request, path: str, page: int, templates
) -> Jinja2Templates.TemplateResponse:

    url_path = await get_pdf_path(path=path)

    if settings.debug:
        await logger.info(f"PDF path - {path}, url-path - {url_path}")

    current_template = "pages/show_pdf.html"
    return templates.TemplateResponse(
        current_template,
        await extend_context(
            {
                "request": request,
                "page": str(page or 1),
                "url_path": url_path,
                "user": await get_current_user(request),
            }
        ),
    )


async def TextHandler(
    request: Request, path: str, lines: str, templates
) -> Jinja2Templates.TemplateResponse:
    file_content = ""
    async with aiofiles.open(path, "r") as f:
        file_content = await f.read()

    start_line, end_line = map(int, lines.split("-"))

    text_before_citation = []
    text_after_citation = []
    citation = []
    anchor_added = False

    for index, line in enumerate(file_content.split("\n")):
        if line == "" or line == "\n":
            continue
        if index + 1 < start_line:
            text_before_citation.append(line)
        elif end_line < index + 1:
            text_after_citation.append(line)
        else:
            anchor_added = True
            citation.append(line)

    current_template = "pages/show_text.html"

    return templates.TemplateResponse(
        current_template,
        await extend_context(
            {
                "request": request,
                "text_before_citation": await lines_to_markdown(text_before_citation),
                "text_after_citation": await lines_to_markdown(text_after_citation),
                "citation": await lines_to_markdown(citation),
                "anchor_added": anchor_added,
                "user": await get_current_user(request),
            }
        ),
    )
