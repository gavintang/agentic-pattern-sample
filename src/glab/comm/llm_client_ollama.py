"""Client to communicate with Local Ollama Server"""
import uuid
from datetime import datetime
from typing import Any

import requests
from ollama import ChatResponse, Client, ResponseError
from dataclasses import asdict

from glab.comm.library import (
  LlmResponse, LlmChoice, LlmMessage, TokenUsage, ResponseDuration, LlmClient, FinishReason, Role,
)

class OllamaClient(LlmClient):

  def __init__(self, host: str, model: str):
    self.host = host
    self.model = model

  def chat(self, messages: list[LlmMessage]) -> list[LlmResponse]:
    _id = str(uuid.uuid4())
    _resp = _submit_to_ollama(self.host, self.model, messages)
    return [_convert(_id, self.model, _resp)]

  def embed(self, text: str | None) -> Any:
    session = requests.Session()
    response = session.post(
      f"{self.host.rstrip('/')}/api/embed",
      json={"model": self.model, "input": text}, timeout=(10, 600)
    )
    return response.json()["embeddings"]

def _submit_to_ollama(host: str, model: str, messages: list[LlmMessage] | None = None) -> ChatResponse:
  _messages = [asdict(m) for m in (messages or [])]
  try:
    _client = Client(host=host)
    return _client.chat(model=model, messages=_messages)
  except ResponseError as e:
    detail = e.error or f"(HTTP {e.status_code}, No Content)"
    raise RuntimeError(f"Ollama request failed: {detail}") from e
  except ConnectionError as e:
    raise RuntimeError(f"Cannot connect Ollama service, please check service status.") from e

def _convert(req_id: str, model: str, response: ChatResponse) -> LlmResponse:
  _object = "chat.completion"
  _created = int(
    datetime.fromisoformat(response.created_at.replace("Z", "+00:00")).timestamp()
  ) if response.created_at else int(datetime.now().timestamp())
  _message = LlmMessage(role=Role.ASSISTANT, content=response.message.content or "")
  _finish_reason: FinishReason | None = FinishReason(response.done_reason) if response.done_reason else None
  _choices: list[LlmChoice] = [LlmChoice(index=0, message=_message, finish_reason=_finish_reason)]
  _prompt_eval_count = response.prompt_eval_count or 0
  _completion_tokens = response.eval_count or 0
  _usage = TokenUsage(
    prompt_tokens = _prompt_eval_count,
    cached_tokens = 0,
    completion_tokens = _completion_tokens,
    total_tokens = _prompt_eval_count + _completion_tokens,
  )

  _load_duration = response.load_duration or 0
  _prefill_duration = response.prompt_eval_duration or 0
  _decode_duration = response.eval_duration or 0
  _duration = ResponseDuration(
    load = _load_duration,
    prefill = _prefill_duration,
    decode = _decode_duration,
    total = _load_duration + _prefill_duration + _decode_duration
  )

  return LlmResponse(
    id=req_id, name=None, object=_object, created=_created, model=model, choices=_choices, tool_calls=None,
    usage=_usage, duration=_duration
  )

