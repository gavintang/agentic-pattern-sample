import json
from typing import Any

import pytest
from qdrant_client import models

from glab.comm.library import VdbClient
from glab.comm.vdb_client_qdrant import VdbQdrantClient
from tests.comm.test_settings import llm_ollama_bgem3

QDRANT_URL = "http://localhost:6333"

DATA_FILE = "startups_demo.json"
# COLLECTION_NAME = "startups"
COLLECTION_NAME = "tmp_startups"
DISTANCE = models.Distance.COSINE
EMBEDDING_MODEL = "bge-m3:567m"

MAX_RECORDS = 100
VECTOR_SIZE = 1024

@pytest.fixture()
def qdrant_client(request) -> VdbClient:
  client = VdbQdrantClient(
    host = QDRANT_URL,
    vector_size = VECTOR_SIZE,
    collection_name = COLLECTION_NAME,
  )
  entries = _load_text_rows()
  client.reset_collection(index_fields=["city"])
  client.import_collection(llm_ollama_bgem3(), entries)
  def teardown():
    client.delete_collection()
  request.addfinalizer(teardown)
  return client

@pytest.mark.qdrant
def test_connection():
  client = VdbQdrantClient(QDRANT_URL, 1024, COLLECTION_NAME)
  print(client.info())

@pytest.mark.llm
@pytest.mark.ollama
@pytest.mark.qdrant
def test_neural_search(qdrant_client):
  # rs = qdrant_client.neural_search(llm_ollama_bgem3(),"Invitation", city="Chicago")
  rs = qdrant_client.neural_search(llm_ollama_bgem3(),"driving occasion", city="Chicago")
  print(json.dumps(rs, indent=2))

def _load_text_rows() -> list[dict[str, Any]]:
  with open(DATA_FILE, "r", encoding="utf-8") as file:
    rows = [
      json.loads(line)
      for line in file if line.strip()
    ]
  return rows[:MAX_RECORDS] if MAX_RECORDS is not None else rows
