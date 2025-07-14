"""
This file consolidates parameters for logging, database connections, model paths, API settings, and security.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from aiologger.handlers.streams import AsyncStreamHandler
from pydantic import BaseModel, Field, computed_field
from aiologger.formatters.base import Formatter
from typing import Callable, List, Optional
from datetime import timedelta
from dotenv import load_dotenv
from aiologger import Logger
from pathlib import Path
import asyncio
import torch
import sys
import os


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
    echo: bool = False
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

    debug: bool = True


logger = Logger.with_default_handlers(name='app-logger')


async def setup_logger(logger: Logger) -> None:
    for handler in logger.handlers:
        await handler.close()
    logger.handlers.clear()

    formatter = Formatter(fmt="%(levelname)s: %(message)s")
    stream_handler = AsyncStreamHandler(stream=sys.stdout)
    stream_handler.formatter = formatter
    logger.add_handler(stream_handler)


settings = Settings()


async def main():
    await setup_logger()

    await logger.warning("Successfully loaded settings")
    await logger.info(f"Base Directory: {settings.base_dir}")
    await logger.info(f"Running on device: {settings.device}")
    await logger.info(f"Qdrant Host: {settings.qdrant.host}")
    await logger.info(f"LLM GPU Layers: {settings.local_llm.gpu_layers}")

    await logger.info("\n--- Full settings model dump (secrets masked) ---")
    await logger.info(settings.model_dump())

    await logger.info("\n--- Secret fields (from .env file) ---")
    await logger.info(f"Postgres URL: {settings.postgres.url}")
    await logger.info(f"JWT Algorithm: {settings.jwt_algorithm}")
    await logger.info(f"Secret Pepper: {settings.secret_pepper}")
    await logger.info(f"Gemini API Key: {settings.api_key}")

    await logger.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

