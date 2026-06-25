from abc import ABC, abstractmethod


class LLMClientError(RuntimeError):
    pass


class LLMConfigurationError(LLMClientError):
    pass


class LLMOutputValidationError(LLMClientError):
    pass


class BaseLLMClient(ABC):
    @abstractmethod
    def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        task_type: str,
        timeout_seconds: int | None = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def complete_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        task_type: str,
        timeout_seconds: int | None = None,
    ) -> str:
        raise NotImplementedError
