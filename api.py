from fastapi import FastAPI, UploadFile, Form, File
import uvicorn
import os
from rag_generator import RAG_system

api = FastAPI()
rag = None

def initialize_rag() -> RAG_system:
    global rag
    if rag is None:
        rag = RAG_system()
    return rag

@api.get("/")
def root():
    return {"status": "ok"}

@api.post("/message_with_docs")
async def create_prompt(files: list[UploadFile] = File(...), prompt: str = Form(...)):
    docs = []
    rag = initialize_rag()

    try:
        for file in files:
            content = await file.read()
            temp_storage = os.path.join(os.path.dirname(os.path.realpath(__file__)), "temp_storage")
            os.makedirs(temp_storage, exist_ok=True)
            saved_file = os.path.join(temp_storage, file.filename)

            with open(saved_file, "wb") as f:
                f.write(content)

            docs.append(saved_file)
    
        rag.upload_documents(docs)
        return {"response": rag.generate_response(user_prompt=prompt), "status": 200}

    except Exception as e:
        print(e)
        


def main():
    uvicorn.run("api:api", host="127.0.0.1", port=5050, reload=True)

if __name__ == '__main__':
    main()