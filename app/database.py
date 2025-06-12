from qdrant_client import QdrantClient  # main component to provide the access to db
from qdrant_client.embed import embedder
from qdrant_client.http.models import ScoredPoint
from qdrant_client.models import VectorParams, Distance, \
    PointStruct  # VectorParams -> config of vectors that will be used as primary keys
from models import Embedder  # Distance -> defines the metric
from chunks import Chunk  # PointStruct -> instance that will be stored in db
import numpy as np
from uuid import UUID
from settings import qdrant_client_config
import time


# TODO: for now all documents are saved to one db, but what if user wants to get references from his own documents, so temp storage is needed

class VectorDatabase:
    def __init__(self, embedder: Embedder, host: str = "qdrant", port: int = 6333):
        self.host: str = host
        self.client: QdrantClient = self._initialize_qdrant_client()
        self.collection_name: str = "document_chunks"
        self.embedder: Embedder = embedder  # embedder is used to convert a user's query

        if not self._check_collection_exists():
            self._create_collection()

    def store(self, chunks: list[Chunk]) -> None:
        points: list[PointStruct] = []

        for chunk in chunks:
            vector: np.ndarray = self.embedder.encode(chunk.get_raw_text())
            points.append(PointStruct(
                id=str(chunk.id),
                vector=vector,
                payload={"metadata": chunk.get_metadata(), "text": chunk.get_raw_text()}
            ))

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    '''
    According to tests, re-ranker needs ~7-10 chunks to generate the most accurate hit

    TODO: implement hybrid search
    '''

    def search(self, query: str, top_k: int = 5) -> list[Chunk]:
        query_embedded: np.ndarray = self.embedder.encode(query)

        points: list[ScoredPoint] = self.client.query_points(
            collection_name=self.collection_name,
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
                client = QdrantClient(**qdrant_client_config)
                client.get_collections()
                return client
            except Exception as e:
                if attempt == max_retries - 1:
                    raise ConnectionError(
                        f"Failed to connect to Qdrant server after {max_retries} attempts. "
                        f"Last error: {str(e)}"
                    )

                print(f"Connection attempt {attempt + 1} out of {max_retries} failed. "
                      f"Retrying in {delay} seconds...")

                time.sleep(delay)
                delay *= 2

    def _check_collection_exists(self) -> bool:
        try:
            return self.client.collection_exists(self.collection_name)
        except Exception as e:
            raise ConnectionError(
                f"Failed to check collection {self.collection_name} exists. Last error: {str(e)}"
            )

    def _create_collection(self) -> None:
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedder.get_vector_dimensionality(),
                    distance=Distance.COSINE
                )
            )
        except Exception as e:
            raise RuntimeError(f"Failed to create collection {self.collection_name}: {str(e)}")

    def __del__(self):
        if hasattr(self, "client"):
            self.client.close()
