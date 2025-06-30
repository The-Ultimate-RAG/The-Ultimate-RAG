"""
This file consolidates parameters for logging, database connections, model paths, API settings, and security.
"""

import logging  # kind of advanced logger
import os

import torch
from dotenv import load_dotenv

load_dotenv()

base_path = os.path.dirname(os.path.realpath(__file__))

# Logging setup for console output.
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

# Qdrant vector database connection.
qdrant_client_config = {
    "host": "localhost",
    "port": 6333,
}

# Automatically detects CUDA or uses CPU.
device = "cuda" if torch.cuda.is_available() else "cpu"

embedder_model = "all-MiniLM-L6-v2"

reranker_model = "cross-encoder/ms-marco-MiniLM-L6-v2"

local_llm_config = {
    "model_path_or_repo_id": "TheBloke/Mistral-7B-v0.1-GGUF",
    "model_file": "mistral-7b-v0.1.Q5_K_S.gguf",
    "model_type": "mistral",
    "gpu_layers": 20 if torch.cuda.is_available() else 0,
    "threads": 8,
    "context_length": 4096,  # The maximum context window is 4096 tokens
    "mlock": True,  # Locks the model into RAM to prevent swapping
}

local_generation_config = {
    "last_n_tokens": 128,  # The most recent of tokens that will be penalized (if it was repeated)
    "temperature": 0.3,  # Controls the randomness of output. Higher value - higher randomness
    "repetition_penalty": 1.2,
}

text_splitter_config = {
    "chunk_size": 1000,  # The maximum size of chunk
    "chunk_overlap": 100,
    "length_function": len,  # Function to measure chunk length
    "is_separator_regex": False,
    "add_start_index": True,
}

# "127.0.0.1"
api_config = {
    "app": "app.api:api",
    "host": "127.0.0.1",
    "port": 5050,
    "reload": True,  # The server will reload on system changes
}

gemini_generation_config = {
    "temperature": 0,  # deterministic, predictable output
    "top_p": 0.95,
    "top_k": 20,
    "candidate_count": 1,
    "seed": 5,
    "max_output_tokens": 1001,
    "stop_sequences": ["STOP!"],
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
}

use_gemini: bool = True

max_delta = (
    0.15  # defines what is the minimum boundary for vectors to be considered similar
)

postgres_client_config = {
    "url": os.environ["DATABASE_URL"],
    "echo": False,
}

very_secret_pepper = "goida"  # +1 point, имба
jwt_algorithm = "HS256"

max_cookie_lifetime = 3000  # in seconds

url_user_not_required = ["login", "", "viewer", "message_with_docs", "new_user"]
