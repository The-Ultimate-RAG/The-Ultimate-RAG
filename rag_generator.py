from models import LLM, Embedder
from processor import Document_processor
from database import Vector_database

class RAG_system:
    def __init__(self):
        self.embedder = Embedder()
        self.processor = Document_processor()
        self.db = Vector_database(embedder=self.embedder)


    def upload_documents(self, documents: list[str]) -> None:
        self.processor.load_documents(documents=documents, add_to_unprocessed=True)
        self.processor.generate_chunks()
        self.db.store(self.processor.get_and_save_unsaved_chunks())
    

    def generate_response(self, user_prompt: str):
        pass 