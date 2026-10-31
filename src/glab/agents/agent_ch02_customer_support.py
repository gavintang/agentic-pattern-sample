"""
# Chapter 2: Routing
```Prompt chaining, sometimes referred to as Pipeline pattern, represents a powerful paradigm for handling intricate tasks
when leveraging large language models (LLMs). Rather than expecting an LLM to solve a complex problem in a single,
monolithic step, prompt chaining advocates for a divide-and-conquer strategy. The core idea is to break down the original,
daunting problem into a sequence of smaller, more manageable sub-problems.``` -- Agentic Design Patterns

In this demo, the task to support customer as an online chatbot, it will classify customer's request (pre-sale, post-sale,
business, unknown) and then route the request to various sub agentics to generate response to customer.
"""

from typing import Mapping, Literal, get_args

from glab.comm import library as lib
from glab.comm.skills import ClassifyCustomerRequestSkill, SupportPreSaleSkill, SupportPostSaleSkill, \
  SupportBusinessCooperationSkill, ForwardToHumanSupportSkill, parse_json_data

Category = Literal["pre-sale", "post-sale", "business", "unknown"]

class CustomerSupportAgent(lib.Agent):

  def __init__(self, clients: Mapping[str, lib.LlmClient]):
    super().__init__(clients)

  def run(self, query: str) -> lib.AgentResponse:
    route_table: dict[str, lib.SkillHandler] = {
      "pre-sale": lib.SkillHandler(skill=SupportPreSaleSkill(), client_id="think"),
      "post-sale": lib.SkillHandler(skill=SupportPostSaleSkill(), client_id="think"),
      "business": lib.SkillHandler(skill=SupportBusinessCooperationSkill(), client_id="think"),
      "unknown": lib.SkillHandler(skill=ForwardToHumanSupportSkill(), client_id="think")
    }
    return self._run_via_route(ClassifyCustomerRequestSkill(), route_table, self.context(query))

  def _run_via_route(self, detect_skill: lib.Skill, route_table: dict[str, lib.SkillHandler], context: lib.AgentContext) -> lib.AgentResponse:
    response_list: list[lib.LlmResponse] = []
    detect_skill_handler = lib.SkillHandler(skill=detect_skill, client_id="detect")
    self._process_with_skill_handler(detect_skill_handler, response_list, context)
    detect_response_message = context.last_message()
    if detect_response_message is None: raise RuntimeError('failed to detect customer request')
    detect_rs = parse_json_data(detect_response_message.content)
    category = detect_rs["category"] if detect_rs["category"] in get_args(Category) else "unknown"
    handler = route_table[category]
    if handler is None: raise RuntimeError('failed to find skill handler')
    self._process_with_skill_handler(handler, response_list, context)
    return lib.Agent.make_response(context, response_list)
