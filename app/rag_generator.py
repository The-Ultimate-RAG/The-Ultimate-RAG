from models import LLM, Embedder, Reranker
from processor import DocumentProcessor
from database import VectorDatabase
import time
import os
from settings import reranker_model, embedder_model, base_path

# TODO: write a better prompt
# TODO: wrap original(user's) prompt with LLM's one

class RagSystem:
    def __init__(self):
        self.embedder = Embedder(model=embedder_model)
        self.reranker = Reranker(model=reranker_model)
        self.processor = DocumentProcessor()
        self.db = VectorDatabase(embedder=self.embedder)
        self.llm = LLM()


    '''
    Provides a prompt with substituted context from chunks

    TODO: add template to prompt without docs
    '''
    def get_prompt_template(self, user_prompt: str, chunks: list) -> str:
        sources = ""
        prompt = ""

        for chunk in chunks:
            citation = (f"[Source: {chunk.filename}, "
                        f"Page: {chunk.page_number}, "
                        f"Lines: {chunk.start_line}-{chunk.end_line}, "
                        f"Start: {chunk.start_index}]\n\n")
            sources += f"Original text:\n{chunk.get_raw_text()}\nCitation:{citation}"

        with open(os.path.join(base_path, "prompt_templates", "test2.txt")) as f:
            prompt = f.read()

        prompt += (
            "**QUESTION**: " 
            f"{user_prompt.strip()}\n"
            "**CONTEXT DOCUMENTS**:\n"
            f"{sources}\n"
        )

        return prompt
    

    '''
    Splits the list of documents into groups with 'split_by' docs (done to avoid qdrant_client connection error handling), loads them,
    splits into chunks, and saves to db
    '''
    def upload_documents(self, documents: list[str], split_by: int = 3, debug_mode: bool = False) -> None:
        
        for i in range(0, len(documents), split_by):

            if debug_mode:
                print(f"New document group is taken into processing, time - {time.time()}")

            docs = documents[i: i + split_by]

            self.processor.load_documents(documents=docs, add_to_unprocessed=True)
            self.processor.generate_chunks()
            self.db.store(self.processor.get_and_save_unsaved_chunks())
    

    '''
    Produces answer to user's request. First, finds the most relevant chunks, generates prompt with them, and asks llm
    '''
    def generate_response(self, user_prompt: str) -> str:
        relevant_chunks = self.db.search(query=user_prompt, top_k=15)
        relevant_chunks = [relevant_chunks[ranked["corpus_id"]]
                           for ranked in self.reranker.rank(query=user_prompt, chunks=relevant_chunks)[:3]]

        general_prompt = self.get_prompt_template(user_prompt=user_prompt, chunks=relevant_chunks)
        
        return self.llm.get_response(prompt=general_prompt)


    '''
    Produces the list of the most relevant chunks
    '''
    def get_relevant_chunks(self, query):
        relevant_chunks = self.db.search(query=query, top_k=15)
        relevant_chunks = [relevant_chunks[ranked["corpus_id"]]
                           for ranked in self.reranker.rank(query=query, chunks=relevant_chunks)]
        return relevant_chunks