from sentence_transformers import SentenceTransformer, CrossEncoder # SentenceTransformer -> model for embeddings, CrossEncoder -> re-ranker
from ctransformers import AutoModelForCausalLM
import torch # used to run on cuda if avaliable
from chunks import Chunk
import numpy as np # used only for type hints
from settings import device, llm_config, generation_config

# TODO: replace all models with geminai after receiving api-keys

class Embedder:
    def __init__(self, model: str = "BAAI/bge-m3"):
        self.device: str = device
        self.model_name: str = model
        self.model: SentenceTransformer = SentenceTransformer(model, device=self.device)


    '''
    Encodes string to dense vector
    '''
    def encode(self, text: str) -> np.ndarray:
        return self.model.encode(sentences=text)
    

    '''
    Returns the dimensionality of dense vector
    '''
    def get_vector_dimensionality(self) -> (int | None):
        return self.model.get_sentence_embedding_dimension()
    

class Reranker:
    def __init__(self, model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"):
        self.device: str = device
        self.model_name: str = model
        self.model: CrossEncoder = CrossEncoder(model, device=self.device)
    
    
    '''
    Returns re-sorted (by relevance) vector with dicts, from which we need only the 'corpus_id'
    since it is a position of chunk in original list
    '''
    def rank(self, query: str, chunks: list[Chunk]) -> list[dict[str, int]]:
        return self.model.rank(query, [chunk.get_raw_text() for chunk in chunks])



# TODO: add models parameters to global config file
# TODO: add exception handling when response have more tokens than was set
# TODO: find a way to restrict the model for providing too long answers

class LLM:
    def __init__(self):
        self.model = AutoModelForCausalLM.from_pretrained(**llm_config)


    '''
    Produces the response to user's prompt

    stream -> flag, determines weather we need to wait until the response is ready or can show it token by token 

    TODO: invent a way to really stream the answer (as return value)
    '''
    def get_response(self, prompt: str, stream: bool = True, logging: bool = True) -> str:
        
        with open("prompt.txt", "w") as f:
            f.write(prompt)
        
        generated_text = ""
        tokenized_text: list[int] = self.model.tokenize(text=prompt)
        response: list[int] = self.model.generate(tokens=tokenized_text, **generation_config)

        if logging:
            print(response)
        
        if not stream:
            return self.model.detokenize(response)
        
        for token in response:
            chunk = self.model.detokenize([token])
            generated_text += chunk
            if logging:
                print(chunk, end="", flush=True) # flush -> clear the buffer

        return generated_text