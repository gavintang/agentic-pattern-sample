import json
from typing import Any

import pytest

from glab.comm.library import VdbClient
from tests.comm.test_settings import qdrant_client, llm_embed_client

DATA_FILE = "tests/resource/startups_sample100"
MAX_RECORDS = 100

@pytest.fixture()
def client(request) -> VdbClient:
  client = qdrant_client()
  entries = _load_text_rows()
  client.reset_collection(index_fields=["city"])
  client.import_collection(llm_embed_client(), entries)
  def teardown():
    client.delete_collection()
  request.addfinalizer(teardown)
  return client

@pytest.mark.qdrant
def test_connection():
  client = qdrant_client()
  assert len(client.info()) > 0

@pytest.mark.qdrant
def test_add_entry(client):
  llm = llm_embed_client()
  pid = client.add_entry(llm, {
    "alt": "Lemonade -  sales and marketing location based services social commerce shopping",
    "city": "New York",
    "description": "Set up shop\nLemonade let's you set up shop where ever you are, whether it's on the street or at your doorstep. It's like the good old days when you opened up a Lemonade stand. Your shop information is advertised on a map so that everyone can find you. Anything from food carts ...",
    "images": "https://d1qb2nb5cznatu.cloudfront.net/startups/i/481431-0af6937d4bfc7e0869c52394f64735c2-thumb_jpg.jpg?buster=1409968372",
    "link": "https://www.lemonadeapp.us",
    "name": "Lemonade"
  })
  assert pid is not None

@pytest.mark.llm
@pytest.mark.ollama
@pytest.mark.qdrant
def test_neural_search(client):
  rs = client.neural_search(llm_embed_client(),"Freelancers developers", city="Hong Kong")
  assert len(rs) > 0

def _load_text_rows() -> list[dict[str, Any]]:
  with open(DATA_FILE, "r", encoding="utf-8") as file:
    rows = [
      json.loads(line)
      for line in file if line.strip()
    ]
  return rows[:MAX_RECORDS] if MAX_RECORDS is not None else rows
