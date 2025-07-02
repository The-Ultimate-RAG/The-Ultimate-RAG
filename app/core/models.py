import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, \
    CrossEncoder  # SentenceTransformer -> model for embeddings, CrossEncoder -> re-ranker
from ctransformers import AutoModelForCausalLM
from torch import Tensor
from google import genai
from google.genai import types
from app.core.chunks import Chunk
from app.settings import settings, BASE_DIR, GeminiEmbeddingSettings

load_dotenv()


class Embedder:
    def __init__(self, model: str = "BAAI/bge-m3"):
        self.device: str = settings.device
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
        self.device: str = settings.device
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
        self.model = AutoModelForCausalLM.from_pretrained(**settings.local_llm.model_dump())

    '''
    Produces the response to user's prompt

    stream -> flag, determines weather we need to wait until the response is ready or can show it token by token 

    TODO: invent a way to really stream the answer (as return value)
    '''
    def get_response(self, prompt: str, stream: bool = True, logging: bool = True,
                     use_default_config: bool = True) -> str:

        with open("../prompt.txt", "w") as f:
            f.write(prompt)

        generated_text = ""
        tokenized_text: list[int] = self.model.tokenize(text=prompt)
        response: list[int] = self.model.generate(tokens=tokenized_text, **settings.local_llm.model_dump())

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


class GeminiLLM:
    def __init__(self, model="gemini-2.0-flash"):
        self.client = genai.Client(api_key=settings.api_key)
        self.model = model

    def get_response(self, prompt: str, stream: bool = True, logging: bool = True,
                     use_default_config: bool = False) -> str:
        path_to_prompt = os.path.join(BASE_DIR, "prompt.txt")
        with open(path_to_prompt, "w", encoding="utf-8", errors="replace") as f:
            f.write(prompt)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                **settings.gemini_generation.model_dump()) if use_default_config else None
        )

        return response.text

    async def get_streaming_response(self, prompt: str, stream: bool = True, logging: bool = True,
                     use_default_config: bool = False):
        path_to_prompt = os.path.join(BASE_DIR, "prompt.txt")
        with open(path_to_prompt, "w", encoding="utf-8", errors="replace") as f:
            f.write(prompt)

        response = self.client.models.generate_content_stream(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                **settings.gemini_generation.model_dump()) if use_default_config else None
        )

        for chunk in response:
            yield chunk

class GeminiEmbed:
    def __init__(self, model="text-embedding-004"):
        self.client = genai.Client(api_key=settings.api_key)
        self.model = model
        self.settings = GeminiEmbeddingSettings()

    def encode(self, text: str | list[str]) -> list[Tensor]:

        if isinstance(text, str):
            text = [text]
        
        output: list[Tensor] = []
        max_batch_size = 100 # can not be changed due to google restrictions

        for i in range(0, len(text), max_batch_size):
            batch = text[i:i + max_batch_size]
            response = self.client.models.embed_content(
            model=self.model,
            contents=batch,
            config=types.EmbedContentConfig(
                **settings.gemini_embedding.model_dump())
            ).embeddings

            for i, emb in enumerate(response):
                output.append(emb.values)

        return output
    
    def get_vector_dimensionality(self) -> (int | None):
        return getattr(self.settings, "output_dimensionality")