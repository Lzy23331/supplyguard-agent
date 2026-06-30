from functools import lru_cache
import os
from pathlib import Path

from pydantic import ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=(
            str(Path(__file__).resolve().parents[2] / "backend" / ".env"),
            str(Path(__file__).resolve().parents[2] / ".env"),
        ),
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )

    app_name: str = "SupplyGuard Agent"
    deployment_mode: str = Field(default="demo", alias="DEPLOYMENT_MODE")
    enable_real_query: bool = Field(default=False, alias="ENABLE_REAL_QUERY")
    demo_mode_enabled: bool = Field(default=True, alias="DEMO_MODE_ENABLED")
    real_query_daily_limit: int = Field(default=20, alias="REAL_QUERY_DAILY_LIMIT")
    real_query_cache_days: int = Field(default=7, alias="REAL_QUERY_CACHE_DAYS")
    cache_demo_tasks: bool = Field(default=True, alias="CACHE_DEMO_TASKS")
    enable_llm_report_polish: bool = Field(default=True, alias="ENABLE_LLM_REPORT_POLISH")
    max_report_polish_input_chars: int = Field(default=6000, alias="MAX_REPORT_POLISH_INPUT_CHARS")
    report_llm_max_input_chars: int = Field(default=6000, alias="REPORT_LLM_MAX_INPUT_CHARS")
    report_llm_timeout_seconds: int = Field(default=30, alias="REPORT_LLM_TIMEOUT_SECONDS")
    max_report_polish_output_tokens: int = Field(default=1800, alias="MAX_REPORT_POLISH_OUTPUT_TOKENS")
    report_polish_top_search_results: int = Field(default=5, alias="REPORT_POLISH_TOP_SEARCH_RESULTS")
    report_polish_top_profile_fields: int = Field(default=8, alias="REPORT_POLISH_TOP_PROFILE_FIELDS")
    report_polish_timeout_seconds: int = Field(default=30, alias="REPORT_POLISH_TIMEOUT_SECONDS")
    model_mode: str = Field(default="mock", alias="MODEL_MODE")
    database_url: str = Field(default="sqlite:///./supplyguard.db", alias="DATABASE_URL")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    llm_timeout_seconds: int = Field(default=30, alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=2, alias="LLM_MAX_RETRIES")
    llm_fallback_to_mock: bool = Field(default=True, alias="LLM_FALLBACK_TO_MOCK")
    provider_mode: str = Field(default="mock", alias="PROVIDER_MODE")
    provider_fallback_to_mock: bool = Field(default=True, alias="PROVIDER_FALLBACK_TO_MOCK")
    provider_timeout_seconds: int = Field(default=15, alias="PROVIDER_TIMEOUT_SECONDS")
    provider_max_retries: int = Field(default=1, alias="PROVIDER_MAX_RETRIES")
    web_search_provider: str = Field(default="mock", alias="WEB_SEARCH_PROVIDER")
    web_search_api: str = Field(default="serpapi", alias="WEB_SEARCH_API")
    serpapi_api_key: str | None = Field(default=None, alias="SERPAPI_API_KEY")
    google_cse_api_key: str | None = Field(default=None, alias="GOOGLE_CSE_API_KEY")
    google_cse_cx: str | None = Field(default=None, alias="GOOGLE_CSE_CX")
    tencentcloud_secret_id: str | None = Field(default=None, alias="TENCENTCLOUD_SECRET_ID")
    tencentcloud_secret_key: str | None = Field(default=None, alias="TENCENTCLOUD_SECRET_KEY")
    tencentcloud_region: str = Field(default="ap-guangzhou", alias="TENCENTCLOUD_REGION")
    tencent_web_search_endpoint: str = Field(default="https://wsa.tencentcloudapi.com", alias="TENCENT_WEB_SEARCH_ENDPOINT")
    tencent_web_search_version: str = Field(default="2025-05-08", alias="TENCENT_WEB_SEARCH_VERSION")
    tencent_web_search_action: str = Field(default="SearchPro", alias="TENCENT_WEB_SEARCH_ACTION")
    tencent_web_search_max_queries: int = Field(default=6, alias="TENCENT_WEB_SEARCH_MAX_QUERIES")
    tencent_web_search_top_k: int = Field(default=5, alias="TENCENT_WEB_SEARCH_TOP_K")
    tencent_web_search_timeout_seconds: int = Field(default=20, alias="TENCENT_WEB_SEARCH_TIMEOUT_SECONDS")
    web_search_max_queries: int | None = Field(default=None, alias="WEB_SEARCH_MAX_QUERIES")
    web_search_results_per_query: int | None = Field(default=None, alias="WEB_SEARCH_RESULTS_PER_QUERY")
    web_search_max_total_results: int = Field(default=25, alias="WEB_SEARCH_MAX_TOTAL_RESULTS")
    web_search_max_evidence_items: int = Field(default=12, alias="WEB_SEARCH_MAX_EVIDENCE_ITEMS")
    web_search_llm_top_n: int = Field(default=10, alias="WEB_SEARCH_LLM_TOP_N")
    web_search_min_entity_match_for_scoring: float = Field(default=0.65, alias="WEB_SEARCH_MIN_ENTITY_MATCH_FOR_SCORING")
    web_search_min_risk_relevance_for_scoring: float = Field(default=0.55, alias="WEB_SEARCH_MIN_RISK_RELEVANCE_FOR_SCORING")
    web_search_min_domain_trust_for_scoring: float = Field(default=0.35, alias="WEB_SEARCH_MIN_DOMAIN_TRUST_FOR_SCORING")
    web_search_min_confidence_for_scoring: float = Field(default=0.55, alias="WEB_SEARCH_MIN_CONFIDENCE_FOR_SCORING")
    web_search_llm_disambiguation_enabled: bool = Field(default=False, alias="WEB_SEARCH_LLM_DISAMBIGUATION_ENABLED")
    web_search_llm_disambiguation_max_results: int = Field(default=10, alias="WEB_SEARCH_LLM_DISAMBIGUATION_MAX_RESULTS")
    tencent_wsa_provider: str | None = Field(default=None, alias="TENCENT_WSA_PROVIDER")
    tencent_wsa_endpoint: str | None = Field(default=None, alias="TENCENT_WSA_ENDPOINT")
    tencent_wsa_action: str | None = Field(default=None, alias="TENCENT_WSA_ACTION")
    tencent_wsa_version: str | None = Field(default=None, alias="TENCENT_WSA_VERSION")
    tencent_wsa_edition: str | None = Field(default=None, alias="TENCENT_WSA_EDITION")
    newsapi_key: str | None = Field(default=None, alias="NEWSAPI_KEY")
    gdelt_enabled: bool = Field(default=True, alias="GDELT_ENABLED")
    sanctions_provider: str = Field(default="mock", alias="SANCTIONS_PROVIDER")
    opensanctions_api_key: str | None = Field(default=None, alias="OPENSANCTIONS_API_KEY")
    sanctions_local_csv: str = Field(default="data/external/sanctions_list.csv", alias="SANCTIONS_LOCAL_CSV")
    company_info_provider: str = Field(default="mock", alias="COMPANY_INFO_PROVIDER")
    opencorporates_api_token: str | None = Field(default=None, alias="OPENCORPORATES_API_TOKEN")
    companies_house_api_key: str | None = Field(default=None, alias="COMPANIES_HOUSE_API_KEY")
    qcc_api_key: str | None = Field(default=None, alias="QCC_API_KEY")
    tianyancha_token: str | None = Field(default=None, alias="TIANYANCHA_TOKEN")
    llm_query_planner_enabled: bool = Field(default=True, alias="LLM_QUERY_PLANNER_ENABLED")
    llm_search_evidence_extract_enabled: bool = Field(default=False, alias="LLM_SEARCH_EVIDENCE_EXTRACT_ENABLED")
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2], alias="PROJECT_ROOT")

    @model_validator(mode="after")
    def use_deepseek_key_alias(self) -> "Settings":
        self.provider_mode = (self.provider_mode or "mock").strip().lower()
        self.web_search_provider = (self.web_search_provider or "mock").strip().lower()
        self.web_search_api = (self.web_search_api or "serpapi").strip().lower()
        self.company_info_provider = (self.company_info_provider or "mock").strip().lower()
        self.sanctions_provider = (self.sanctions_provider or "mock").strip().lower()
        if not self.openai_api_key and os.getenv("DEEPSEEK_API_KEY"):
            self.openai_api_key = os.getenv("DEEPSEEK_API_KEY")
            if not os.getenv("OPENAI_BASE_URL"):
                self.openai_base_url = "https://api.deepseek.com/v1"
            if not os.getenv("OPENAI_MODEL"):
                self.openai_model = "deepseek-chat"
        if self.tencent_wsa_provider and not os.getenv("WEB_SEARCH_PROVIDER"):
            self.web_search_provider = self.tencent_wsa_provider.strip().lower()
        if self.tencent_wsa_provider == "real" and not os.getenv("WEB_SEARCH_API"):
            self.web_search_api = "tencent"
        if (
            self.web_search_provider == "mock"
            and self.tencentcloud_secret_id
            and self.tencentcloud_secret_key
            and (self.tencent_wsa_endpoint or self.tencent_wsa_action or self.tencent_wsa_version)
            and not os.getenv("WEB_SEARCH_PROVIDER")
        ):
            self.web_search_provider = "real"
            self.web_search_api = "tencent"
        if self.tencent_wsa_endpoint and not os.getenv("TENCENT_WEB_SEARCH_ENDPOINT"):
            self.tencent_web_search_endpoint = self.tencent_wsa_endpoint
        if self.tencent_wsa_action and not os.getenv("TENCENT_WEB_SEARCH_ACTION"):
            self.tencent_web_search_action = self.tencent_wsa_action
        if self.tencent_wsa_version and not os.getenv("TENCENT_WEB_SEARCH_VERSION"):
            self.tencent_web_search_version = self.tencent_wsa_version
        if self.web_search_max_queries is not None and not os.getenv("TENCENT_WEB_SEARCH_MAX_QUERIES"):
            self.tencent_web_search_max_queries = self.web_search_max_queries
        if self.web_search_results_per_query is not None and not os.getenv("TENCENT_WEB_SEARCH_TOP_K"):
            self.tencent_web_search_top_k = self.web_search_results_per_query
        if self.tencent_web_search_endpoint and not self.tencent_web_search_endpoint.startswith(("http://", "https://")):
            self.tencent_web_search_endpoint = f"https://{self.tencent_web_search_endpoint}"
        return self

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


