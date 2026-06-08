from app.config import get_settings


class ModelClient:
    def complete(self, system: str, user: str) -> str:
        settings = get_settings()
        if settings.model_mode != "llm":
            return f"Mock model response: {user[:160]}"
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required when MODEL_MODE=llm")
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

