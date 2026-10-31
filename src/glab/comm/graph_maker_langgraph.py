from typing import TypeVar, Callable, Hashable

from langgraph.graph import StateGraph
from langgraph.types import Command, Send

from glab.comm.library import LlmResponse, Agent, LlmClient, Skill, Role, LlmMessage

StateT = TypeVar("StateT")

ActionRespT = type[Command | list[Command] | Send | list[Send]]

class GraphNodeContext:
  def __init__(self, agent: Agent, query: str):
    self.agent: Agent = agent
    self.agent_context = agent.context(query)
    self.response_list: list[LlmResponse] = []
  def llm_client(self, name: str = "") -> LlmClient:
    return self.agent.client(name)
  def llm_chat(self, skill: Skill, client_name: str = ""):
    client: LlmClient = self.agent.client(client_name)
    self.agent.process(client, skill, self.response_list, self.agent_context)
  def last_message(self, role: Role | None = None) -> LlmMessage | None:
    return self.agent_context.last_message(role)
  def make_agent_response(self):
    return self.agent.make_response(self.agent_context, self.response_list)

class GraphMaker:
  def __init__(self, context: GraphNodeContext, state_schema: type[StateT]):
    self.agent = context.agent
    self.stateT = state_schema
    self.graph_builder = StateGraph(state_schema)
    self.context = context
  def add_node(self, node: str, action: Callable[[StateT, GraphNodeContext], Command | list[Command]]):
    self.graph_builder.add_node(node, lambda state: action(state, self.context))
  def add_edge(self, start: str, end: str):
    self.graph_builder.add_edge(start, end)
  def add_conditional_edges(
    self,
    source: str,
    route: Callable[[StateT, GraphNodeContext], Send | list[Send] | str | list[str]],
    path_map: dict[Hashable, str] | list[str] | None = None,
  ):
    self.graph_builder.add_conditional_edges(source, lambda state: route(state, self.context), path_map)
  def compile(self):
    return self.graph_builder.compile()