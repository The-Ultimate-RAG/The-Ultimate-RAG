from fastapi import FastAPI, UploadFile, Form, File
import os
from rag_generator import RagSystem
from fastapi.responses import HTMLResponse
from settings import base_path

api = FastAPI()
rag = None

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
            saved_file = os.path.join(temp_storage, file.filename)

            with open(saved_file, "wb") as f:
                f.write(content)

            docs.append(saved_file)
    
        if len(files) > 0:
            rag.upload_documents(docs)

        return {"response": rag.generate_response(user_prompt=prompt), "status": 200}

    except Exception as e:
        print(e)
        
    finally:
        for file in files:
            temp_storage = os.path.join(base_path, "temp_storage")
            saved_file = os.path.join(temp_storage, file.filename)
            os.remove(saved_file)
        
