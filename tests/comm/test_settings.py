from typing import Sequence, Callable, Any

from glab.comm.library import LlmClient, VdbClient
from glab.comm.llm_client_langchain import LangchainAgent
from glab.comm.llm_client_ollama import OllamaClient
from glab.comm.vdb_client_qdrant import VdbQdrantClient
from glab.config import settings

def llm_client(model: str | None = None) -> LlmClient:
  ollama_host = settings.ollama_host
  ollama_model = model or settings.model
  return OllamaClient(host=ollama_host, model=ollama_model)

def llm_embed_client(model: str | None = None) -> LlmClient:
  ollama_host = settings.ollama_host
  ollama_model = model or settings.embed_model
  return OllamaClient(host=ollama_host, model=ollama_model)

def qdrant_client(collection_name: str | None = None, qdrant_vector_size: int | None = None) -> VdbClient:
  return VdbQdrantClient(
    host=settings.qdrant_host,
    vector_size=qdrant_vector_size or int(settings.qdrant_vector_size),
    collection_name=collection_name or "my_temp_collection",
  )

def langchain_ollama(model: str | None = None, tools: Sequence[Callable[..., Any] | dict[str, Any]] | None= None) -> LangchainAgent:
  ollama_host = settings.ollama_host
  ollama_model = model or settings.model
  return LangchainAgent(
    llm_type="ollama", host=ollama_host, temperature=0, model=ollama_model, tools=tools or []
  )
