from glab.agents.agent_ch03_feedback_analyst import FeedbackAnalystAgent
from glab.comm.library import Application, AgentResponse, AgentBuilder
from glab.comm.llm_client_ollama import OllamaClient
from glab.config import settings

class AppCh03CustomerFeedback(Application):

  def collect_input(self) -> str:
    print(f"** Customer feedback analyst (ch03: Parallelization) **\n")
    print(f":: Please enter customer feedback (Blank Line to finish):")
    print(f"e.g. My invoice shows a 'prorated adjustment' of -$4.20. What does that mean? And why is this month's total different from last month when I didn't change anything?")
    print(f"------\n")
    return Application.collect_multilines_input()

  def process(self, query: str) -> AgentResponse:
    _think_llm = OllamaClient(host=settings.ollama_host, model=settings.model)
    builder = AgentBuilder()
    builder.add_client("default", _think_llm)
    builder.add_client("think", _think_llm)
    return builder.build(FeedbackAnalystAgent).run(query)