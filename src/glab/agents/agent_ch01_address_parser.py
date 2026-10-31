"""
# Chapter 1: Prompt Chain
Prompt chain provides a powerful framework for large language models by decomposing complex problems into a sequence
of simpler, more manageable subtasks.

In this demo, the task to convert the plain address text input by user to 3 subtasks, detect-language,
extract-address-to-json, and evaluate-address-data. Each subtask can be processed by different LLM.
"""
import uuid
from typing import Mapping

import glab.comm.library as lib
from glab.comm.skills import DetectLanguageSkill, ExtractAddressInfoSkill, EvaluateAddressDataSkill

class AddressInfoAgent(lib.Agent):

  def __init__(self, clients: Mapping[str, lib.LlmClient], tool_registry: Mapping[str, lib.Tool]):
    super().__init__(clients, tool_registry)

  def run(self, query: str) -> lib.AgentResponse:
    """Building prompt chain and process"""
    chain: list[lib.SkillHandler] = [
      lib.SkillHandler(skill=DetectLanguageSkill(), client_id="default"),
      lib.SkillHandler(skill=ExtractAddressInfoSkill(), client_id="think"),
      lib.SkillHandler(skill=EvaluateAddressDataSkill(), client_id="review"),
    ]
    return self._run_in_sequence(chain, self._context(query))

  def _run_in_sequence(self, chain: list[lib.SkillHandler], context: lib.AgentContext):
    req_id = str(uuid.uuid4())
    response_list: list[lib.LlmResponse] = []
    for handler in chain:
      self._process_with_skill_handler(req_id, handler, response_list, context)
    return lib.Agent._make_response(context, response_list)
