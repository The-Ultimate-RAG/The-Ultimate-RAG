from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from embedder import Embedder
from chunks import Chunk
from processor import Document_processor
import numpy as np

class Vector_database:
    def __init__(self, host: str, port: int, embedder: Embedder):
        self.host: str = host
        self.client: QdrantClient = QdrantClient(host=host, port=port)
        self.collection_name: str = "document_chunks"
        self.embedder: Embedder = embedder

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
                id=str(chunk.id), # TODO: remove kostyly, hotya ih navernoe ne uberesh
                vector=vector,
                payload={"metadata": chunk.get_metadata(), "text": chunk.get_raw_text()}
            ))

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )


def main():
    processor = Document_processor()
    processor.load_document("/home/danil/Documents/Учеба/Прога/ML/TheUltimateRAG/samples/sample.txt", add_to_unprocessed=True)
    processor.generate_chunks()

    embedder = Embedder()

    db = Vector_database("localhost", 6333, embedder)
    db.store(processor.chunks)


if __name__ == '__main__':
    main()