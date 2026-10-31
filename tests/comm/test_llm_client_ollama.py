import uuid
import pytest

from glab.comm.library import LlmMessage, LlmResponse, Role
from tests.comm.test_settings import llm_ollama_deepseekr1

@pytest.fixture()
def llm(): return llm_ollama_deepseekr1()

@pytest.mark.llm
@pytest.mark.ollama
def test_submit(llm):
  _id = str(uuid.uuid4())
  _messages = [LlmMessage(Role.USER, "who are you?")]
  rs = llm.submit(_id, _messages)
  assert isinstance(rs, LlmResponse)
  assert rs.choices[0].message.role == "assistant"
  assert isinstance(rs.choices[0].message.content, str)
  assert rs.id == _id
  print(rs)
