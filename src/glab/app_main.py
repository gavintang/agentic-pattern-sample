import dataclasses
import json
import os
import re
import subprocess
import time
from dataclasses import asdict

from glab.agents.agent_ch14_startup_retrieval import StartupRetrievalAgent
from glab.app.app_ch01_address_parser import AppCh01AddressParser
from glab.app.app_ch02_customer_support import AppCh02CustomerSupport
from glab.app.app_ch03_customer_feedback import AppCh03CustomerFeedback
from glab.app.app_ch14_startup_retrieval import AppCh14ResetCollection, AppCh14ImportEntries, AppCh14AddStartupEntry, \
  AppCh14NeuralSearch, AppCh14DeleteCollection
from glab.comm.library import AgentBuilder, Application

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
    print(f"14. Startup Retrieval (ch14: Knowledge Retrieval)\n")
    cmd = input("> Please enter your choice ('q' for quit): ").strip()
    match cmd:
      case "q":
        break
      case "1": _process(AppCh01AddressParser())
      case "2": _process(AppCh02CustomerSupport())
      case "3": _process(AppCh03CustomerFeedback())
      case "14": _14_menu_startup_retrieval()
      case _:
        print(f">> Unknown command: {cmd}")
        input("> type <any> to continue")

def main():
  ai_demo()

if __name__ == '__main__':
  main()

def _clear_screen():
  subprocess.run('cls' if os.name == 'nt' else 'clear')

def _dump_json(data):
  return json.dumps(json.loads("{}"), indent=2, ensure_ascii=False) if data is None \
    else json.dumps(json.loads(data), indent=2, ensure_ascii=False) if isinstance(data, str) \
    else json.dumps(asdict(data), indent=2, ensure_ascii=False) if dataclasses.is_dataclass(data) \
    else "{}"

def _process(app: Application):
  _clear_screen()
  print("\n")
  query = app.collect_input()
  if not query:
    print(f":: Cancelled ::")
    input("pause, type <any-key> to continue\n")
    return

  print(f"------")
  print(f":: Received input: {query}")
  print(f":: Thanks for input. AI is processing the request ... \n")

  ts0 = time.time_ns()
  resp = app.process(query)
  escaped = time.time_ns() - ts0
  print(f"DONE! spent time: {escaped} ns")
  input("pause, type <any-key> to continue\n")

  last_message = resp.last_message()
  print(f"## Result:\n```\n{_dump_json(last_message.content if last_message is not None else "{}")}\n```\n")
  print(f"## Token usage:\n```json\n{_dump_json(resp.token_usage)}\n```")
  input("pause, type <any-key> to continue\n")

  print(f"## All LLM Messages: \n")
  for idx, msg in enumerate(resp.messages):
    content = msg.content or ""
    print(f"#### MESSAGE {idx + 1}: {msg.role}:\n```markdown\n{content}\n```\n")
  input("pause, type <any-key> to continue\n")

  print(f"## LLM Responses: \n")
  for rs in resp.responses:
    print(f"#### {rs.model} {rs.id}:\n```json\n{_dump_json(rs)}\n```\n")
  input("pause, type <any-key> to continue\n")
  input("Completed, type <any-key> to continue")

DEFAULT_COLLECTION = "my-startup-lib"

def _14_menu_startup_retrieval():
  collection_name = input("input collection name [a-z_-]: ")
  while len(collection_name) > 0 and not re.match(r"[a-z_-]+", collection_name):
    collection_name = input("invalid collection name, please retry: ")
    collection_name = DEFAULT_COLLECTION if not collection_name else collection_name
  agent = AgentBuilder().build(lambda clients: StartupRetrievalAgent(clients, collection_name))
  while True:
    _clear_screen()
    print(f"\n Collection Name: {collection_name}")
    print(f"------")
    print("\n")
    print(f" * ************************************* *")
    print(f" * Select function for startup retrieval *")
    print(f" * ************************************* *\n")
    print(f" 1. Create or reset collection")
    print(f" 2. Import startup entries")
    print(f" 3. Add startup entry")
    print(f" 4. Neural search")
    print(f" 5. Delete collection")
    print(f" type 'q' to back main menu")
    cmd = input("> Please enter your choice: ").strip()
    match cmd:
      case "q": break
      case "1": _process(AppCh14ResetCollection(agent))
      case "2": _process(AppCh14ImportEntries(agent))
      case "3": _process(AppCh14AddStartupEntry(agent))
      case "4": _process(AppCh14NeuralSearch(agent))
      case "5": _process(AppCh14DeleteCollection(agent))
