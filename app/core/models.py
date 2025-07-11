import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from sentence_transformers import (
    CrossEncoder,
)  # SentenceTransformer -> model for embeddings, CrossEncoder -> re-ranker
from torch import Tensor
from google import genai
from google.genai import types
from app.core.chunks import Chunk
from app.settings import settings, BASE_DIR, GeminiEmbeddingSettings

load_dotenv()


class Reranker:
    def __init__(self, model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"):
        self.device: str = settings.device
        self.model_name: str = model
        self.model: CrossEncoder = CrossEncoder(model, device=self.device)

    async def rank(self, query: str, chunks: list[Chunk]) -> list[dict[str, int]]:
        return await asyncio.to_thread(self.model.rank, query, [await chunk.get_raw_text() for chunk in chunks])


class GeminiLLM:
    def __init__(self, model="gemini-2.0-flash"):
        self.client = genai.Client(api_key=settings.api_key)
        self.model = model

    async def get_response(
        self,
        prompt: str,
        stream: bool = True,
        logging: bool = True,
        use_default_config: bool = False,
    ) -> str:
        path_to_prompt = os.path.join(BASE_DIR, "prompt.txt")
        with open(path_to_prompt, "w", encoding="utf-8", errors="replace") as f:
            f.write(prompt)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=(
                types.GenerateContentConfig(**settings.gemini_generation.model_dump())
                if use_default_config
                else None
            ),
        )

        return response.text

    async def get_streaming_response(
        self,
        prompt: str,
        stream: bool = True,
        logging: bool = True,
        use_default_config: bool = False,
    ):
        path_to_prompt = os.path.join(BASE_DIR, "prompt.txt")
        with open(path_to_prompt, "w", encoding="utf-8", errors="replace") as f:
            f.write(prompt)

        response = self.client.models.generate_content_stream(
            model=self.model,
            contents=prompt,
            config=(
                types.GenerateContentConfig(**settings.gemini_generation.model_dump())
                if use_default_config
                else None
            ),
        )

        for chunk in response:
            yield chunk


class GeminiEmbed:
    def __init__(self, model="text-embedding-004"):
        self.client = genai.Client(api_key=settings.api_key)
        self.model = model
        self.settings = GeminiEmbeddingSettings()
        self.max_workers = 5
        self.embed_executor = ThreadPoolExecutor(max_workers=self.max_workers)

    def _embed_batch_sync(self, batch: list[str], idx: int) -> dict:
        response = self.client.models.embed_content(
            model=self.model,
            contents=batch,
            config=types.EmbedContentConfig(
                **settings.gemini_embedding.model_dump()
            ),
        ).embeddings
        return {"idx": idx, "embeddings": response}

    async def encode(self, text: str | list[str]) -> list[Tensor]:

        if isinstance(text, str):
            text = [text]

        groups: list[dict] = []
        max_batch_size = 100  # can not be changed due to google restrictions
        batches: list[list[str]] = [
            text[i : i + max_batch_size]
            for i in range(0, len(text), max_batch_size)
        ]
        print(*[len(batch) for batch in batches])

        loop = asyncio.get_running_loop()

        tasks = [
            loop.run_in_executor(
                self.embed_executor,
                self._embed_batch_sync,
                batch,
                idx
            )
            for idx, batch in enumerate(batches)
        ]

        groups = await asyncio.gather(*tasks)

        groups.sort(key=lambda x: x["idx"])

        result: list[float] = []
        for group in groups:
            for vec in group["embeddings"]:
                result.append(vec.values)
        return result

    async def get_vector_dimensionality(self) -> int | None:
        return getattr(self.settings, "output_dimensionality")


class Wrapper:
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model
        self.client = genai.Client(api_key=settings.api_key)

    async def wrap(self, prompt: str) -> str:
        def wrapper(prompt):
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(**settings.gemini_wrapper.model_dump())
            )
            return response.text
        return await asyncio.to_thread(wrapper, prompt)
