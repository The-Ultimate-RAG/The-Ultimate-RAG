from qdrant_client import AsyncQdrantClient  # main component to provide the access to db
from qdrant_client.http.models import (
    ScoredPoint,
    Filter,
    FieldCondition,
    MatchText
)
from app.core.models import GeminiEmbed
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    TextIndexParams,
    TokenizerType
)  # VectorParams -> config of vectors that will be used as primary keys
from app.core.processor import DocumentProcessor
from app.core.chunks import Chunk  # PointStruct -> instance that will be stored in db
import numpy as np
from uuid import UUID
from app.settings import settings
import time
from fastapi import HTTPException
import re
import asyncio


class VectorDatabase:
    def __init__(self, embedder: GeminiEmbed, host: str = "qdrant", port: int = 6333):
        self.host: str = host
        self.client: AsyncQdrantClient = self._initialize_qdrant_client()
        self.embedder: GeminiEmbed = embedder  # embedder is used to convert a user's query

    async def store(
        self, collection_name: str, chunks: list[Chunk], batch_size: int = 1000
    ) -> None:
        points: list[PointStruct] = []

        print("Start getting text embeddings")
        start = time.time()
        vectors = await self.embedder.encode([await chunk.get_raw_text() for chunk in chunks])
        print(f"Embeddings - {time.time() - start}")

        for vector, chunk in zip(vectors, chunks):
            ok = await self.accept_vector(collection_name, vector)
            if ok:
                points.append(
                    PointStruct(
                        id=str(chunk.id),
                        vector=vector,
                        payload={
                            "metadata": await chunk.get_metadata(),
                            "text": await chunk.get_raw_text(),
                        },
                    )
                )

        async def _upsert(batch):
            await self.client.upsert(
                collection_name=collection_name,
                points=batch,
                wait=True,
            )

        batches = [
            points[group : group + batch_size]
            for group in range(0, len(points), batch_size)
        ]

        await asyncio.gather(*[_upsert(batch) for batch in batches])

    async def cosine_similarity(self, vec1: list[float], vec2: list[float] | list[list[float]]) -> float:
        loop = asyncio.get_running_loop()

        def compute_similarity():
            if len(vec2) == 0:
                return 0

            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)

            if vec2_np.ndim == 2:
                vec2_np = vec2_np.T
            similarities = np.array(vec1_np @ vec2_np / (np.linalg.norm(vec1_np) * np.linalg.norm(vec2_np, axis=0)))
            return np.max(similarities)

        return await loop.run_in_executor(None, compute_similarity)

    async def accept_vector(self, collection_name: str, vector: np.array) -> bool:
        search = await self.client.query_points(
            collection_name=collection_name,
            query=vector, limit=1, with_vectors=True
        )

        most_similar = search.points

        if not len(most_similar):
            return True
        most_similar = most_similar[0]

        return 1 - await self.cosine_similarity(vector, most_similar.vector) >= settings.max_delta

    async def construct_keywords_list(self, query: str) -> list[FieldCondition]:
        loop = asyncio.get_running_loop()
        def extract_keywords():
            keywords = re.findall(r'\b[A-Z]{2,}\b', query)
            return [
                FieldCondition(key="text", match=MatchText(text=word))
                for word in keywords
                if 2 <= len(word) <= 30
            ]
        return await loop.run_in_executor(None, extract_keywords)

    async def combine_points_without_duplications(self, first: list[ScoredPoint], second: list[ScoredPoint] = None) -> list[ScoredPoint]:
        combined = []
        similarity_vectors = []

        to_combine = [first]
        if second is not None:
            to_combine.append(second)

        for group in to_combine:
            for point in group:
                similarity = await self.cosine_similarity(point.vector, similarity_vectors)
                if 1 - similarity > min(settings.max_delta, 0.2):
                    combined.append(point)
                    similarity_vectors.append(point.vector)
        return combined

    async def search(self, collection_name: str, query: str, top_k: int = 5) -> list[Chunk]:
        query_embedded: np.ndarray = await self.embedder.encode(query)

        if isinstance(query_embedded, list):
            query_embedded = query_embedded[0]

        keywords = await self.construct_keywords_list(query)

        search = await self.client.query_points(
            collection_name=collection_name,
            query=query_embedded,
            limit=top_k + int(top_k * 0.3),
            query_filter=Filter(should=keywords),
            with_vectors=True
        )

        mixed_result: list[ScoredPoint] = search.points

        print(f"Len of original array -> {len(mixed_result)}")
        combined = await self.combine_points_without_duplications(mixed_result)
        print(f"Len of combined array -> {len(combined)}")

        return [
            Chunk(
                id=UUID(point.payload.get("metadata", {}).get("id", "")),
                filename=point.payload.get("metadata", {}).get("filename", ""),
                page_number=point.payload.get("metadata", {}).get("page_number", 0),
                start_index=point.payload.get("metadata", {}).get("start_index", 0),
                start_line=point.payload.get("metadata", {}).get("start_line", 0),
                end_line=point.payload.get("metadata", {}).get("end_line", 0),
                text=point.payload.get("text", ""),
            )
            for point in combined
        ]

    def _initialize_qdrant_client(self, max_retries=5, delay=2) -> AsyncQdrantClient:
        for attempt in range(max_retries):
            try:
                client = AsyncQdrantClient(**settings.qdrant.model_dump())
                return client
            except Exception as e:
                if attempt == max_retries - 1:
                    raise HTTPException(
                        500,
                        f"Failed to connect to Qdrant server after {max_retries} attempts. "
                        f"Last error: {str(e)}",
                    )

                print(
                    f"Connection attempt {attempt + 1} out of {max_retries} failed. "
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)
                delay *= 2

    async def _check_collection_exists(self, collection_name: str) -> bool:
        try:
            return await self.client.collection_exists(collection_name)
        except Exception as e:
            raise HTTPException(
                500,
                f"Failed to check collection {collection_name} exists. Last error: {str(e)}",
            )

    async def _create_collection(self, collection_name: str) -> None:
        try:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size= await self.embedder.get_vector_dimensionality(),
                    distance=Distance.COSINE,
                ),
            )
            await self.client.create_payload_index(
                collection_name=collection_name,
                field_name="text",
                field_schema=TextIndexParams(
                    type="text",
                    tokenizer=TokenizerType.WORD,
                    min_token_len=2,
                    max_token_len=30,
                    lowercase=True
                )
            )
        except Exception as e:
            raise HTTPException(
                500, f"Failed to create collection {self.collection_name}: {str(e)}"
            )

    async def create_collection(self, collection_name: str) -> None:
        try:
            if await self._check_collection_exists(collection_name):
                return
            await self._create_collection(collection_name)
        except Exception as e:
            print(e)
            raise HTTPException(500, e)

    # def __del__(self):
    #     if hasattr(self, "client"):
    #         await self.client.close()

    async def get_collections(self) -> list[str]:
        try:
            return await self.client.get_collections()
        except Exception as e:
            print(e)
            raise HTTPException(500, "Failed to get collection names")
