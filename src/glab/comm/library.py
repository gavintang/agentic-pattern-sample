"""Abstract agent protocol"""
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Protocol, TypeVar, Mapping, Callable

class FinishReason(StrEnum):
  STOP = "stop"
  LENGTH = "length"
  TOOL_CALLS = "tool_calls"
  CONTENT_FILTER = "content_filter"

class Role(StrEnum):
  SYSTEM = "system"
  USER = "user"
  ASSISTANT = "assistant"

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
class LlmResponse:
  id: str
  object: str
  created: int
  model: str
  choices: list[LlmChoice]
  usage: TokenUsage
  duration: ResponseDuration | None
  def last_message(self, role: Role | None = None) -> LlmMessage | None:
    return next((m for m in reversed([c.message for c in self.choices]) if role is None or m.role == role), None)

@dataclass(frozen=True)
class AgentResponse:
  messages: tuple[LlmMessage]
  responses: tuple[LlmResponse]
  token_usage: TokenUsage
  def last_message(self, role: Role | None = None) -> LlmMessage | None:
    return next(
      (m for m in reversed(self.messages) if role is None or m.role == role), None
    )

Res = TypeVar("Res", covariant=True)
class Tool(Protocol[Res]):
  def process(self, **params: Any) -> Res: ...

@dataclass(frozen=True)
class AgentContext:
  query: str
  tool_registry: Mapping[str, Tool]
  messages: list[LlmMessage]
  def last_message(self, role: Role | None = None) -> LlmMessage | None:
    return next((m for m in reversed(self.messages) if role is None or m.role == role), None)

class LlmClient(Protocol):
  """LLM client interface"""
  def submit(self, req_id: str | None, messages: list[LlmMessage]) -> LlmResponse: ...
  def embed(self, text: str) -> Any: ...

class Skill(Protocol):
  """Agent skill interface"""
  def instructions(self, context: AgentContext) -> str: ...
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
  def neural_search(self, llm_client: LlmClient, text: str, **params) -> list[dict[str, Any] | None]: ...

class Agent(Protocol):
  def __init__(self, clients: Mapping[str, LlmClient], tool_registry: Mapping[str, Tool]):
    self.clients: Mapping[str, LlmClient] = clients
    self.tool_registry: Mapping[str, Tool] = tool_registry
  def run(self, query: str) -> AgentResponse: ...
  def _client(self, name: str) -> LlmClient:
    _default_client = self.clients.get('default')
    if _default_client is None: raise RuntimeError('default client not found')
    return self.clients.get(name) or _default_client
  def _context(self, query: str) -> AgentContext:
    return AgentContext(query, self.tool_registry, [])
  def _process_with_skill_handler(self, req_id: str, handler: SkillHandler, response_list: list[LlmResponse], context: AgentContext):
    skill, client = handler.skill, self._client(handler.client_id)
    prompt = skill.instructions(context)
    request_message: LlmMessage = LlmMessage(role=Role.SYSTEM, content=prompt)
    context.messages.append(request_message)
    response = client.submit(req_id, [request_message])
    response_list.append(response)
    response_message = response.last_message()
    if response_message is not None: context.messages.append(response_message)
  @staticmethod
  def _make_response(context: AgentContext, response_list: list[LlmResponse]) -> AgentResponse:
    token_usage = Agent.calculate_total_usage(response_list)
    return AgentResponse(tuple(context.messages), tuple(response_list), token_usage)
  @staticmethod
  def calculate_total_usage(responses: list[LlmResponse]):
    _prompt_tokens, _cached_tokens, _completion_tokens, _total_tokens = 0, 0, 0, 0
    for rsp in responses:
      _prompt_tokens += rsp.usage.prompt_tokens
      _cached_tokens += rsp.usage.cached_tokens if rsp.usage.cached_tokens is not None else 0
      _completion_tokens += rsp.usage.completion_tokens
      _total_tokens += rsp.usage.total_tokens
    return TokenUsage(_prompt_tokens, _cached_tokens, _completion_tokens, _total_tokens)

class AgentException(Exception):
  def __init__(self, message: str, name: str):
    super().__init__(message)
    self.name = name

class AgentBuilder:
  def __init__(self):
    self.clients: dict[str, LlmClient] = {}
    self.tool_registry: dict[str, Tool] = {}
  def build(self, maker: Callable[[Mapping[str, LlmClient], Mapping[str, Tool]], Agent]) -> Agent:
    _clients = MappingProxyType(self.clients)
    _tools = MappingProxyType(self.tool_registry)
    return maker(_clients, _tools)
  def add_client(self, name: str | None, client: LlmClient):
    _name = name or 'default'
    self.clients[_name] = client
  def register_tool(self, name:str, tool: Tool):
    self.tool_registry[name] = tool
