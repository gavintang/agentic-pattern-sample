import operator
from typing import Annotated, Mapping

from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.types import Send, Command
from pydantic import BaseModel, Field

from glab.comm.graph_maker_langgraph import GraphNodeContext, GraphMaker
from glab.comm.library import Agent, LlmClient, AgentBuilder
from tests.comm.test_settings import llm_client

class DemoAgent(Agent):
  def __init__(self, clients: Mapping[str, LlmClient]):
    super().__init__(clients)

class DemoState(BaseModel):
  message: str
  results: Annotated[list[str], operator.add] = Field(default_factory=list)

def dispatcher_1(state: DemoState):
  print(f"dispatcher receive state: {state}\n")
  return [ "s1", "s2", "s3"]

def dispatcher_2(state: DemoState):
  print(f"dispatcher receive state: {state}\n")
  return [
    Send("worker", { "message": "worker 2"}),
    Send("worker", { "message": "worker 1"}),
    Send("worker", { "message": "worker 3"}),
  ]

def worker_1(state: DemoState):
  print(f"worker receive state: {state}\n")
  return Command(update={ "results": [ state.message ]})

def worker_2(id: str, state: DemoState):
  print(f"worker receive state: {state}\n")
  return Command(update={ "results": [ f"{id}: {state.message}" ]})

def search(state: DemoState):
  return Command(update={"results": ["google result: " + state.message]})

def test_make_graph():
  builder = StateGraph(DemoState)
  builder.add_node("search", search)
  builder.add_edge(START, "search")
  builder.add_edge("search", END)
  graph = builder.compile()
  res = graph.invoke({"message": "langgraph parallel"})
  print(res)

def test_make_graph_parallel_1():
  builder = StateGraph(DemoState)
  builder.add_node("worker1", lambda state: worker_2("w1", state))
  builder.add_node("worker2", lambda state: worker_2("w2", state))
  builder.add_node("worker3", lambda state: worker_2("w3", state))
  builder.add_conditional_edges(
    source=START,
    path=dispatcher_1,
    path_map={
      "s1": "worker1",
      "s2": "worker2",
      "s3": "worker3",
    }
  )
  builder.add_edge("worker1", END)
  builder.add_edge("worker2", END)
  builder.add_edge("worker3", END)
  graph = builder.compile()
  res = graph.invoke({"message": "langgraph parallel"})
  print(res)
  assert isinstance(res, dict)
  res_state = DemoState(**res)
  assert res_state.message == "langgraph parallel"
  assert ['w1: langgraph parallel', 'w2: langgraph parallel', 'w3: langgraph parallel'] == res_state.results

def test_make_graph_parallel_2():
  builder = StateGraph(DemoState)
  builder.add_node("worker", lambda state: worker_1(DemoState(**state)))
  builder.add_conditional_edges(START, dispatcher_2)
  builder.add_edge("worker", END)
  graph = builder.compile()
  res = graph.invoke({"message": "langgraph parallel"})
  print(res)
  assert isinstance(res, dict)
  res_state = DemoState(**res)
  assert res_state.message == "langgraph parallel"
  assert len(res_state.results) == 3
  assert ['worker 2', 'worker 1', 'worker 3'] == res_state.results

def test_make_graph_via_maker():
  agent_builder = AgentBuilder()
  agent_builder.add_client("default", llm_client())
  agent = agent_builder.build(DemoAgent)
  ctx = GraphNodeContext(agent, "hi")
  maker = GraphMaker(ctx, DemoState)
  maker.add_node("search", lambda state, _: search(state))
  maker.add_edge(START, "search")
  maker.add_edge("search", END)
  graph = maker.compile()
  res = graph.invoke({"message": "langgraph parallel"})
  res_state = DemoState(**res)
  print(res)
  assert res_state.message == "langgraph parallel"
  assert ['google result: langgraph parallel'] == res_state.results

def test_make_graph_parallel_vai_maker_1():
  agent_builder = AgentBuilder()
  agent_builder.add_client("default", llm_client())
  agent = agent_builder.build(DemoAgent)
  ctx = GraphNodeContext(agent, "hi")
  maker = GraphMaker(ctx, DemoState)
  maker.add_node("worker1", lambda state, _: worker_2("w1", state))
  maker.add_node("worker2", lambda state, _: worker_2("w2", state))
  maker.add_node("worker3", lambda state, _: worker_2("w3", state))
  maker.add_conditional_edges(
    source=START,
    route=lambda state, _: dispatcher_1(state),
    path_map={
      "s1": "worker1",
      "s2": "worker2",
      "s3": "worker3",
    }
  )
  maker.add_edge("worker1", END)
  maker.add_edge("worker2", END)
  maker.add_edge("worker3", END)
  graph = maker.compile()
  res = graph.invoke({"message": "langgraph parallel"})
  print(res)
  assert isinstance(res, dict)
  res_state = DemoState(**res)
  assert res_state.message == "langgraph parallel"
  assert ['w1: langgraph parallel', 'w2: langgraph parallel', 'w3: langgraph parallel'] == res_state.results

def test_make_graph_parallel_vai_maker_2():
  agent_builder = AgentBuilder()
  agent_builder.add_client("default", llm_client())
  agent = agent_builder.build(DemoAgent)
  ctx = GraphNodeContext(agent, "hi")
  maker = GraphMaker(ctx, DemoState)
  maker.add_node("worker", lambda state, _: worker_1(DemoState(**state)))
  maker.add_conditional_edges(START, lambda state, _: dispatcher_2(state))
  maker.add_edge("worker", END)
  graph = maker.compile()
  res = graph.invoke({"message": "langgraph parallel"})
  print(res)
  assert isinstance(res, dict)
  res_state = DemoState(**res)
  assert res_state.message == "langgraph parallel"
  assert len(res_state.results) == 3
  assert ['worker 2', 'worker 1', 'worker 3'] == res_state.results