"""
This file consolidates parameters for logging, database connections, model paths, API settings, and security.
"""

# Standard Library Imports
import os
import logging
from datetime import timedelta
from typing import Callable, List, Optional

# Third-Party Library Imports
import torch
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class QdrantSettings(BaseModel):
    host: str = Field("localhost", validation_alias="LOCAL_HOST")
    port: int = Field(6334, validation_alias="LOCAL_PORT")
    prefer_grpc: bool = Field(True, validation_alias="gRPC")


class ModelsSettings(BaseModel):
    embedder_model: str = "all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"


class LocalLLMSettings(BaseModel):
    model_path_or_repo_id: str = "TheBloke/Mistral-7B-v0.1-GGUF"
    model_file: str = "mistral-7b-v0.1.Q5_K_S.gguf"
    model_type: str = "mistral"

    gpu_layers: Optional[int] = None
    threads: int = 8
    context_length: int = 4096
    mlock: bool = True  # Locks the model into RAM to prevent swapping


class GenerationSettings(BaseModel):
    last_n_tokens: int = (
        128  # The most recent of tokens that will be penalized (if it was repeated)
    )
    temperature: float = (
        0.3  # Controls the randomness of output. Higher value - higher randomness
    )
    repetition_penalty: float = 1.2


class TextSplitterSettings(BaseModel):
    chunk_size: int = 1000  # The maximum size of chunk
    chunk_overlap: int = 100
    length_function: Callable = len  # Function to measure chunk length
    is_separator_regex: bool = False
    add_start_index: bool = True


class APISettings(BaseModel):
    app: str = "app.api.api:api"
    host: str = "127.0.0.1"
    port: int = 5050
    reload: bool = True  # The server will reload on system changes


class GeminiSettings(BaseModel):
    temperature: float = 0.6
    top_p: float = 0.8
    top_k: int = 20
    candidate_count: int = None
    seed: int = 5
    max_output_tokens: int = 1001
    stop_sequences: List[str] = Field(default_factory=lambda: ["STOP!"])
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0


class GeminiEmbeddingSettings(BaseModel):
    output_dimensionality: int = 382
    task_type: str = "retrieval_document"


class GeminiWrapperSettings(BaseModel):
    temperature: float = 0.0
    top_p: float = 0.95
    top_k: int = 20
    candidate_count: int = 1
    seed: int = 5
    max_output_tokens: int = 100
    stop_sequences: List[str] = Field(default_factory=lambda: ["STOP!"])
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0


class PostgresSettings(BaseModel):
    url: str = os.environ["DATABASE_URL"]
    echo: bool = True
    pool_size: int = 5
    max_overflow: int = 10

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        extra="ignore"
    )

    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    local_llm: LocalLLMSettings = Field(default_factory=LocalLLMSettings)
    models: ModelsSettings = Field(default_factory=ModelsSettings)
    local_generation: GenerationSettings = Field(default_factory=GenerationSettings)
    text_splitter: TextSplitterSettings = Field(default_factory=TextSplitterSettings)
    api: APISettings = Field(default_factory=APISettings)
    gemini_generation: GeminiSettings = Field(default_factory=GeminiSettings)
    gemini_embedding: GeminiEmbeddingSettings = Field(
        default_factory=GeminiEmbeddingSettings
    )
    gemini_wrapper: GeminiWrapperSettings = Field(
        default_factory=GeminiWrapperSettings
    )
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)

    use_gemini: bool = True
    max_delta: float = (
        0.15  # defines what is the minimum boundary for vectors to be considered similar
    )
    max_cookie_lifetime: timedelta = timedelta(seconds=3000)
    password_reset_token_lifetime: timedelta = timedelta(seconds=3000)

    device: str = Field(
        default_factory=lambda: "cuda" if torch.cuda.is_available() else "cpu"
    )
    base_dir: Path = BASE_DIR

    stream: bool = True

    secret_pepper: str = os.environ["SECRET_PEPPER"]
    jwt_algorithm: str = os.environ["JWT_ALGORITHM"]
    api_key: str = os.environ["GEMINI_API_KEY"]

    @computed_field
    @property
    def get_gpu_layers(self) -> int:
        return 20 if self.device == "cuda" else 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


settings = Settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

if __name__ == "__main__":

    def bold_text(text: str):
        return "\033[1m" + text + "\033[0m"

    print(bold_text("--- Successfully loaded settings ---"))
    print(f"{bold_text("Base Directory:")} {settings.base_dir}")
    print(f"{bold_text("Running on device:")} {settings.device}")
    print(f"{bold_text("Qdrant Host:")} {settings.qdrant.host}")
    print(f"{bold_text("LLM GPU Layers:")} {settings.local_llm.gpu_layers}")

    # model_dump() is useful for debugging or passing to other libraries.
    # It safely excludes secret values.
    print(bold_text("\n--- Full settings model dump (secrets masked) ---"))
    print(settings.model_dump())

    print(bold_text("\n--- Secret fields (from .env file) ---"))
    print(f"{bold_text("Postgres URL:")} {settings.postgres.url}")
    print(f"{bold_text("JWT Algorithm:")} {settings.jwt_algorithm}")
    print(f"{bold_text("Secret Pepper:")} {settings.secret_pepper}")
    # Corrected line to access the API key
    print(f"{bold_text("Gemini API Key:")} {settings.api_key}")

# # Qdrant vector database connection.
# qdrant_client_config = {
#     "host": os.getenv("QDRANT_HOST", "localhost"),
#     "port": os.getenv("QDRANT_PORT", "6333"),
# }
#
# # Automatically detects CUDA or uses CPU.
# device = "cuda" if torch.cuda.is_available() else 'cpu'
#
# embedder_model = "all-MiniLM-L6-v2"
#
# reranker_model = "cross-encoder/ms-marco-MiniLM-L6-v2"
#
# local_llm_config = {
#     "model_path_or_repo_id": "TheBloke/Mistral-7B-v0.1-GGUF",
#     "model_file": "mistral-7b-v0.1.Q5_K_S.gguf",
#     "model_type": "mistral",
#     "gpu_layers": 20 if torch.cuda.is_available() else 0,
#     "threads": 8,
#     "context_length": 4096,  # The maximum context window is 4096 tokens
#     "mlock": True,  # Locks the model into RAM to prevent swapping
# }
#
# local_generation_config = {
#     "last_n_tokens": 128,  # The most recent of tokens that will be penalized (if it was repeated)
#     "temperature": 0.3,  # Controls the randomness of output. Higher value - higher randomness
#     "repetition_penalty": 1.2,
# }
#
# text_splitter_config = {
#     "chunk_size": 1000,  # The maximum size of chunk
#     "chunk_overlap": 100,
#     "length_function": len,  # Function to measure chunk length
#     "is_separator_regex": False,
#     "add_start_index": True,
# }
#
# # "127.0.0.1"
# api_config = {
#     "app": "app.api:api",
#     "host": "127.0.0.1",
#     "port": 5050,
#     "reload": True,  # The server will reload on system changes
# }
#
# gemini_generation_config = {
#     "temperature": 0,  # deterministic, predictable output
#     "top_p": 0.95,
#     "top_k": 20,
#     "candidate_count": 1,
#     "seed": 5,
#     "max_output_tokens": 1001,
#     "stop_sequences": ['STOP!'],
#     "presence_penalty": 0.0,
#     "frequency_penalty": 0.0,
# }
#
# use_gemini: bool = True
#
# max_delta = 0.15  # defines what is the minimum boundary for vectors to be considered similar
#
# postgres_client_config = {
#     "url": os.getenv("POSTGRESQL_DATABASE_URL"),
#     "echo": False,
# }
#
# jwt_algorithm = "HS256"
# VERY_SECRET_PEPPER = os.getenv("SECRET_PEPPER")
#
# max_cookie_lifetime = 3000  # in seconds
#
