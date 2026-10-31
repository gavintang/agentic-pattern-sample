import pytest

from glab.comm.library import LlmMessage, Role, LlmResponse
from tests.comm.test_settings import langchain_ollama

def get_weather(city: str) -> str:
  """Get weather for a given city."""
  print("calling get_weather")
  return f"It's always sunny in {city}!"

@pytest.fixture()
def llm(): return langchain_ollama()

@pytest.mark.llm
@pytest.mark.ollama
def test_submit(llm):
  _messages = [LlmMessage(Role.USER, "who are you?")]
  resp_list = llm.chat(_messages)
  assert len(resp_list) == 1
  rs = resp_list[0]
  assert isinstance(rs, LlmResponse)
  assert len(rs.choices) == 1
  assert rs.choices[0].message.role == "assistant"
  assert isinstance(rs.choices[0].message.content, str)
  assert rs.id is not None

@pytest.mark.llm
@pytest.mark.ollama
def test_run():
  llm = langchain_ollama(tools = [get_weather])
  _messages = [LlmMessage(Role.SYSTEM, "You are a helpful assistant. Don't call tool twice")]
  _messages = [LlmMessage(Role.USER, "How is the weather in San Francisco?")]
  resp_list = llm.chat(_messages)
  assert len(resp_list) == 3
  assert resp_list[0].object == "tool_call"
  assert resp_list[1].object == "tool_call.success"
  assert resp_list[2].object == "chat.completion"