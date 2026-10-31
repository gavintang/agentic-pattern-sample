import json
from functools import lru_cache
from importlib.resources import files

from glab.comm.library import Skill, AgentContext, Role

class DetectLanguageSkill(Skill):
  """Skill to detect language of user input"""
  def instructions(self, context: AgentContext) -> str:
    _query=context.query
    return _render_prompt_via_template("detect-language-agent.md", user_input=_query)

class ExtractAddressInfoSkill(Skill):
  """Skill to extract address info and convert to JSON data"""
  def instructions(self, context: AgentContext) -> str:
    _msg = context.last_message(Role.ASSISTANT)
    _content = _msg.content if _msg is not None else context.query
    _address_data = parse_json_data(_content)
    _language: str = _address_data["language"]
    _template = "extract-address-info-zh.md" if _language == "zh" else "extract-address-info.md"
    _input = _address_data["input"]
    return _render_prompt_via_template(template=_template, user_input=_input)

class EvaluateAddressDataSkill(Skill):
  """Skill to evaluate address data is valid or not"""
  def instructions(self, context: AgentContext) -> str:
    _msg = context.last_message(Role.ASSISTANT)
    _content = _msg.content if _msg is not None else context.query
    return _render_prompt_via_template("evaluate-address-data.md", user_input=_content)

class ClassifyCustomerRequestSkill(Skill):
  """Skill to detect customer request"""
  def instructions(self, context: AgentContext) -> str:
    _query = context.query
    return _render_prompt_via_template("classify-customer-request.md", user_input=_query)

class SupportPreSaleSkill(Skill):
  """Skill to support pre-sale"""
  def instructions(self, context: AgentContext) -> str:
    _query = context.query
    return _render_prompt_via_template("generate-presale-support-reply.md", user_input=_query)

class SupportPostSaleSkill(Skill):
  """Skill to support post-sale"""
  def instructions(self, context: AgentContext) -> str:
    _query = context.query
    return _render_prompt_via_template("generate-postsale-support-reply.md", user_input=_query)

class SupportBusinessCooperationSkill(Skill):
  """Skill to support business cooperation"""
  def instructions(self, context: AgentContext) -> str:
    _query = context.query
    return _render_prompt_via_template("generate-business-cooperation-reply.md", user_input=_query)

class ForwardToHumanSupportSkill(Skill):
  """Skill to forward to human support"""
  def instructions(self, context: AgentContext) -> str:
    _query = context.query
    return _render_prompt_via_template("forward-to-human-support.md", user_input=_query)

def _render_prompt_via_template(template: str, **params) -> str:
  _name = template.lower()
  if not _name.endswith(".md"): _name += ".md"
  _template = _get_cached_template(_name)
  _template = "{user_input}" if _template is None else _template
  return _template.format(**params)

@lru_cache(maxsize=None)
def _get_cached_template(name: str) -> str | None:
  try:
    return (files("glab.prompts") / name).read_text(encoding="utf-8")
  except FileNotFoundError:
    return None

def parse_json_data(content: str) -> dict:
  try:
    _json = json.loads(content)
    return _json if isinstance(_json, dict) else {"list": _json} if isinstance(_json, list) else {"input": _json}
  except json.JSONDecodeError:
    return {"input": content}