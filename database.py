from qdrant_client import QdrantClient # main component to provide the access to db
from qdrant_client.models import VectorParams, Distance, PointStruct # VectorParams -> config of vectors that will be used as primary keys
from models import Embedder                                          # Distance -> defines the metric
from chunks import Chunk                                             # PointStruct -> instance that will be stored in db
import numpy as np
from uuid import UUID
from settings import qdrant_client_config

# TODO: for now all documents are saved to one db, but what if user wants to get references from his own documents, so temp storage is needed

class Vector_database:
    def __init__(self, embedder: Embedder, host: str = "localhost", port: int = 6333):
        self.host: str = host
        self.client: QdrantClient = QdrantClient(**qdrant_client_config)
        self.collection_name: str = "document_chunks"
        self.embedder: Embedder = embedder # embedder is used to convert a user's query 

        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=embedder.get_vector_dimensionality(), distance=Distance.COSINE)
            )
    

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
    def search(self, query: str, top_K: int = 5) -> list[Chunk]:
        query_embedded: np.ndarray = self.embedder.encode(query)

        points: list[PointStruct] = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedded,
            limit=top_K
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
            )
        for point in points]
