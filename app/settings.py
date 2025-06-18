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
    "host": "localhost",
    "port": 6333,
}

device = "cuda" if torch.cuda.is_available() else 'cpu'

embedder_model = "all-MiniLM-L6-v2"

reranker_model = "cross-encoder/ms-marco-MiniLM-L6-v2"

local_llm_config = {
    "model_path_or_repo_id": "TheBloke/Mistral-7B-v0.1-GGUF",
    "model_file": "mistral-7b-v0.1.Q5_K_S.gguf",
    "model_type": "mistral",
    "gpu_layers": 20 if torch.cuda.is_available() else 0,
    "threads": 8,
    "context_length": 4096,
    "mlock": True,
}

local_generation_config = {
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
    "app": "app.api:api",
    "host": "127.0.0.1",
    "port": 5050,
    "reload": True,
}

gemini_generation_config = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 20,
    "candidate_count": 1,
    "seed": 5,
    "max_output_tokens": 100,
    "stop_sequences": ['STOP!'],
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
}

use_gemini: bool = False

max_delta = 0.15 # defines what is the minimum boundary for vectors to be considered similar


# for postgres client
# Note: you should run postgres server with similar host, post, and do not forget to create a user with similar settings
host = "localhost"
port = 5432
user = "postgres"
password = "1121"
dbname = "exp"

postgers_client_config = {
    "url": f"postgresql://{user}:{password}@{host}:{port}/{dbname}",
    "echo": False,
}

very_secret_pepper = "goida"
jwt_algorithm = "HS256"