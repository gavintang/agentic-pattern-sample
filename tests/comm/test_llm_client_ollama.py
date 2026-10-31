import pytest

from glab.comm.library import LlmMessage, LlmResponse, Role
from tests.comm.test_settings import llm_client

@pytest.fixture()
def llm(): return llm_client()

@pytest.mark.llm
@pytest.mark.ollama
def test_submit(llm):
  _messages = [LlmMessage(Role.USER, "who are you?")]
  resp_list = llm.chat(_messages)
  assert len(resp_list) == 1
  rs = resp_list[0]
  assert isinstance(rs, LlmResponse)
  assert rs.choices[0].message.role == "assistant"
  assert isinstance(rs.choices[0].message.content, str)
  assert rs.id is not None
  print(rs)
