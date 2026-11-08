"""
# Chapter 3: Parallelization
```Parallelization involves executing multiple components, such as LLM calls, tool usages, or even entire sub-agents,
concurrently. Instead of waiting for one step to complete before starting the next, parallel execution
allows independent tasks to run at the same time, significantly reducing the overall execution time for tasks
that can be broken down into independent parts.``` -- Agentic Design Patterns

In this demo, the agent task is to analysis customer feedback, it will classify customer emotion, content urgency and
extract order info parallely, and then compose feedback reply or escalate to human based on the information in feedback.
Using LangGraph to manage the workflow of agentics.
"""

from typing import Mapping, Literal

from langgraph.constants import START, END
from langgraph.types import Command, Send
from pydantic import BaseModel

from glab.comm.graph_maker_langgraph import GraphMaker, GraphNodeContext
from glab.comm.library import LlmClient, Role, Agent, AgentResponse, LlmMessage
from glab.comm.skills import ClassifyFeedbackIntentSkill, ClassifyFeedbackUrgencySkill, parse_json_data, \
  ForwardToHumanSupportSkill, ComposeFeedbackReplySkill, ExtractOrderInfoSkill, dump_json_data

class OrderState(BaseModel):
  order_id: str
  product: str
  service_region: str

class FeedbackAgentState(BaseModel):
  feedback_content: str
  emotion: Literal["neutral", "grateful", "satisfied", "confused", "disappointed", "frustrated"] | None = None
  urgency: Literal["low", "medium", "high", "critical"] | None = None
  topic: str | None = None
  summary: str | None = None
  order: OrderState | None = None
  draft_response: str | None = None
  raise_to_humber: bool = False

def parse_feedback_content(state: FeedbackAgentState):
  return [
    Send("classify_emotion", state),
    Send("classify_urgency", state),
    Send("extract_order_info", state)
  ]

def classify_feedback_emotion(_state: FeedbackAgentState, context: GraphNodeContext):
  context.llm_chat(ClassifyFeedbackIntentSkill(), "think")
  message = context.last_message(Role.ASSISTANT)
  if message is None: raise RuntimeError('failed to classify feedback emotion')
  rs = parse_json_data(message.content)
  update = {
    "emotion": f"{rs.get('emotion') or 'neutral'}",
    "topic": f"{rs.get('topic') or ''}",
    "summary": f"{rs.get('summary') or ''}",
  }
  return Command(goto="evaluate_reply_action", update=update)

def classify_feedback_urgency(_state: FeedbackAgentState, context: GraphNodeContext):
  context.llm_chat(ClassifyFeedbackUrgencySkill(), "think")
  message = context.last_message(Role.ASSISTANT)
  if message is None: raise RuntimeError('failed to classify feedback urgency')
  rs = parse_json_data(message.content)
  update = {
    "urgency": f"{rs.get('urgency') or 'medium'}"
  }
  return Command(goto="evaluate_reply_action", update=update)

def extract_order_info(_state: FeedbackAgentState, context: GraphNodeContext):
  context.llm_chat(ExtractOrderInfoSkill(), "think")
  message = context.last_message(Role.ASSISTANT)
  if message is None: raise RuntimeError('failed to extract order info')
  rs = parse_json_data(message.content)
  order = {
    "order_id": f"{rs.get('order_id') or ''}",
    "product": f"{rs.get('product') or ''}",
    "service_region": f"{rs.get('service_region') or ''}",
  }
  return Command(goto="evaluate_reply_action", update={"order": order})

def evaluate_reply_action(state: FeedbackAgentState):
  _emotion = state.emotion
  _urgency = state.urgency
  if _emotion in ["disappointed", "frustrated"] or _urgency in ["critical"]:
    return Command(goto="escalate_to_human", update=state)
  else:
    return Command(goto="compose_feedback_reply")

def escalate_to_human(_state: FeedbackAgentState, context: GraphNodeContext):
  context.llm_chat(ForwardToHumanSupportSkill(), "think")
  message = context.last_message(Role.ASSISTANT)
  if message is None: raise RuntimeError('failed to escalate to human')
  rs = parse_json_data(message.content)
  update = {
    "draft_response": rs.get("reply") or "",
    "raise_to_humber": True
  }
  return Command(update=update)

def compose_feedback_reply(state: FeedbackAgentState, context: GraphNodeContext):
  order_id = state.order.order_id if state.order else ""
  product = state.order.product if state.order else ""
  service_region = state.order.service_region if state.order else ""
  feedback = state.feedback_content or ""
  skill = ComposeFeedbackReplySkill(
    feedback=feedback, emotion=state.emotion, order_id=order_id, product=product, service_region=service_region,
  )
  context.llm_chat(skill, "think")
  message = context.last_message(Role.ASSISTANT)
  if message is None: raise RuntimeError('failed to compose feedback reply')
  rs = parse_json_data(message.content)
  update = {
    "draft_response": rs.get("reply") or ""
  }
  return Command(update=update)

class FeedbackAnalystAgent(Agent):

  def __init__(self, clients: Mapping[str, LlmClient]):
    super().__init__(clients)

  def run(self, query: str) -> AgentResponse:
    context = GraphNodeContext(self, query)
    maker = GraphMaker(context, FeedbackAgentState)
    maker.add_node("classify_emotion", classify_feedback_emotion)
    maker.add_node("classify_urgency", classify_feedback_urgency)
    maker.add_node("extract_order_info", extract_order_info)
    maker.add_node("evaluate_reply_action", lambda state, ctx: evaluate_reply_action(state))
    maker.add_node("escalate_to_human", escalate_to_human)
    maker.add_node("compose_feedback_reply", compose_feedback_reply)

    maker.add_conditional_edges(
      START, lambda state, ctx: parse_feedback_content(state)
    )
    maker.add_edge("evaluate_reply_action", END)

    graph = maker.compile()
    result = graph.invoke({"feedback_content": query})
    resp_message = LlmMessage(Role.SYSTEM, dump_json_data(result))
    context.agent_context.messages.append(resp_message)
    return context.make_agent_response()
