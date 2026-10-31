import json
from typing import Any

import pytest

from glab.comm.library import VdbClient
from tests.comm.test_settings import llm_client, qdrant_client

MODEL = "bge-m3:567m"
DATA_FILE = "tests/resource/startups_demo"
MAX_RECORDS = 100

@pytest.fixture()
def client(request) -> VdbClient:
  client = qdrant_client()
  entries = _load_text_rows()
  client.reset_collection(index_fields=["city"])
  client.import_collection(llm_client(MODEL), entries)
  def teardown():
    client.delete_collection()
  request.addfinalizer(teardown)
  return client

@pytest.mark.qdrant
def test_connection():
  client = qdrant_client()
  assert len(client.info()) > 0

@pytest.mark.llm
@pytest.mark.ollama
@pytest.mark.qdrant
def test_neural_search(client):
  rs = client.neural_search(llm_client(model=MODEL),"driving occasion", city="Chicago")
  assert len(rs) > 0

def _load_text_rows() -> list[dict[str, Any]]:
  with open(DATA_FILE, "r", encoding="utf-8") as file:
    rows = [
      json.loads(line)
      for line in file if line.strip()
    ]
  return rows[:MAX_RECORDS] if MAX_RECORDS is not None else rows
