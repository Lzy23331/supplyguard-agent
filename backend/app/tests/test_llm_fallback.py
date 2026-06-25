from app.config import get_settings
from app.database import get_db, init_db
from app.services.llm_task_service import generate_intake_plan


def test_llm_mode_without_openai_key_falls_back_to_mock(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "llm")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("LLM_FALLBACK_TO_MOCK", "true")
    get_settings.cache_clear()
    init_db()

    plan = generate_intake_plan(None, "fallback-task", {"name": "测试供应商"}, agent_name="TestAgent")

    assert "focus_areas" in plan
    with get_db() as conn:
        row = conn.execute(
            "SELECT fallback_used, fallback_reason FROM llm_call_logs WHERE task_id=? ORDER BY id DESC LIMIT 1",
            ("fallback-task",),
        ).fetchone()
    assert row is not None
    assert row["fallback_used"] == 1
    assert "OPENAI_API_KEY" in row["fallback_reason"]
    get_settings.cache_clear()


def test_deepseek_api_key_alias_is_supported(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "llm")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.openai_api_key == "test-deepseek-key"
    assert settings.openai_base_url == "https://api.deepseek.com/v1"
    assert settings.openai_model == "deepseek-chat"
    get_settings.cache_clear()
