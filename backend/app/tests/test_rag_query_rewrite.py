from app.database import init_db
from app.tools.rag_policy import RAGPolicyTool


def test_rag_query_rewrite_fallback_does_not_break_policy_retrieval(monkeypatch):
    init_db()

    def fail_rewrite(*args, **kwargs):
        raise RuntimeError("rewrite failed")

    monkeypatch.setattr("app.tools.rag_policy.rewrite_policy_queries", fail_rewrite)
    tool = RAGPolicyTool()
    policies, queries, rewrite_used = tool.retrieve_with_query_rewrite(
        task_id="rag-fallback-task",
        supplier_profile={"region": "境外"},
        evidence_items=[{"title": "供应商涉及制裁名单", "content": "黑名单风险"}],
        fallback_query="制裁名单 黑名单 境外供应商",
        top_k=3,
    )

    assert policies
    assert queries == ["制裁名单 黑名单 境外供应商"]
    assert rewrite_used is False


def test_rag_query_rewrite_uses_mock_queries(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "mock")
    init_db()
    tool = RAGPolicyTool()

    policies, queries, rewrite_used = tool.retrieve_with_query_rewrite(
        task_id="rag-mock-task",
        supplier_profile={"region": "境外", "cooperation_type": "紧急采购"},
        evidence_items=[{"title": "交付延期与制裁筛查", "content": "合同争议 黑名单"}],
        fallback_query="标准准入",
        top_k=3,
    )

    assert policies
    assert 3 <= len(queries) <= 6
    assert rewrite_used is True
