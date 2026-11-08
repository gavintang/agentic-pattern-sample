import json
from dataclasses import asdict

import pytest

from glab.agents.agent_ch03_feedback_analyst import FeedbackAnalystAgent
from glab.comm.library import AgentBuilder, LlmMessage
from glab.comm.skills import parse_json_data
from tests.comm.test_settings import llm_client

@pytest.fixture()
def llm(): return llm_client()

@pytest.mark.llm
@pytest.mark.ollama
def test_run(llm):
  query = "order: ID4102314 application service. I've reset my password three times and it STILL says invalid credentials. This is the second week in a row. What is going on over there?"
  builder = AgentBuilder()
  builder.add_clients([("default", llm), ("think", llm)])
  agent = builder.build(FeedbackAnalystAgent)
  resp = agent.run(query)
  print(json.dumps(asdict(resp), indent=2, ensure_ascii=False))
  rs = resp.last_message()
  assert isinstance(rs, LlmMessage)
  rs_content = parse_json_data(rs.content)

  assert rs_content.get("feedback_content") == query
  assert isinstance(rs_content.get("draft_response"), str)
  assert rs_content.get("emotion") == "frustrated"
  assert rs_content["order"]["order_id"] == "ID4102314"
  assert rs_content["order"]["product"] == "application service"
  assert rs_content["order"]["service_region"] == ""
  assert rs_content["raise_to_humber"] == True
  assert isinstance(rs_content["summary"], str)
  assert isinstance(rs_content["topic"], str)
  assert isinstance(rs_content["urgency"], str)

