import json
from dataclasses import asdict

import pytest

from glab.agents.agent_ch01_address_parser import AddressInfoAgent
from glab.comm.library import AgentBuilder
from tests.comm.test_settings import llm_client

@pytest.fixture()
def llm(): return llm_client()

@pytest.mark.llm
@pytest.mark.ollama
def test_run(llm):
  query = "Duane Reipold, 360 Rainbow Blvd, Niagara Falls, NY 14303, United States"
  builder = AgentBuilder()
  builder.add_client("default", llm)
  builder.add_client("think", llm)
  builder.add_client("review", llm)
  agent = builder.build(AddressInfoAgent)
  resp = agent.run(query)
  print(json.dumps(asdict(resp), indent=2, ensure_ascii=False))
  assert len(resp.messages) == 6
  assert len(resp.responses) == 3
  assert resp.token_usage.total_tokens > 0
