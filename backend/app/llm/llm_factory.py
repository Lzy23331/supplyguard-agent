from dataclasses import dataclass

from app.config import get_settings
from app.llm.base import BaseLLMClient, LLMConfigurationError
from app.llm.mock_client import MockLLMClient
from app.llm.openai_compatible_client import OpenAICompatibleClient


@dataclass(frozen=True)
class LLMClientBundle:
    client: BaseLLMClient
    actual_model_mode: str
    requested_model_mode: str
    model_name: str | None
    fallback_used: bool = False
    fallback_reason: str | None = None


def create_llm_client() -> LLMClientBundle:
    settings = get_settings()
    requested = (settings.model_mode or "mock").lower()
    if requested == "mock":
        return LLMClientBundle(MockLLMClient(), "mock", requested, "mock-llm")
    if requested in {"llm", "real"} and settings.openai_api_key:
        return LLMClientBundle(OpenAICompatibleClient(), "llm", requested, settings.openai_model)
    if requested in {"llm", "real"} and settings.llm_fallback_to_mock:
        return LLMClientBundle(
            MockLLMClient(),
            "mock",
            requested,
            "mock-llm",
            fallback_used=True,
            fallback_reason="OPENAI_API_KEY is empty; fallback to mock client",
        )
    raise LLMConfigurationError("MODEL_MODE=llm/real requires OPENAI_API_KEY or DEEPSEEK_API_KEY when LLM_FALLBACK_TO_MOCK=false")
