from app.tools.document_parser_tool import DocumentParserTool
from app.tools.rag_policy_tool import RAGPolicyTool
from app.config import get_settings


def test_document_parser_returns_policy_chunks():
    chunks = DocumentParserTool().parse_policy_chunks(get_settings().policies_dir)
    assert len(chunks) >= 8
    assert all(chunk["doc_name"] and chunk["section_title"] and chunk["content"] for chunk in chunks)


def test_policy_search_high_risk_terms():
    matches = RAGPolicyTool().retrieve("制裁名单 黑名单 境外供应商", top_k=3)
    assert matches
    assert any("制裁" in item["content"] or "黑名单" in item["content"] for item in matches)
    assert all("score" in item and "matched_keywords" in item for item in matches)


def test_policy_search_medium_risk_terms():
    matches = RAGPolicyTool().retrieve("交付延期 合同争议 补充材料 人工复核", top_k=3)
    assert matches
    assert any("补充材料" in item["content"] or "交付延期" in item["content"] for item in matches)
    assert all(item["matched_keywords"] for item in matches)


def test_policy_search_low_risk_terms():
    matches = RAGPolicyTool().retrieve("标准准入 资料完整 年度复查", top_k=3)
    assert matches
    assert any("标准准入" in item["content"] or "年度复查" in item["content"] for item in matches)
