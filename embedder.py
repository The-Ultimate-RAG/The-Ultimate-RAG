from sentence_transformers import SentenceTransformer
import torch
import numpy as np

class Embedder:
    def __init__(self, model: str = "BAAI/bge-m3"):
        device = "cuda" if torch.cuda.is_available() else 'cpu'
        self.device: str = device
        self.model: SentenceTransformer = SentenceTransformer(model, device=device)

    def encode(self, text: str) -> np.ndarray:
        return self.model.encode(sentences=text)
    
    def get_vector_dimensionality(self) -> (int | None):
        return self.model.get_sentence_embedding_dimension()