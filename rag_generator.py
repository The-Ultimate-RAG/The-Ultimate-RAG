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
    '''
    def get_prompt_template(self, user_prompt: str, chunks: list) -> str:
        sources = ""

        for chunk in chunks:
            citation = f"[Source: {chunk.filename}, Page: {chunk.page_number}, Lines: {chunk.start_line}-{chunk.end_line}, Start: {chunk.start_index}]\n\n"
            sources += f"Original text:\n{chunk.get_raw_text()}\nCitation:{citation}"

        prompt = (
                "You are a helpful assistant that answers questions based on the provided context.\n"
                "Always cite your sources using the exact references provided with the context.\n"
                "The are starting positions called 'Start' in the sources' context. For each reference mention it and add to its value the index "
                "of the character, were the exact citation starts.\n"
                "Just provide answer as plain text. If you use dirrect text from source wrap it with '' and add [idx] were idx is the number of source from context.\n"
                "Provide ONLY your answer and then list the references in the end.\n\n"
                f"Question: {user_prompt.strip()}\n\n"
                f"Context:\n{sources.strip()}\n\n"
                "Your answer:"
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
        relevant_chunks = self.db.search(query=user_prompt, top_K=10)
        relevant_chunks = [relevant_chunks[ranked["corpus_id"]] for ranked in self.reranker.rank(query=user_prompt, chunks=relevant_chunks)[:3]]

        general_prompt = self.get_prompt_template(user_prompt=user_prompt, chunks=relevant_chunks)
        
        return self.llm.get_response(prompt=general_prompt)


def main():
    system = RAG_system()

    path = "path_to_dir_with_docs"
    files = [join(path, f) for f in os.listdir(path) if isfile(join(path, f))]

    print("Start processing the documents")
    start = time.time()
    system.upload_documents(files, debug_mode=True)
    print(f"Loading of {len(files)} files has taken {start - time.time()} seconds\n\n\n")

    system.generate_response("What is the purpose of the NullHandler in Python's logging module, and why is it recommended for use in libraries?")


if __name__ == '__main__':
    main()