from models import LLM, Embedder, Reranker
from processor import Document_processor
from database import Vector_database
from os.path import isfile, join # will be removed, for now used to find files in dir
import time
import os

# TODO: write a better prompt
# TODO: wrap original(user's) prompt with LLM's one

class RAG_system:
    def __init__(self):
        self.embedder = Embedder()
        self.reranker = Reranker()
        self.processor = Document_processor()
        self.db = Vector_database(embedder=self.embedder)
        self.llm = LLM()


    '''
    Provides a prompt with substituted context from chunks

    TODO: add template to prompt without docs
    '''
    def get_prompt_template(self, user_prompt: str, chunks: list) -> str:
        sources = ""

        for chunk in chunks:
            citation = f"[Source: {chunk.filename}, Page: {chunk.page_number}, Lines: {chunk.start_line}-{chunk.end_line}, Start: {chunk.start_index}]\n\n"
            sources += f"Original text:\n{chunk.get_raw_text()}\nCitation:{citation}"

        prompt = (
            "You are a helpful assistant that provides concise answers based on the following documents.\n"
            "Rules:\n"
            "1. Answer ONLY using the provided context\n"
            "2. Keep answers under 3 sentences unless complex analysis is required\n"
            "3. Always cite sources like: [Source: filename, Page X]\n"
            "4. If unsure, say 'I couldn't find a definitive answer in the documents'\n\n"
            f"Question: {user_prompt.strip()}\n\n"
            f"Relevant Context:\n{sources}\n\n"
            "Concise Answer:"
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
        relevant_chunks = self.db.search(query=user_prompt, top_K=15)
        relevant_chunks = [relevant_chunks[ranked["corpus_id"]] for ranked in self.reranker.rank(query=user_prompt, chunks=relevant_chunks)[:3]]

        general_prompt = self.get_prompt_template(user_prompt=user_prompt, chunks=relevant_chunks)
        
        return self.llm.get_response(prompt=general_prompt)
