import torch
import logging # kind of advanced logger
import os

base_path = os.path.dirname(os.path.realpath(__file__))
                            
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
  
qdrant_client_config = {
    "host": "qdrant" if os.name == "nt" else "localhost",
    "port": 6333,

    # Note: for now it may not work

    # "grpc_port": 6334,
    # "prefer_grpc": True
}

device = "cuda" if torch.cuda.is_available() else 'cpu'

embedder_model = "all-MiniLM-L6-v2"

reranker_model = "cross-encoder/ms-marco-MiniLM-L6-v2"

llm_config = {
    "model_path_or_repo_id": "TheBloke/Mistral-7B-v0.1-GGUF",
    "model_file": "mistral-7b-v0.1.Q5_K_S.gguf",
    "model_type": "mistral",
    "gpu_layers": 20 if torch.cuda.is_available() else 0,
    "threads": 8,
    "context_length": 4096,
    "mlock": True,
}

generation_config = {
    "last_n_tokens": 128,
    "temperature": 0.3,
    "repetition_penalty": 1.2,
}

text_splitter_config = {
    "chunk_size": 1000,
    "chunk_overlap": 100,
    "length_function": len,
    "is_separator_regex": False,
    "add_start_index": True,
}

# "127.0.0.1"
api_config = {
    "app": "api:api",
    "host": "127.0.0.1",
    "port": 5050,
    "reload": True,
}