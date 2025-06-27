from qdrant_client import QdrantClient  # main component to provide the access to db
from qdrant_client.http.models import ScoredPoint
from qdrant_client.models import VectorParams, Distance, \
    PointStruct  # VectorParams -> config of vectors that will be used as primary keys
from app.core.models import Embedder  # Distance -> defines the metric
from app.core.chunks import Chunk  # PointStruct -> instance that will be stored in db
import numpy as np
from uuid import UUID
from app.settings import settings
import time
from fastapi import HTTPException


class VectorDatabase:
    def __init__(self, embedder: Embedder, host: str = "qdrant", port: int = 6333):
        self.host: str = host
        self.client: QdrantClient = self._initialize_qdrant_client()
        self.embedder: Embedder = embedder  # embedder is used to convert a user's query
        self.already_stored: np.array[np.array] = np.array([]).reshape(0,
                                                                       embedder.get_vector_dimensionality())  # should be already normalized

    def store(self, collection_name: str, chunks: list[Chunk], batch_size: int = 1000) -> None:
        points: list[PointStruct] = []

        vectors = self.embedder.encode([chunk.get_raw_text() for chunk in chunks])

        for vector, chunk in zip(vectors, chunks):
            if self.accept_vector(collection_name, vector):
                points.append(PointStruct(
                    id=str(chunk.id),
                    vector=vector,
                    payload={"metadata": chunk.get_metadata(), "text": chunk.get_raw_text()}
                ))

        if len(points):
            for group in range(0, len(points), batch_size):
                self.client.upsert(
                    collection_name=collection_name,
                    points=points[group: group + batch_size],
                    wait=False,
                )

    '''
    Measures a cosine of angle between tow vectors
    '''

    def cosine_similarity(self, vec1, vec2):
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        return vec1_np @ vec2_np / (np.linalg.norm(vec1_np) * np.linalg.norm(vec2_np))

    '''
    Defines weather the vector should be stored in the db by searching for the most
    similar one
    '''

    def accept_vector(self, collection_name: str, vector: np.array) -> bool:
        most_similar = self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=1,
            with_vectors=True
        ).points

        if not len(most_similar):
            return True
        else:
            most_similar = most_similar[0]

        if 1 - self.cosine_similarity(vector, most_similar.vector) < settings.max_delta:
            return False
        return True

    '''
    According to tests, re-ranker needs ~7-10 chunks to generate the most accurate hit

    TODO: implement hybrid search
    '''

    def search(self, collection_name: str, query: str, top_k: int = 5) -> list[Chunk]:
        query_embedded: np.ndarray = self.embedder.encode(query)

        if isinstance(query_embedded, list):
            query_embedded = query_embedded[0]
            
        points: list[ScoredPoint] = self.client.query_points(
            collection_name=collection_name,
            query=query_embedded,
            limit=top_k
        ).points

        return [
            Chunk(
                id=UUID(point.payload.get("metadata", {}).get("id", "")),
                filename=point.payload.get("metadata", {}).get("filename", ""),
                page_number=point.payload.get("metadata", {}).get("page_number", 0),
                start_index=point.payload.get("metadata", {}).get("start_index", 0),
                start_line=point.payload.get("metadata", {}).get("start_line", 0),
                end_line=point.payload.get("metadata", {}).get("end_line", 0),
                text=point.payload.get("text", "")
            ) for point in points
        ]

    def _initialize_qdrant_client(self, max_retries=5, delay=2) -> QdrantClient:
        for attempt in range(max_retries):
            try:
                client = QdrantClient(**settings.qdrant.model_dump())
                client.get_collections()
                return client
            except Exception as e:
                if attempt == max_retries - 1:
                    raise HTTPException(
                        500,
                        f"Failed to connect to Qdrant server after {max_retries} attempts. "
                        f"Last error: {str(e)}"
                    )

                print(f"Connection attempt {attempt + 1} out of {max_retries} failed. "
                      f"Retrying in {delay} seconds...")

                time.sleep(delay)
                delay *= 2

    def _check_collection_exists(self, collection_name: str) -> bool:
        try:
            return self.client.collection_exists(collection_name)
        except Exception as e:
            raise HTTPException(
                500, f"Failed to check collection {collection_name} exists. Last error: {str(e)}"
            )

    def _create_collection(self, collection_name: str) -> None:
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedder.get_vector_dimensionality(),
                    distance=Distance.COSINE
                )
            )
        except Exception as e:
            raise HTTPException(500, f"Failed to create collection {self.collection_name}: {str(e)}")

    def create_collection(self, collection_name: str) -> None:
        try:
            if self._check_collection_exists(collection_name):
                return
            self._create_collection(collection_name)
        except Exception as e:
            print(e)
            raise HTTPException(500, e)

    def __del__(self):
        if hasattr(self, "client"):
            self.client.close()

    def get_collections(self) -> list[str]:
        try:
            return self.client.get_collections()
        except Exception as e:
            print(e)
            raise HTTPException(500, "Failed to get collection names")
