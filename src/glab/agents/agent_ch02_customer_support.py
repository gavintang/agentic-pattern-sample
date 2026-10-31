import uuid
from typing import Mapping, Literal, get_args

from glab.comm import library as lib
from glab.comm.skills import ClassifyCustomerRequestSkill, SupportPreSaleSkill, SupportPostSaleSkill, \
  SupportBusinessCooperationSkill, ForwardToHumanSupportSkill, parse_json_data

Category = Literal["pre-sale", "post-sale", "business", "unknown"]

class CustomerSupportAgent(lib.Agent):

  def __init__(self, clients: Mapping[str, lib.LlmClient], tool_registry: Mapping[str, lib.Tool]):
    super().__init__(clients, tool_registry)

  def run(self, query: str) -> lib.AgentResponse:
    route_table: dict[str, lib.SkillHandler] = {
      "pre-sale": lib.SkillHandler(skill=SupportPreSaleSkill(), client_id="think"),
      "post-sale": lib.SkillHandler(skill=SupportPostSaleSkill(), client_id="think"),
      "business": lib.SkillHandler(skill=SupportBusinessCooperationSkill(), client_id="think"),
      "unknown": lib.SkillHandler(skill=ForwardToHumanSupportSkill(), client_id="think")
    }
    return self._run_via_route(ClassifyCustomerRequestSkill(), route_table, self._context(query))

  def _run_via_route(self, detect_skill: lib.Skill, route_table: dict[str, lib.SkillHandler], context: lib.AgentContext) -> lib.AgentResponse:
    req_id = str(uuid.uuid4())
    response_list: list[lib.LlmResponse] = []
    detect_skill_handler = lib.SkillHandler(skill=detect_skill, client_id="detect")
    self._process_with_skill_handler(req_id, detect_skill_handler, response_list, context)
    detect_response_message = context.last_message()
    if detect_response_message is None: raise RuntimeError('failed to detect customer request')
    detect_rs = parse_json_data(detect_response_message.content)
    category = detect_rs["category"] if detect_rs["category"] in get_args(Category) else "unknown"
    handler = route_table[category]
    if handler is None: raise RuntimeError('failed to find skill handler')
    self._process_with_skill_handler(req_id, handler, response_list, context)
    return lib.Agent._make_response(context, response_list)
