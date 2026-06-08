from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", populate_by_name=True)

    app_name: str = "SupplyGuard Agent"
    database_url: str = "sqlite:///./supplyguard.db"
    model_mode: str = Field(default="mock", alias="MODEL_MODE")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    project_root: Path = Path(__file__).resolve().parents[2]


@lru_cache
def get_settings() -> Settings:
    return Settings()
