from app.tools.evidence_extraction_tool import EvidenceExtractionTool
from app.config import get_settings


def test_keyword_fallback_extracts_user_input_evidence(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "mock")
    get_settings.cache_clear()
    tool = EvidenceExtractionTool()

    items = tool.extract_evidence_from_text(
        {"name": "Demo"},
        "该供应商过去一年存在两次交付延期，双方曾因付款纠纷和合同争议进行沟通。",
        task_id="keyword-task",
    )

    assert len(items) >= 1
    assert all(item["source_type"] == "user_input" for item in items)
    assert all(item["source_name"] == "用户粘贴材料" for item in items)
    assert all(item["title"] and item["content"] and item["raw_text"] for item in items)
    assert all(isinstance(item["confidence"], float) for item in items)
    keywords = {keyword for item in items for keyword in item["risk_keywords"]}
    assert {"交付延期", "付款纠纷", "合同争议"}.intersection(keywords)
    assert all(item["source_quote"] for item in items)
    get_settings.cache_clear()


def test_llm_failure_falls_back_to_keyword_extraction(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "llm")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()

    def fail_client():
        raise RuntimeError("llm unavailable")

    monkeypatch.setattr("app.tools.evidence_extraction_tool.create_llm_client", fail_client)

    items = EvidenceExtractionTool().extract_evidence_from_text(
        {"name": "Demo"},
        "材料显示供应商存在经营异常和行政处罚。",
        task_id="llm-fallback-material",
    )

    assert items
    assert any(item["extracted_by"] == "MockKeywordExtractor" for item in items)
    get_settings.cache_clear()
