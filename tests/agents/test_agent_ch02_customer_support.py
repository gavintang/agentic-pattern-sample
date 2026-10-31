import json
from dataclasses import asdict

import pytest

from glab.agents.agent_ch02_customer_support import CustomerSupportAgent
from glab.comm.library import AgentBuilder
from tests.comm.test_settings import llm_ollama_gemma4, llm_ollama_deepseekr1

@pytest.fixture()
def llm_gemma(): return llm_ollama_gemma4()

@pytest.fixture()
def llm_deepseek(): return llm_ollama_deepseekr1()

@pytest.mark.llm
@pytest.mark.ollama
def test_run(llm_gemma, llm_deepseek):
  query = "What problems does your product solve? Is it suitable for our use case?"
  builder = AgentBuilder()
  builder.add_client("default", llm_gemma)
  builder.add_client("think", llm_gemma)
  agent = builder.build(CustomerSupportAgent)
  resp = agent.run(query)
  print(json.dumps(asdict(resp), indent=2, ensure_ascii=False))
  assert len(resp.messages) == 4
  assert len(resp.responses) == 2
  assert resp.token_usage.total_tokens > 0
