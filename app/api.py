from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.staticfiles import StaticFiles
import os
from rag_generator import RagSystem
from fastapi.responses import HTMLResponse, FileResponse
from settings import base_path
from response_parser import add_links
from document_validator import path_is_valid

api = FastAPI()
rag = None
api.mount("/pdfs", StaticFiles(directory=os.path.join(base_path, "temp_storage", "pdfs")), name="pdfs")

def initialize_rag() -> RagSystem:
    global rag
    if rag is None:
        rag = RagSystem()
    return rag

@api.get("/")
def root():
    content = None
    with open(os.path.join(base_path, "frontend", "templates", "form.html")) as f:
        content = f.read()

    return HTMLResponse(content=content)


@api.post("/message_with_docs/")
async def create_prompt(files: list[UploadFile] = File(...), prompt: str = Form(...)):
    docs = []
    rag = initialize_rag()

    try:
        for file in files:
            content = await file.read()
            temp_storage = os.path.join(base_path, "temp_storage")
            os.makedirs(temp_storage, exist_ok=True)

            if file.filename.endswith('.pdf'):
                saved_file = os.path.join(temp_storage, "pdfs", file.filename)
            else:
                saved_file = os.path.join(temp_storage, file.filename)

            with open(saved_file, "wb") as f:
                f.write(content)

            docs.append(saved_file)
    
        if len(files) > 0:
            rag.upload_documents(docs)

        response_raw = rag.generate_response(user_prompt=prompt)
        response = add_links(response_raw)

        return {"response": response, "status": 200}

    except Exception as e:
        print(e)
        
    # finally:
    #     for file in files:
    #         temp_storage = os.path.join(base_path, "temp_storage")
    #         saved_file = os.path.join(temp_storage, file.filename)
    #         os.remove(saved_file)

def PDFHandler(path: str, page: int):
    template = ""
    with open(os.path.join(base_path, "frontend", "templates", "show_pdf.html"), "r") as f:
        template = f.read()

    filename = os.path.basename(path)
    url_path = f"/pdfs/{filename}"

    template = template.replace("PAGE", str(page or 1)).replace("PATH", url_path)

    return HTMLResponse(content=template)

def TextHandler(path: str, lines: str):

    text = ""
    with open(os.path.join(base_path, "frontend", "templates", "show_text.html"), "r") as f:
        text = f.read()

    file_content = ""
    with open(path, "r") as f:
        file_content = f.read()

    start_line, end_line = map(int, lines.split('-'))

    content = []
    for index, line in enumerate(file_content.split('\n')):
        if start_line <= index <= end_line:
            content.append(f'<span style="background-color: yellow;">{ line }</span>')
        else:
            content.append(line)

    text += "<pre>" + '\n'.join(content) + "</pre>"
    text += '</body>\n</html>'

    return HTMLResponse(content=text)

def DocHandler():
    pass

@api.get("/viewer/")
def show_document(path: str, page: int, lines: str, start: int):
    if not path_is_valid(path):
        return  HTTPException(status_code=404, detail="Document not found")

    ext = path.split(".")[-1]
    if ext == 'pdf':
        return PDFHandler(path=path, page=page)
    elif ext in ('txt', 'csv', 'md'):
        return TextHandler(path=path, lines=lines)
    elif ext in ('docx', 'doc'):
        return TextHandler(path=path, lines=lines)
    else:
        return FileResponse(path=path)
