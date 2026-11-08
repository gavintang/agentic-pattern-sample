import json
import os

from glab.agents.agent_ch14_startup_retrieval import StartupRetrievalAgent
from glab.comm.library import Application, AgentResponse, Agent
from glab.comm.skills import dump_json_data

DEFAULT_COLLECTION = "my-startup-lib"

class AppCh14ResetCollection(Application):
  def __init__(self, agent: Agent):
    self.agent = agent
  def collect_input(self) -> str:
    collection_name = DEFAULT_COLLECTION
    if isinstance(self.agent, StartupRetrievalAgent): collection_name = self.agent.collection_name
    print(f"** 14. Startup Retrieval (ch14: Knowledge Retrieval) **\n")
    is_ok = input(f":: Please confirm to create or reset collection '{collection_name}'? (y/n): ").lower() == "y"
    return dump_json_data({
      "cmd": "reset",
      "collection": f"{self.agent.collection_name}"
    }) if is_ok else ""
  def process(self, query: str) -> AgentResponse:
    return self.agent.run(query)


class AppCh14ImportEntries(Application):
  def __init__(self, agent: Agent):
    self.agent = agent
  def collect_input(self) -> str:
    print(f"** 14. Startup Retrieval (ch14: Knowledge Retrieval) **\n")
    print(f":: Please input collection entries file ::")
    print(f":: e.g. ./tests/resource/startups_sample100")
    print(f"------\n")
    file_path = input("input file location: ")
    while not file_path or not os.path.isfile(file_path):
      file_path = input("invalid file location, please input: ")
    return dump_json_data({
      "cmd": "import",
      "file": f"{file_path}"
    })
  def process(self, query: str) -> AgentResponse:
    return self.agent.run(query)


class AppCh14AddStartupEntry(Application):
  def __init__(self, agent: Agent):
    self.agent = agent
  def collect_input(self) -> str:
    print(f"** 14. Startup Retrieval (ch14: Knowledge Retrieval) **\n")
    print(f":: Please input entry name ::")
    print(f":: e.g. ")
    print(f"        name: OneSaas")
    print(f"        city: Sydney")
    print(f"        link: http://onesaas.com")
    print(f"      images: https://d1qb2nb5cznatu.cloudfront.net/startups/i/525071-fc85bbf4f2ee4eed26b243e9a2b75bed-thumb_jpg.jpg?buster=1414966692")
    print(f"         alt: OneSaas -  global")
    print(f" description: When your business apps get along, everyone's happy\nGet OneSaas and have all your business apps talking to each other, sharing data and making life easier.\nAutomatically sync data between all your apps -- Get your business apps happily teamed up and making your business life easier.\nConnect your apps in minutes, ...")
    print(f"------\n")
    is_ok = False
    query = ""
    while not is_ok:
      name = input("input name: ")
      city = input("input city: ")
      link = input("input website link: ")
      image = input("input image url: ")
      alt = input("input short summary (ALT): ")
      print("input description (Blank Line to finish): ")
      description = Application.collect_multilines_input()
      query = dump_json_data({
        "cmd": "add",
        "name": name,
        "alt": alt,
        "city": city,
        "description": description,
        "images": image,
        "link": link
      })
      print(f"Entry:: {json.dumps(query, sort_keys=False, indent=2, separators=(',', ': '))} \n")
      is_ok = input("Is it ok? (y/n): ").lower() == "y"
    return query
  def process(self, query: str) -> AgentResponse:
    return self.agent.run(query)


class AppCh14NeuralSearch(Application):
  def __init__(self, agent: Agent):
    self.agent = agent
  def collect_input(self) -> str:
    print(f"** 14. Startup Retrieval (ch14: Knowledge Retrieval) **\n")
    print(f":: Please input your query ::")
    print(f":: e.g. ")
    print(f":: #1. city: 'Sydney', search: 'reinvent education'")
    print(f":: #2. city: '', search: 'reinvent education'")
    print(f"------\n")
    is_ok = False
    query = ""
    while not is_ok:
      city = input("input city: ") or None
      search = input("input search query: ")
      query = dump_json_data({
        "cmd": "search",
        "city": city,
        "query": search
      })
      print(f"Search Query:: {json.dumps(query, sort_keys=False, indent=2, separators=(',', ': '))} \n")
      is_ok = input("Is it ok? (y/n): ").lower() == "y"
    return query
  def process(self, query: str) -> AgentResponse:
    return self.agent.run(query)


class AppCh14DeleteCollection(Application):
  def __init__(self, agent: Agent):
    self.agent = agent
  def collect_input(self) -> str:
    collection_name = DEFAULT_COLLECTION
    if isinstance(self.agent, StartupRetrievalAgent): collection_name = self.agent.collection_name
    print(f"** 14. Startup Retrieval (ch14: Knowledge Retrieval) **\n")
    is_ok = input(f":: Please confirm to delete collection '{collection_name}'? (y/n): ").lower() == "y"
    return dump_json_data({
      "cmd": "delete",
      "collection": f"{collection_name}"
    }) if is_ok else ""
  def process(self, query: str) -> AgentResponse:
    return self.agent.run(query)