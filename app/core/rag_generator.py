from app.core.models import Reranker, GeminiLLM, GeminiEmbed, Wrapper
from app.settings import settings, BASE_DIR, logger
from app.core.processor import DocumentProcessor
from app.core.database import VectorDatabase
from typing import Any, AsyncGenerator
import aiofiles
import asyncio
import os


class RagSystem:
    def __init__(self):
        self.embedder = GeminiEmbed()
        self.reranker = Reranker(model=settings.models.reranker_model)
        self.db = VectorDatabase(embedder=self.embedder)
        self.llm = GeminiLLM()
        self.wrapper = Wrapper()
        self.processor = DocumentProcessor()


    async def get_general_prompt(self, user_prompt: str, collection_name: str) -> str:
        loop = asyncio.get_event_loop()
        start = loop.time()
        await logger.info(f"Time of initializing - {loop.time() - start}")

        start = loop.time()
        enhanced_prompt = await self.enhance_prompt(user_prompt.strip())
        await logger.info(f"Time of enhancing - {loop.time() - start}")

        start = loop.time()
        relevant_chunks = await self.db.search(collection_name, query=enhanced_prompt, top_k=30)
        await logger.info(f"Time of searching - {loop.time() - start}")

        start = loop.time()
        if relevant_chunks is not None and len(relevant_chunks) > 0:
            ranks = await self.reranker.rank(query=enhanced_prompt, chunks=relevant_chunks)
            relevant_chunks = [relevant_chunks[rank["corpus_id"]] for rank in ranks]
        else:
            relevant_chunks = []

        sources = ""
        prompt = ""

        for chunk in relevant_chunks[: min(10, len(relevant_chunks))]:
            citation = (
                f"[Source: {chunk.filename}, "
                f"Page: {chunk.page_number}, "
                f"Lines: {chunk.start_line}-{chunk.end_line}, "
                f"Start: {chunk.start_index}]\n\n"
            )
            sources += f"Original text:\n{await chunk.get_raw_text()}\nCitation:{citation}"

        await logger.info(f"Time of reranking - {loop.time() - start}")

        start = loop.time()
        async with aiofiles.open(
            os.path.join(BASE_DIR, "app", "prompt_templates", "test2.txt")
        ) as prompt_file:
            prompt = await prompt_file.read()

        prompt += (
            "**QUESTION**: "
            f"{enhanced_prompt}\n"
            "**CONTEXT DOCUMENTS**:\n"
            f"{sources}\n"
        )
        await logger.info(f"Time of preparing prompt - {loop.time() - start}")

        return prompt

    async def enhance_prompt(self, original_prompt: str) -> str:
        path_to_wrapping_prompt = os.path.join(BASE_DIR, "app", "prompt_templates", "wrapper.txt")
        enhanced_prompt = ""
        async with aiofiles.open(path_to_wrapping_prompt, "r") as f:
            enhanced_prompt = (await f.read()).replace("[USERS_PROMPT]", original_prompt)
        return await self.wrapper.wrap(enhanced_prompt)

    async def upload_documents(self, collection_name: str, documents: list[str], split_by: int = 3) -> None:
        loop = asyncio.get_event_loop()
        for i in range(0, len(documents), split_by):

            if settings.debug:
                await logger.info("New document group is taken into processing")

            docs = documents[i : i + split_by]

            loading_time = 0
            chunk_generating_time = 0
            db_saving_time = 0

            if settings.debug:
                await logger.info("Start loading the documents")

            start = loop.time()
            await self.processor.load_documents(documents=docs)
            loading_time = loop.time() - start

            if settings.debug:
                await logger.info("Start loading chunk generation")

            start = loop.time()
            await self.processor.generate_chunks()
            chunk_generating_time = loop.time() - start

            if settings.debug:
                await logger.info("Start saving to db")

            start = loop.time()
            chunks = await self.processor.get_and_save_unsaved_chunks()
            await self.db.store(collection_name, chunks)
            db_saving_time = loop.time() - start

            if settings.debug:
                await logger.info(
                    f"loading time = {loading_time}, chunk generation time = {chunk_generating_time}, saving time = {db_saving_time}\n"
                )

    async def extract_text(self, response) -> str:
        text = ""
        try:
            text = response.candidates[0].content.parts[0].text
        except Exception as e:
            print(e)
        return text

    async def generate_response(self, collection_name: str, user_prompt: str, stream: bool = True) -> str:
        general_prompt = await self.get_general_prompt(
            user_prompt=user_prompt, collection_name=collection_name
        )

        return self.llm.get_response(prompt=general_prompt)

    async def generate_response_stream(self, collection_name: str, user_prompt: str, stream: bool = True) -> AsyncGenerator[Any, Any]:
        loop = asyncio.get_event_loop()
        start = loop.time()
        general_prompt = await self.get_general_prompt(
            user_prompt=user_prompt, collection_name=collection_name
        )
        logger.info(f"Time of getting prompt message - {loop.time() - start}")

        async for chunk in self.llm.get_streaming_response(
            prompt=general_prompt
        ):
            yield await self.extract_text(chunk)

    async def get_relevant_chunks(self, collection_name: str, query):
        relevant_chunks = await self.db.search(collection_name, query=query, top_k=15)
        relevant_chunks = [
            relevant_chunks[ranked["corpus_id"]]
            for ranked in await self.reranker.rank(query=query, chunks=relevant_chunks)
        ]
        return relevant_chunks

    async def create_new_collection(self, collection_name: str) -> None:
        await self.db.create_collection(collection_name)

    async def get_collections_names(self) -> list[str]:
        return await self.db.get_collections()
