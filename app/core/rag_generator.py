from typing import Any, AsyncGenerator
from app.core.models import LocalLLM, Embedder, Reranker, GeminiLLM, GeminiEmbed, Wrapper
from app.core.processor import DocumentProcessor
from app.core.database import VectorDatabase
import time
import os
from app.settings import settings, BASE_DIR


class RagSystem:
    def __init__(self):
        self.embedder = (
            GeminiEmbed()
            if settings.use_gemini
            else Embedder(model=settings.models.embedder_model)
        )
        self.reranker = Reranker(model=settings.models.reranker_model)
        self.processor = DocumentProcessor(self.embedder)
        self.db = VectorDatabase(embedder=self.embedder)
        self.llm = GeminiLLM() if settings.use_gemini else LocalLLM()
        self.wrapper = Wrapper()

    """
    Provides a prompt with substituted context from chunks

    TODO: add template to prompt without docs
    """

    def get_general_prompt(self, user_prompt: str, collection_name: str) -> str:
        enhanced_prompt = self.enhance_prompt(user_prompt.strip())

        relevant_chunks = list(self.db.search(collection_name, query=enhanced_prompt, top_k=30))
        if relevant_chunks is not None and len(relevant_chunks) > 0:
            ranks = self.reranker.rank(query=enhanced_prompt, chunks=relevant_chunks)
            relevant_chunks = [relevant_chunks[rank["corpus_id"]] for rank in ranks]
        else:
            relevant_chunks = []

        sources = ""
        prompt = ""

        for chunk in relevant_chunks[: min(5, len(relevant_chunks))]:
            citation = (
                f"[Source: {chunk.filename}, "
                f"Page: {chunk.page_number}, "
                f"Lines: {chunk.start_line}-{chunk.end_line}, "
                f"Start: {chunk.start_index}]\n\n"
            )
            sources += f"Original text:\n{chunk.get_raw_text()}\nCitation:{citation}"

        with open(
            os.path.join(BASE_DIR, "app", "prompt_templates", "test2.txt")
        ) as prompt_file:
            prompt = prompt_file.read()

        prompt += (
            "**QUESTION**: "
            f"{enhanced_prompt}\n"
            "**CONTEXT DOCUMENTS**:\n"
            f"{sources}\n"
        )
        print(prompt)
        return prompt

    def enhance_prompt(self, original_prompt: str) -> str:
        path_to_wrapping_prompt = os.path.join(BASE_DIR, "app", "prompt_templates", "wrapper.txt")
        enhanced_prompt = ""
        with open(path_to_wrapping_prompt, "r") as f:
            enhanced_prompt = f.read().replace("[USERS_PROMPT]", original_prompt)
        return self.wrapper.wrap(enhanced_prompt)

    """
    Splits the list of documents into groups with 'split_by' docs (done to avoid qdrant_client connection error handling), loads them,
    splits into chunks, and saves to db
    """

    def upload_documents(
        self,
        collection_name: str,
        documents: list[str],
        split_by: int = 3,
        debug_mode: bool = True,
    ) -> None:

        for i in range(0, len(documents), split_by):

            if debug_mode:
                print(
                    "<"
                    + "-" * 10
                    + "New document group is taken into processing"
                    + "-" * 10
                    + ">"
                )

            docs = documents[i : i + split_by]

            loading_time = 0
            chunk_generating_time = 0
            db_saving_time = 0

            print("Start loading the documents")
            start = time.time()
            self.processor.load_documents(documents=docs, add_to_unprocessed=True)
            loading_time = time.time() - start

            print("Start loading chunk generation")
            start = time.time()
            self.processor.generate_chunks()
            chunk_generating_time = time.time() - start

            print("Start saving to db")
            start = time.time()
            self.db.store(collection_name, self.processor.get_and_save_unsaved_chunks())
            db_saving_time = time.time() - start

            if debug_mode:
                print(
                    f"loading time = {loading_time}, chunk generation time = {chunk_generating_time}, saving time = {db_saving_time}\n"
                )

    def extract_text(self, response) -> str:
        text = ""
        try:
            text = response.candidates[0].content.parts[0].text
        except Exception as e:
            print(e)
        return text

    """
    Produces answer to user's request. First, finds the most relevant chunks, generates prompt with them, and asks llm
    """

    async def generate_response(
        self, collection_name: str, user_prompt: str, stream: bool = True
    ) -> str:
        general_prompt = self.get_general_prompt(
            user_prompt=user_prompt, collection_name=collection_name
        )

        return self.llm.get_response(prompt=general_prompt)

    async def generate_response_stream(
        self, collection_name: str, user_prompt: str, stream: bool = True
    ) -> AsyncGenerator[Any, Any]:
        general_prompt = self.get_general_prompt(
            user_prompt=user_prompt, collection_name=collection_name
        )

        async for chunk in self.llm.get_streaming_response(
            prompt=general_prompt, stream=True
        ):
            yield self.extract_text(chunk)

    """
    Produces the list of the most relevant chunkВs
    """

    def get_relevant_chunks(self, collection_name: str, query):
        relevant_chunks = self.db.search(collection_name, query=query, top_k=15)
        relevant_chunks = [
            relevant_chunks[ranked["corpus_id"]]
            for ranked in self.reranker.rank(query=query, chunks=relevant_chunks)
        ]
        return relevant_chunks

    def create_new_collection(self, collection_name: str) -> None:
        self.db.create_collection(collection_name)

    def get_collections_names(self) -> list[str]:
        return self.db.get_collections()
