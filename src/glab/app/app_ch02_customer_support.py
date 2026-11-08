from glab.agents.agent_ch02_customer_support import CustomerSupportAgent
from glab.comm.library import Application, AgentResponse, AgentBuilder
from glab.comm.llm_client_ollama import OllamaClient
from glab.config import settings

class AppCh02CustomerSupport(Application):

  def collect_input(self) -> str:
    print(f"** Customer support chatbot (ch02: Routing) **\n")
    print(f":: Please enter customer request (Blank Line to finish):")
    print(f"e.g. What problems does your product solve? Is it suitable for our use case?")
    print(f"------\n")
    return Application.collect_multilines_input()

  def process(self, query: str) -> AgentResponse:
    _think_llm = OllamaClient(host=settings.ollama_host, model=settings.model)
    builder = AgentBuilder()
    builder.add_client("default", _think_llm)
    builder.add_client("think", _think_llm)
    return builder.build(CustomerSupportAgent).run(query)