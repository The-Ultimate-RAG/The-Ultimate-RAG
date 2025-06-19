from sentence_transformers import SentenceTransformer, \
    CrossEncoder  # SentenceTransformer -> model for embeddings, CrossEncoder -> re-ranker
from ctransformers import AutoModelForCausalLM
from torch import Tensor
from google import genai
from google.genai import types
from app.key import KEY
from app.chunks import Chunk
import numpy as np # used only for type hints
from app.settings import device, local_llm_config, local_generation_config, gemini_generation_config


class Embedder:
    def __init__(self, model: str = "BAAI/bge-m3"):
        self.device: str = device
        self.model_name: str = model
        self.model: SentenceTransformer = SentenceTransformer(model, device=self.device)

    '''
    Encodes string to dense vector
    '''

    def encode(self, text: str | list[str]) -> Tensor | list[Tensor]:
        return self.model.encode(sentences=text, show_progress_bar=False, batch_size=32)

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

class LocalLLM:
    def __init__(self):
        self.model = AutoModelForCausalLM.from_pretrained(**local_llm_config)

    '''
    Produces the response to user's prompt

    stream -> flag, determines weather we need to wait until the response is ready or can show it token by token 

    TODO: invent a way to really stream the answer (as return value)
    '''

    def get_response(self, prompt: str, stream: bool = True, logging: bool = True,
                     use_default_config: bool = True) -> str:

        with open("prompt.txt", "w") as f:
            f.write(prompt)

        generated_text = ""
        tokenized_text: list[int] = self.model.tokenize(text=prompt)
        response: list[int] = self.model.generate(tokens=tokenized_text, **local_generation_config)

        if logging:
            print(response)

        if not stream:
            return self.model.detokenize(response)

        for token in response:
            chunk = self.model.detokenize([token])
            generated_text += chunk
            if logging:
                print(chunk, end="", flush=True)  # flush -> clear the buffer

        return generated_text


class Gemini:
    def __init__(self, model="gemini-2.0-flash"):
        self.client = genai.Client(api_key=KEY)
        self.model = model

    def get_response(self, prompt: str, stream: bool = True, logging: bool = True,
                     use_default_config: bool = False) -> str:
        with open("prompt.txt", "w", encoding="utf-8", errors="replace") as f:
            f.write(prompt)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(**gemini_generation_config) if use_default_config else None
        )

        return response.text
