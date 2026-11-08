import json
from dataclasses import asdict

import pytest
from glab.agents.agent_ch14_startup_retrieval import StartupRetrievalAgent
from glab.comm.library import AgentBuilder, LlmClient, LlmMessage, Role, Agent
from glab.comm.skills import parse_json_data, dump_json_data
from tests.comm.test_settings import llm_embed_client

COLLECTION = "my_temp_collection"

@pytest.fixture()
def llm(request) -> LlmClient:
  return llm_embed_client()

@pytest.fixture()
def agent(llm) -> Agent:
  builder = AgentBuilder()
  builder.add_client("default", llm)
  return builder.build(lambda clients: StartupRetrievalAgent(clients, COLLECTION))

@pytest.fixture()
def _setup(request, agent):
  q1 = f'{{"cmd": "reset"}}'
  agent.run(q1)
  def teardown():
    q2 = f'{{"cmd": "delete"}}'
    agent.run(q2)
  request.addfinalizer(teardown)

@pytest.mark.qdrant
def test_run_reset_collection(agent):
  query = f'{{"cmd": "reset"}}'
  resp = agent.run(query)
  print(json.dumps(asdict(resp), indent=2, ensure_ascii=False))
  llm_message = resp.last_message(Role.SYSTEM)
  assert isinstance(llm_message, LlmMessage)
  rs = parse_json_data(llm_message.content)
  assert rs["collection"] == "my_temp_collection"

@pytest.mark.llm
@pytest.mark.ollama
@pytest.mark.qdrant
def test_import_collection_entries(_setup, agent):
  query = f'{{"cmd": "import", "collection": "{COLLECTION}", "file": "./tests/resource/startups_sample100"}}'
  resp = agent.run(query)
  print(json.dumps(asdict(resp), indent=2, ensure_ascii=False))
  llm_message = resp.last_message()
  assert isinstance(llm_message, LlmMessage)
  rs = parse_json_data(llm_message.content)
  assert rs["collection"] == "my_temp_collection"
  assert rs["size"] == int("100")

  query = f'{{"cmd": "search", "collection": "{COLLECTION}", "query": "reinvent education"}}'
  resp = agent.run(query)
  print(json.dumps(asdict(resp), indent=2, ensure_ascii=False))
  msg = resp.last_message()
  assert isinstance(msg, LlmMessage)
  assert msg.role == Role.SYSTEM
  rs = parse_json_data(msg.content)
  assert isinstance(rs["result"], list)
  assert len(rs["result"]) > 1

@pytest.mark.llm
@pytest.mark.ollama
@pytest.mark.qdrant
def test_add_collection_entry(_setup, agent):
  query = dump_json_data({
    "cmd": "add",
    "collection": f"{COLLECTION}",
    "name": "TLE",
    "alt": "TLE -  manufacturing ventures for good small and medium businesses Journalists, not-for-profit, SMEs, and other professional content providers",
    "city": "Sydney",
    "description": "Real time Logistics Optimisation. \nThe world has more than enough food to end hunger. The problem is getting the surplus from those who have it to those who need it.\nIt’s a problem of logistics.\nFoodbank Local connects donors with excess food to welfare agencies who then convert it into meals. ...",
    "images": "https://d1qb2nb5cznatu.cloudfront.net/startups/i/498048-33ee6a41550e46bd21fe9c9ee13868ae-thumb_jpg.jpg?buster=1411980232",
    "link": "http://Foodbanklocal.com"
  })
  resp = agent.run(query)
  print(json.dumps(asdict(resp), indent=2, ensure_ascii=False))
  llm_message = resp.last_message()
  assert isinstance(llm_message, LlmMessage)
  rs = parse_json_data(llm_message.content)
  assert rs["collection"] == "my_temp_collection"
  assert isinstance(rs["id"], int)
