from functools import lru_cache
from pathlib import Path

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", populate_by_name=True, arbitrary_types_allowed=True)

    app_name: str = "SupplyGuard Agent"
    model_mode: str = Field(default="mock", alias="MODEL_MODE")
    database_url: str = Field(default="sqlite:///./supplyguard.db", alias="DATABASE_URL")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2], alias="PROJECT_ROOT")

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def samples_dir(self) -> Path:
        return self.data_dir / "samples"

    @property
    def policies_dir(self) -> Path:
        return self.data_dir / "policies"

    @property
    def suppliers_path(self) -> Path:
        return self.samples_dir / "suppliers.json"

    @property
    def mock_search_results_path(self) -> Path:
        return self.samples_dir / "mock_search_results.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
