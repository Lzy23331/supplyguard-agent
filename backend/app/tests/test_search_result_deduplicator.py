from app.services.search_result_deduplicator import SearchResultDeduplicator


def test_deduplicates_url_title_and_snippet():
    rows = [
        {"title": "比亚迪行政处罚信息", "url": "https://example.com/a?utm_source=x", "snippet": "行政处罚详情", "rank": 1},
        {"title": "比亚迪行政处罚信息", "url": "https://example.com/a?utm_source=y", "snippet": "行政处罚详情", "rank": 2},
        {"title": "比亚迪行政处罚信息", "url": "https://example.com/b", "snippet": "行政处罚详情", "rank": 3},
    ]

    kept, duplicates = SearchResultDeduplicator().deduplicate(rows)

    assert len(kept) == 1
    assert len(duplicates) == 2
    assert {item["excluded_reason"] for item in duplicates} <= {"duplicate_canonical_url", "duplicate_same_domain_title", "duplicate_similar_snippet"}
