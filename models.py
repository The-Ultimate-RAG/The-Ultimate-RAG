from sentence_transformers import SentenceTransformer, CrossEncoder # SentenceTransformer -> model for embeddings, CrossEncoder -> re-ranker
from ctransformers import AutoModelForCausalLM
import torch # used to run on cuda if avaliable
from chunks import Chunk
import numpy as np # used only for type hints

# TODO: add device to global config file
# TODO: replace all models with geminai after receiving api-keys

class Embedder:
    def __init__(self, model: str = "BAAI/bge-m3"):
        device = "cuda" if torch.cuda.is_available() else 'cpu'
        self.device: str = device
        self.model_name: str = model
        self.model: SentenceTransformer = SentenceTransformer(model, device=device)


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
        device = "cuda" if torch.cuda.is_available() else 'cpu'
        self.device: str = device
        self.model_name: str = model
        self.model: CrossEncoder = CrossEncoder(model, device=device)
    
    
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
        self.max_tokens = 4096
        self.model = AutoModelForCausalLM.from_pretrained(
            "TheBloke/Mistral-7B-v0.1-GGUF",
            model_file="mistral-7b-v0.1.Q5_K_S.gguf",
            model_type="mistral",
            gpu_layers=20 if torch.cuda.is_available() else 0,
            threads=8,
            context_length=self.max_tokens 
        )


    '''
    Produces the response to user's prompt

    stream -> flag, determines weather we need to wait until the response is ready or can show it token by token 

    TODO: invent a way to really stream the answer (as return value)
    '''
    def get_response(self, prompt: str, stream: bool = True, logging: bool = True) -> str:

        generation_config = {
            "last_n_tokens": 128, # regulates repetitions
            "temperature": 0.3,
            "repetition_penalty": 1.2,
        }
            
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