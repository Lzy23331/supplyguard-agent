import json
import re
import time
from typing import Any

import httpx

from app.config import get_settings
from app.llm.base import BaseLLMClient, LLMClientError, LLMOutputValidationError


class OpenAICompatibleClient(BaseLLMClient):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_name = self.settings.openai_model

    def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        task_type: str,
        timeout_seconds: int | None = None,
    ) -> dict:
        text = self.complete_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            task_type=task_type,
            timeout_seconds=timeout_seconds,
        )
        cleaned = self._clean_json_text(text)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LLMOutputValidationError(f"LLM JSON parse failed for {task_type}: {exc}") from exc
        if not isinstance(data, dict):
            raise LLMOutputValidationError(f"LLM output for {task_type} must be a JSON object")
        return data

    def complete_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        task_type: str,
        timeout_seconds: int | None = None,
    ) -> str:
        if not self.settings.openai_api_key:
            raise LLMClientError("OPENAI_API_KEY is empty")
        url = f"{self.settings.openai_base_url.rstrip('/')}/chat/completions"
        timeout = timeout_seconds or self.settings.llm_timeout_seconds
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.settings.openai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        last_error: Exception | None = None
        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except (httpx.HTTPError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt < self.settings.llm_max_retries:
                    time.sleep(min(0.5 * (attempt + 1), 2.0))
        raise LLMClientError(f"OpenAI-compatible request failed for {task_type}: {last_error}") from last_error

    def _clean_json_text(self, text: str) -> str:
        stripped = text.strip()
        match = re.search(r"```(?:json)?\s*(.*?)```", stripped, flags=re.S | re.I)
        return match.group(1).strip() if match else stripped
