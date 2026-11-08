"""Abstract agent protocol"""
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Protocol, Mapping, Callable, Sequence

class FinishReason(StrEnum):
  STOP = "stop"
  LENGTH = "length"
  TOOL_CALLS = "tool_calls"
  CONTENT_FILTER = "content_filter"

class Role(StrEnum):
  SYSTEM = "system"
  USER = "user"
  ASSISTANT = "assistant"
  TOOL = "tool"

@dataclass(frozen=True)
class LlmMessage:
  role: Role
  content: str

@dataclass(frozen=True)
class LlmChoice:
  index: int
  message: LlmMessage
  finish_reason: FinishReason | None

@dataclass(frozen=True)
class LlmRequest:
  id: str
  model: str
  messages: list[LlmMessage]

@dataclass(frozen=True)
class TokenUsage:
  prompt_tokens: int
  cached_tokens: int | None
  completion_tokens: int
  total_tokens: int

@dataclass(frozen=True)
class ResponseDuration:
  load: int
  prefill: int
  decode: int
  total: int

@dataclass(frozen=True)
class ToolCall:
  id: str | None
  name: str
  args: dict[str, Any]

@dataclass(frozen=True)
class LlmResponse:
  id: str
  name: str | None = None
  object: str = "chat"
  created: int | None = None
  model: str | None = None
  choices: list[LlmChoice] = field(default_factory=list)
  tool_calls: list[ToolCall] | None  = None
  usage: TokenUsage | None  = None
  duration: ResponseDuration | None  = None
  def last_message(self, role: Role | None = None) -> LlmMessage | None:
    return next((m for m in reversed([c.message for c in self.choices]) if role is None or m.role == role), None)

@dataclass(frozen=True)
class AgentResponse:
  messages: Sequence[LlmMessage]
  responses: Sequence[LlmResponse]
  token_usage: TokenUsage
  def last_message(self, role: Role | None = None) -> LlmMessage | None:
    return next(
      (m for m in reversed(self.messages) if role is None or m.role == role), None
    )

@dataclass
class AgentContext:
  query: str
  messages: list[LlmMessage]
  def last_message(self, role: Role | None = None) -> LlmMessage | None:
    return next((m for m in reversed(self.messages) if role is None or m.role == role), None)

class LlmClient(Protocol):
  """LLM client interface"""
  def chat(self, messages: list[LlmMessage]) -> list[LlmResponse]: ...
  def embed(self, text: str) -> list[list[float | int]]: ...

class Skill(Protocol):
  """Agent skill interface"""
  def instructions(self, context: AgentContext | None = None, query: str | None = None) -> str: ...
  def run(self, context: AgentContext, client: LlmClient) -> LlmResponse:
    raise NotImplementedError()

@dataclass(frozen=True)
class SkillHandler:
  skill: Skill
  client_id: str

class VdbClient(Protocol):
  """Neural search interface"""
  def info(self) -> str: ...
  def reset_collection(self, index_fields: list[str]): ...
  def delete_collection(self): ...
  def import_collection(self, llm_client: LlmClient, entries: list[dict[str, Any]]): ...
  def add_entry(self, llm_client: LlmClient, entry: dict[str, Any]) -> int | str | None: ...
  def neural_search(self, llm_client: LlmClient, text: str, **params) -> list[dict[str, Any] | None]: ...

class Agent(Protocol):
  def __init__(self, clients: Mapping[str, LlmClient]):
    self.clients: Mapping[str, LlmClient] = clients
  def run(self, query: str) -> AgentResponse: ...
  def process(self, client: LlmClient, skill: Skill, response_list: list[LlmResponse], context: AgentContext):
    self._process_with_skill(client, skill, response_list, context)
  def client(self, name: str) -> LlmClient:
    _default_client = self.clients.get('default')
    if _default_client is None: raise RuntimeError('default client not found')
    return self.clients.get(name) or _default_client
  def context(self, query: str) -> AgentContext:
    return AgentContext(query, [])
  def _process_with_skill_handler(self, handler: SkillHandler, response_list: list[LlmResponse], context: AgentContext):
    client = self.client(handler.client_id)
    skill = handler.skill
    self._process_with_skill(client, skill, response_list, context)
  @staticmethod
  def _process_with_skill(client: LlmClient, skill: Skill, response_list: list[LlmResponse], context: AgentContext):
    prompt = skill.instructions(context)
    request_message: LlmMessage = LlmMessage(role=Role.SYSTEM, content=prompt)
    context.messages.append(request_message)
    response = client.chat([request_message])
    for r in response:
      response_list.append(r)
      response_message = r.last_message()
      if response_message is not None:
        context.messages.append(response_message)
  @staticmethod
  def make_response(context: AgentContext, response_list: list[LlmResponse]) -> AgentResponse:
    token_usage = Agent.calculate_total_usage(response_list)
    return AgentResponse(context.messages, response_list, token_usage)
  @staticmethod
  def calculate_total_usage(responses: list[LlmResponse]):
    _prompt_tokens, _cached_tokens, _completion_tokens, _total_tokens = 0, 0, 0, 0
    for rsp in responses:
      if rsp.usage:
        _prompt_tokens += rsp.usage.prompt_tokens
        _cached_tokens += rsp.usage.cached_tokens or 0
        _completion_tokens += rsp.usage.completion_tokens
        _total_tokens += rsp.usage.total_tokens
    return TokenUsage(_prompt_tokens, _cached_tokens, _completion_tokens, _total_tokens)

class FlowGraph(Protocol):
  def setup(self): ...
  def add_node(self, node: Callable): ...
  def add_edge(self, from_node: str, to_node: str): ...
  def compile(self): ...
  def run(self, messages: list[LlmMessage]): ...

class AgentException(Exception):
  def __init__(self, message: str, name: str):
    super().__init__(message)
    self.name = name

class AgentBuilder:
  def __init__(self):
    self.clients: dict[str, LlmClient] = {}
  def build(self, maker: Callable[[Mapping[str, LlmClient]], Agent]) -> Agent:
    _clients = MappingProxyType(self.clients)
    return maker(_clients)
  def add_client(self, name: str | None, client: LlmClient):
    self.clients[name or 'default'] = client
  def add_clients(self, clients: list[tuple[str | None, LlmClient]]):
    for name, client in clients:
      self.clients[name or "default"] = client

class Application(Protocol):
  def collect_input(self) -> str: ...
  def process(self, query: str) -> AgentResponse: ...
  @staticmethod
  def collect_multilines_input() -> str:
    lst = []
    while True:
      tmp = input()
      if tmp.strip() == "":
        break
      lst.append(tmp)
    return "\n".join(ln for ln in lst if len(ln) > 0)
