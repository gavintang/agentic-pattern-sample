"""
# Chapter 14: Knowledge Retrieval (RAG)
```LLMs exhibit substantial capabilities in generating human-like text. However, their knowledge base is typically
confined to the data on which they were trained, limiting their access to real-time information, specific company data,
or highly specialized details. Knowledge Retrieval (RAG, or Retrieval Augmented Generation) addresses this limitation.
RAG enables LLMs to access and integrate external, current, and context-specific information, thereby enhancing
the accuracy, relevance, and factual basis of their outputs.``` -- Agentic Design Patterns

In this demo, the agent task is to manage a knowledge library of Startup with vector database qdrant. it supports
create collection, import startup entries, add startup entry and delete collection.
"""
import json
import os
import uuid
from datetime import datetime
from typing import Mapping, Any
from glab.comm.library import Agent, LlmClient, AgentResponse, LlmResponse, ToolCall, AgentContext, LlmMessage, \
  LlmChoice, FinishReason, Role
from glab.comm.llm_client_ollama import OllamaClient
from glab.comm.skills import parse_json_data, dump_json_data
from glab.comm.vdb_client_qdrant import VdbQdrantClient
from glab.config import settings

class StartupRetrievalAgent(Agent):

  def __init__(self, clients: Mapping[str, LlmClient], collection_name: str | None = None):
    super().__init__(clients)
    self.collection_name = collection_name or "my-startup-lib"

  def run(self, query: str) -> AgentResponse:
    data = parse_json_data(query)
    cmd = data.get("cmd") or "search"
    print(f" collection name: {self.collection_name}")
    vdb_client = VdbQdrantClient(
      host=settings.qdrant_host,
      vector_size=int(settings.qdrant_vector_size),
      collection_name=self.collection_name,
    )
    context = self.context(query)
    match cmd:
      case "reset": return self._create_or_reset_collection(vdb_client, context)
      case "import": return self._import_collection_entries(vdb_client, context, data)
      case "add": return self._add_collection_entry(vdb_client, context, data)
      case "search": return self._neural_search(vdb_client, context, data)
      case "delete": return self._delete_collection(vdb_client, context)

    return self._create_or_reset_collection(vdb_client, context)

  @staticmethod
  def _create_or_reset_collection(vdb_client: VdbQdrantClient, context: AgentContext) -> AgentResponse:
    vdb_client.reset_collection(index_fields=["city"])
    resp = _make_llm_response(
      "reset-vdb-collection", context,
      llm_message=LlmMessage(Role.SYSTEM, dump_json_data({"collection": vdb_client.collection_name})),
      collection=vdb_client.collection_name, vector_size=vdb_client.vector_size
    )
    return Agent.make_response(context, [resp])

  @staticmethod
  def _import_collection_entries(vdb_client: VdbQdrantClient, context: AgentContext, data: dict[str, Any]) -> AgentResponse:
    file = data["file"]
    if file is None: raise RuntimeError("Missing collection file.")
    elif not os.path.isfile(file): raise RuntimeError(f"Invalid file name, {file}.")
    with open(file, "r", encoding="utf-8") as file:
      entries = [ json.loads(line) for line in file if line.strip() ]
    llm_embed_client = OllamaClient(host=settings.ollama_host, model=settings.embed_model)
    vdb_client.import_collection(llm_embed_client, entries)
    resp = _make_llm_response(
      "import-collection-entries", context,
      llm_message=LlmMessage(Role.SYSTEM, dump_json_data({"collection": vdb_client.collection_name, "size": len(entries)})),
      collection=vdb_client.collection_name, size=len(entries)
    )
    return Agent.make_response(context, [resp])

  @staticmethod
  def _add_collection_entry(vdb_client: VdbQdrantClient, context: AgentContext, data: dict[str, Any]) -> AgentResponse:
    llm_embed_client = OllamaClient(host=settings.ollama_host, model=settings.embed_model)
    pid = vdb_client.add_entry(llm_embed_client, data)
    resp = _make_llm_response(
      "add-collection-entry", context,
      llm_message=LlmMessage(Role.SYSTEM, dump_json_data({"collection": vdb_client.collection_name, "id": pid})),
      collection=vdb_client.collection_name, id=pid
    )
    return Agent.make_response(context, [resp])

  @staticmethod
  def _neural_search(vdb_client: VdbQdrantClient, context: AgentContext, data: dict[str, Any]) -> AgentResponse:
    city = data.get("city")
    query = data.get("query") or ""
    llm_embed_client = OllamaClient(host=settings.ollama_host, model=settings.embed_model)
    rs = vdb_client.neural_search(llm_embed_client, query, city=city)
    llm_message  = LlmMessage(Role.SYSTEM, dump_json_data({"result": rs}))
    resp = _make_llm_response(
      "neural-search", context, llm_message, city=city, query=query
    )
    return Agent.make_response(context, [resp])

  @staticmethod
  def _delete_collection(vdb_client: VdbQdrantClient, context: AgentContext) -> AgentResponse:
    vdb_client.delete_collection()
    resp = _make_llm_response(
      "delete-vdb-collection", context,
      llm_message=LlmMessage(Role.SYSTEM, dump_json_data({"collection": vdb_client.collection_name})),
      collection=vdb_client.collection_name, vector_size=vdb_client.vector_size
    )
    return Agent.make_response(context, [resp])

def _make_llm_response(name:str, context: AgentContext, llm_message: LlmMessage | None = None, **kwargs) -> LlmResponse:
  _id = str(uuid.uuid4())
  tool_call = ToolCall(
    id=_id,
    name=name,
    args=kwargs,
  )
  if llm_message is not None: context.messages.append(llm_message)
  resp = LlmResponse(
    id=_id,
    object="tool_call.success",
    created=int(datetime.now().timestamp()),
    choices=[LlmChoice(0, llm_message, FinishReason.STOP)] if llm_message else [],
    tool_calls=[tool_call]
  )
  return resp
