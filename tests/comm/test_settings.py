from glab.comm.library import LlmClient
from glab.comm.llm_client_ollama import OllamaClient

OLLAMA_HOST = "http://localhost:11434"

def llm_ollama_gemma4() -> LlmClient:
  return OllamaClient(host=OLLAMA_HOST, model="gemma4:e4b")

def llm_ollama_ornith15() -> LlmClient:
  return OllamaClient(host=OLLAMA_HOST, model="ornith-1.5:9b")

def llm_ollama_deepseekr1() -> LlmClient:
  return OllamaClient(host=OLLAMA_HOST, model="deepseek-r1:1.5b")

def llm_ollama_bgem3() -> LlmClient:
  return OllamaClient(host=OLLAMA_HOST, model="bge-m3:567m")