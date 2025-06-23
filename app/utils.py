from fastapi.templating import Jinja2Templates
from fastapi import Request, UploadFile

from app.backend.controllers.chats import list_user_chats, verify_ownership_rights
from app.backend.controllers.users import get_current_user
from app.backend.models.users import User
from app.rag_generator import RagSystem
from app.settings import base_path

from uuid import uuid4
import os

rag = None

# <----------------------- System ----------------------->
def initialize_rag() -> RagSystem:
    global rag
    if rag is None:
        rag = RagSystem()
    return rag


# <----------------------- Tools ----------------------->
'''
Updates response context and adds context of navbar (role, instance(or none)) and footer (none)
'''
def extend_context(context: dict, selected: int = None):
    user = get_current_user(context.get("request"))
    navbar = {
        "navbar": False,
        "navbar_path": "components/navbar.html",
        "navbar_context": {
            "chats": [],
            "user": {
                "role": "user" if user else "guest",
                "instance": user
            }
        }
    }
    sidebar = {
        "sidebar": True,
        "sidebar_path": "components/sidebar.html",
        "sidebar_context": {
            "selected": selected if selected is not None else None,
            "chat_groups": list_user_chats(user.id) if user else []
        }
    }
    footer = {
        "footer": False,
        "footer_context": None
    }

    context.update(**navbar)
    context.update(**footer)
    context.update(**sidebar)

    return context


'''
Validates chat viewing permission by comparing user's chats and requested one
'''
def protect_chat(user: User, chat_id: int) -> bool:
    return verify_ownership_rights(user, chat_id)


async def save_documents(files: list[UploadFile], RAG: RagSystem) -> None:
    temp_storage = os.path.join(base_path, "temp_storage")
    docs = []
    
    if files is None or len(files) == 0:
        return
    
    for file in files:
        content = await file.read()

        if file.filename.endswith('.pdf'):
            saved_file = os.path.join(temp_storage, "pdfs", str(uuid4()) + ".pdf")
        else:
            saved_file = os.path.join(temp_storage, str(uuid4()) + "." + file.filename.split('.')[-1])

        with open(saved_file, "wb") as f:
            f.write(content)

        docs.append(saved_file)

    if len(files) > 0:
        RAG.upload_documents(docs)


# <----------------------- Handlers ----------------------->
def PDFHandler(request: Request, path: str, page: int, templates) -> Jinja2Templates.TemplateResponse:
    filename = os.path.basename(path)
    url_path = f"/pdfs/{filename}"
    current_template = "pages/show_pdf.html"
    return templates.TemplateResponse(
        current_template, 
        extend_context({
        "request": request, 
        "page": str(page or 1), 
        "url_path": url_path,
        "user": get_current_user(request)
        })
    )


def TextHandler(request: Request, path: str, lines: str, templates) -> Jinja2Templates.TemplateResponse:
    file_content = ""
    with open(path, "r") as f:
        file_content = f.read()

    start_line, end_line = map(int, lines.split('-'))

    text_before_citation = []
    text_after_citation = []
    citation = []
    anchor_added = False

    for index, line in enumerate(file_content.split('\n')):
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
        extend_context({
        "request": request, 
        "text_before_citation": text_before_citation,
        "text_after_citation": text_after_citation,
        "citation": citation,
        "anchor_added": anchor_added,
        "user": get_current_user(request)
        })
    )


'''
Optional handler
'''
def DocHandler():
    pass
