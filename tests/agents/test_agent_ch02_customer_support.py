import json
from dataclasses import asdict

import pytest

from glab.agents.agent_ch02_customer_support import CustomerSupportAgent
from glab.comm.library import AgentBuilder
from tests.comm.test_settings import llm_client

@pytest.fixture()
def llm(): return llm_client()

@pytest.mark.llm
@pytest.mark.ollama
def test_run(llm):
  query = "What problems does your product solve? Is it suitable for our use case?"
  builder = AgentBuilder()
  builder.add_client("default", llm)
  builder.add_client("think", llm)
  agent = builder.build(CustomerSupportAgent)
  resp = agent.run(query)
  print(json.dumps(asdict(resp), indent=2, ensure_ascii=False))
  assert len(resp.messages) == 4
  assert len(resp.responses) == 2
  assert resp.token_usage.total_tokens > 0
