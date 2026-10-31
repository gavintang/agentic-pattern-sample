"""
# Chapter 1: Prompt Chain
```Routing introduces conditional logic into an agent's operational framework, enabling a shift from a fixed execution path
to a model where the agent dynamically evaluates specific criteria to select from a set of possible subsequent actions.
This allows for more flexible and context-aware system behavior.``` -- Agentic Design Patterns

In this demo, the task to convert the plain address text input by user to 3 subtasks, detect-language,
extract-address-to-json, and evaluate-address-data. Each subtask can be processed by different LLM.
"""

from typing import Mapping

import glab.comm.library as lib
from glab.comm.skills import DetectLanguageSkill, ExtractAddressInfoSkill, EvaluateAddressDataSkill

class AddressInfoAgent(lib.Agent):

  def __init__(self, clients: Mapping[str, lib.LlmClient]):
    super().__init__(clients)

  def run(self, query: str) -> lib.AgentResponse:
    """Building prompt chain and process"""
    chain: list[lib.SkillHandler] = [
      lib.SkillHandler(skill=DetectLanguageSkill(), client_id="default"),
      lib.SkillHandler(skill=ExtractAddressInfoSkill(), client_id="think"),
      lib.SkillHandler(skill=EvaluateAddressDataSkill(), client_id="review"),
    ]
    return self._run_in_sequence(chain, self.context(query))

  def _run_in_sequence(self, chain: list[lib.SkillHandler], context: lib.AgentContext):
    response_list: list[lib.LlmResponse] = []
    for handler in chain:
      self._process_with_skill_handler(handler, response_list, context)
    return lib.Agent.make_response(context, response_list)
