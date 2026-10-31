"""Client to communicate with LLM Server through langchain wrapper"""
from dataclasses import asdict
from datetime import datetime
from typing import Any, Sequence, Callable, Literal

from langchain.agents import create_agent
from langchain_ollama import ChatOllama, OllamaEmbeddings

from glab.comm.library import LlmClient, LlmMessage, LlmResponse, Role, FinishReason, LlmChoice, \
  TokenUsage, ResponseDuration, ToolCall

LlmType = Literal["ollama", "gemini"]

class LangchainAgent(LlmClient):

  def __init__(
    self,
    llm_type: LlmType, host: str, temperature: float | int, model: str,
    tools: Sequence[Callable[..., Any] | dict[str, Any]]
  ):
    self.proxy = ChatOllama(model=model, temperature=temperature, base_url=host)
    self.embeddings = OllamaEmbeddings(model=model, temperature=temperature, base_url=host)
    self.tools = tools
    match llm_type:
      case "gemini":
        raise NotImplementedError()

  def chat(self, messages: list[LlmMessage]) -> list[LlmResponse]:
    agent = create_agent(model=self.proxy, tools=self.tools)
    result = agent.invoke({"messages": [asdict(msg) for msg in messages]})
    result_messages = [m.model_dump() for m in result["messages"]]
    all_responses = [_convert(rs) for rs in result_messages]
    return [rs for idx, rs in enumerate(all_responses) if idx > 0 or rs.object != "chat"]

  def embed(self, text: str | None) -> Any:
    if text is None: return []
    return self.embeddings.embed_documents([text])

def _convert(rs: dict[str, Any]) -> LlmResponse:
  _id = rs.get("id") or ""
  _name = rs.get("name")
  _tool_call_id: str | None = rs.get("tool_call_id")
  _status: str = rs.get("status") or "error"
  _content: str = rs.get("content") or ""

  _tool_calls = None
  if rs.get("tool_calls") is not None:
    _tool_calls = [
      ToolCall(
        id=call.get("id"),
        name=call.get("name") or "",
        args=call.get("args") or {}
      ) for call in rs.get("tool_calls") or []
    ] if rs.get("tool_calls") else []

  _type: str = rs["type"] if rs["type"] else ""
  match _type:
    case "human":
      _role = Role.USER
      _object = "chat"
    case "ai":
      _role = Role.ASSISTANT
      _object = "chat.completion" if _tool_calls is None or len(_tool_calls) == 0 else "tool_call"
    case "tool":
      _role = Role.TOOL
      _object = f"tool_call.{_status}" if _tool_call_id is not None and _status is not None else "tool_call.failure"
    case _:
      raise RuntimeError(f"unexpected type: {_type}")
  _message = LlmMessage(role=_role, content=_content)

  _response_metadata: dict[str, Any] = rs.get("response_metadata") or {}
  if _response_metadata is not None:
    _created_timestamp = _response_metadata.get("created_at") or ""
    _created = int(datetime.fromisoformat(_created_timestamp.replace("Z", "+00:00")).timestamp()) if len(_created_timestamp) > 0 else int(datetime.now().timestamp())
    _finish_reason: FinishReason | None = FinishReason(_response_metadata.get("done_reason")) if _response_metadata.get("done_reason") else None
    _choices: list[LlmChoice] = [LlmChoice(index=0, message=_message, finish_reason=_finish_reason)]
    _prompt_eval_count = _response_metadata.get("prompt_eval_count") or 0
    _prefill_duration = _response_metadata.get("prompt_eval_duration") or 0
    _decode_duration = _response_metadata.get("eval_duration") or 0
    _load_duration = _response_metadata.get("load_duration") or 0
    _total_duration = _response_metadata.get("total_duration") or 0
    _model = _response_metadata.get("model") or ""

    _duration = None
    if _total_duration > 0:
      _duration = ResponseDuration(
        load=_load_duration,
        prefill=_prefill_duration,
        decode=_decode_duration,
        total=_total_duration
      )

  _usage_metadata: dict[str, Any] | None = rs.get("usage_metadata") or None
  _usage = None
  if _usage_metadata is not None:
    _output_tokens: int = _usage_metadata.get("output_tokens") or 0
    _total_tokens: int = _usage_metadata.get("total_tokens") or 0
    _usage = TokenUsage(
      prompt_tokens = _prompt_eval_count or 0,
      cached_tokens = 0,
      completion_tokens = _output_tokens,
      total_tokens = _total_tokens,
    )

  return LlmResponse(
    id=_id, name=_name, object=_object, created=_created, model=_model, choices=_choices, tool_calls=_tool_calls,
    usage=_usage, duration=_duration
  )