import dataclasses
import json
import os
import subprocess
import time
from dataclasses import asdict
from typing import Callable

from glab.agents.agent_ch01_address_parser import AddressInfoAgent
from glab.agents.agent_ch02_customer_support import CustomerSupportAgent
from glab.comm.library import AgentBuilder, Role, AgentResponse
from glab.comm.llm_client_ollama import OllamaClient
from glab.config import settings

def ai_demo():

  while True:
    _clear_screen()
    print("\n")
    print(f"  * ************************************* *")
    print(f"  * Welcome to the AI Design Pattern demo *")
    print(f"  * ************************************* *\n")
    print(f" 1. Address info parser (ch01: Prompt chaining)")
    print(f" 2. Customer support chatbot (ch02: Routing)")
    print(f" 3. Customer feedback analyst (ch03: Parallelization)")
    print(f" 4. Reply customer feedback (ch04: Reflection)")
    print(f"14. Startup Retrieval (ch14: Knowledge Retrieval)\n")
    cmd = input("> Please enter your choice ('q' for quit): ").strip()
    match cmd:
      case "q":
        break
      case "1":
        _process(_address_parser)
      case "2":
        _process(_customer_support)
      case "3":
        print(">> Customer feedback analyst")
      case "4":
        print(">> Reply customer feedback")
      case "14":
        print(">> Startup Retrieval")
      case _:
        print(f">> Unknown command: {cmd}")
        input("> type <any> to continue")

def main():
  ai_demo()

if __name__ == '__main__':
  main()

def _clear_screen():
  subprocess.run('cls' if os.name == 'nt' else 'clear')

def _collect_multilines_input() -> str:
  lst = []
  while True:
    tmp = input()
    if tmp.strip() == "":
      break
    lst.append(tmp)
  return "\n".join(ln for ln in lst if len(ln) > 0)

def _dump_json(data):
  return json.dumps(json.loads("{}"), indent=2, ensure_ascii=False) if data is None \
    else json.dumps(json.loads(data), indent=2, ensure_ascii=False) if isinstance(data, str) \
    else json.dumps(asdict(data), indent=2, ensure_ascii=False) if dataclasses.is_dataclass(data) \
    else "{}"

def _process(func: Callable[[str], AgentResponse]):
  _clear_screen()
  print("\n")
  print(f"** Address Info Parser (ch01: Prompt chaining) **\n")
  print(f":: Please Enter address info (Blank Line to finish):")
  print(f"------\n")
  query = _collect_multilines_input()
  print(f"------")
  print(f":: Thanks for input. AI is processing the request ... \n")

  ts0 = time.time_ns()
  resp = func(query)
  escaped = time.time_ns() - ts0
  print(f"DONE! spent time: {escaped} ns \n")

  last_message = resp.last_message(Role.ASSISTANT)
  print(f"## Formatted Address Data:\n```\n{_dump_json(last_message.content if last_message is not None else "{}")}\n```\n")
  print(f"## Token usage:\n```json\n{_dump_json(resp.token_usage)}\n```\n")

  print(f"## LLM Responses: \n")
  for rs in resp.responses:
    print(f"#### {rs.model} {rs.id}:\n```json\n{_dump_json(rs)}\n```\n")

  print(f"## All LLM Messages: \n")
  for idx, msg in enumerate(resp.messages):
    content = msg.content or ""
    print(f"#### MESSAGE {idx + 1}: {msg.role}:\n```markdown\n{content}\n```\n")

  input("Type <any> to continue")

def _address_parser(query: str) -> AgentResponse:
  # _default_llm = OllamaClient(host=settings.ollama_host, model="deepseek-r1:1.5b")
  _think_llm = OllamaClient(host=settings.ollama_host, model="ornith-1.5:9b")
  builder = AgentBuilder()
  builder.add_client("default", _think_llm)
  builder.add_client("think", _think_llm)
  builder.add_client("review", _think_llm)
  return builder.build(AddressInfoAgent).run(query)

def _customer_support(query: str) -> AgentResponse:
  _think_llm = OllamaClient(host=settings.ollama_host, model="ornith-1.5:9b")
  builder = AgentBuilder()
  builder.add_client("default", _think_llm)
  builder.add_client("think", _think_llm)
  return builder.build(CustomerSupportAgent).run(query)

