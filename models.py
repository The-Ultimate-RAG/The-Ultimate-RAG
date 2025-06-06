from sentence_transformers import SentenceTransformer, CrossEncoder
from ctransformers import AutoModelForCausalLM
import torch
from chunks import Chunk
import numpy as np

# TODO: add device to global config file

class Embedder:
    def __init__(self, model: str = "BAAI/bge-m3"):
        device = "cuda" if torch.cuda.is_available() else 'cpu'
        self.device: str = device
        self.model_name: str = model
        self.model: SentenceTransformer = SentenceTransformer(model, device=device)

    def encode(self, text: str) -> np.ndarray:
        return self.model.encode(sentences=text)
    
    def get_vector_dimensionality(self) -> (int | None):
        return self.model.get_sentence_embedding_dimension()
    

class Reranker:
    def __init__(self, model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"):
        device = "cuda" if torch.cuda.is_available() else 'cpu'
        self.device: str = device
        self.model_name: str = model
        self.model: CrossEncoder = CrossEncoder(model, device=device)
    
    
    def rank(self, query: str, chunks: list[Chunk]) -> list[dict[str, int]]:
        return self.model.rank(query, [chunk.get_raw_text() for chunk in chunks])


'''
TODO: add models parameters to global config file
TODO: add exception handling when response have more tokens than was set
'''
class LLM:
    def __init__(self):
        self.model = AutoModelForCausalLM.from_pretrained(
            "TheBloke/Mistral-7B-v0.1-GGUF",
            model_file="mistral-7b-v0.1.Q5_K_S.gguf",
            model_type="mistral",
            gpu_layers=0,
            threads=8,
            context_length=512
        )

    def get_response(self, prompt: str, stream: bool = True, logging: bool = True) -> str:
        generated_text = ""
        
        if not stream:
            tokenized_text: list[int] = self.model.tokenize(text=prompt)
            response: list[int] = self.model.generate(tokens=tokenized_text)
            return self.model.detokenize(response)
        
        for token in self.model.generate(self.model.tokenize(prompt)):
            chunk = self.model.detokenize([token])
            generated_text += chunk
            if logging:
                print(chunk, end="", flush=True)