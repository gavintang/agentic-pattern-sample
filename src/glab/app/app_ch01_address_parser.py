from glab.agents.agent_ch01_address_parser import AddressInfoAgent
from glab.comm.library import Application, AgentResponse, AgentBuilder
from glab.comm.llm_client_ollama import OllamaClient
from glab.config import settings

class AppCh01AddressParser(Application):

  def collect_input(self) -> str:
    print(f"** Address info parser (ch01: Prompt chaining) **\n")
    print(f":: Please enter address info (Blank Line to finish):")
    print(f"e.g. 1563 Springfield Ave, Maplewood, NJ 07040, United States, Fredrich Grasher")
    print(f"------\n")
    return Application.collect_multilines_input()

  def process(self, query: str) -> AgentResponse:
    _think_llm = OllamaClient(host=settings.ollama_host, model=settings.model)
    builder = AgentBuilder()
    builder.add_client("default", _think_llm)
    builder.add_client("think", _think_llm)
    builder.add_client("review", _think_llm)
    return builder.build(AddressInfoAgent).run(query)