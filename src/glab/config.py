from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  ollama_host: str = "http://localhost:11434"
  qdrant_host: str = "http://localhost:6333"
  qdrant_vector_size: int = 1024
  model: str = "llama3.2:1b"
  debug: bool = False

  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    env_prefix="MYAPP_"
  )

settings = Settings()