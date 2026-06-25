from app.config import get_settings
from app.evidence_providers.provider_manager import EvidenceProviderManager
from app.evidence_providers.real_company_info_provider import RealCompanyInfoProvider
from app.evidence_providers.real_news_search_provider import RealNewsSearchProvider
from app.evidence_providers.real_sanctions_provider import RealSanctionsProvider
from app.evidence_providers.real_web_search_provider import RealWebSearchProvider


def clear_settings():
    get_settings.cache_clear()


def test_provider_mode_mock_loads_mock_providers(monkeypatch):
    monkeypatch.setenv("PROVIDER_MODE", "mock")
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "mock")
    monkeypatch.setenv("WEB_SEARCH_API", "serpapi")
    monkeypatch.delenv("TENCENT_WSA_PROVIDER", raising=False)
    clear_settings()

    manager = EvidenceProviderManager()
    names = [provider.name for provider in manager.providers]

    assert "MockCompanyInfoProvider" in names
    assert "MockNewsProvider" in names
    assert "MockSanctionsProvider" in names
    assert "InternalRecordCsvProvider" in names


def test_tencent_wsa_alias_enables_tencent_provider(monkeypatch):
    monkeypatch.delenv("WEB_SEARCH_PROVIDER", raising=False)
    monkeypatch.delenv("WEB_SEARCH_API", raising=False)
    monkeypatch.setenv("PROVIDER_MODE", "mock")
    monkeypatch.setenv("TENCENT_WSA_PROVIDER", "real")
    monkeypatch.setenv("TENCENT_WSA_ENDPOINT", "wsa.tencentcloudapi.com")
    clear_settings()

    settings = get_settings()
    manager = EvidenceProviderManager()

    assert settings.web_search_provider == "real"
    assert settings.web_search_api == "tencent"
    assert settings.tencent_web_search_endpoint == "https://wsa.tencentcloudapi.com"
    assert "TencentWebSearchProvider" in [provider.name for provider in manager.providers]


def test_real_provider_is_configured_checks_keys(monkeypatch):
    monkeypatch.delenv("TENCENT_WSA_PROVIDER", raising=False)
    monkeypatch.setenv("WEB_SEARCH_API", "serpapi")
    for key in [
        "SERPAPI_API_KEY",
        "GOOGLE_CSE_API_KEY",
        "GOOGLE_CSE_CX",
        "NEWSAPI_KEY",
        "OPENSANCTIONS_API_KEY",
        "OPENCORPORATES_API_TOKEN",
        "COMPANIES_HOUSE_API_KEY",
        "QCC_API_KEY",
        "TIANYANCHA_TOKEN",
    ]:
        monkeypatch.setenv(key, "")
    monkeypatch.setenv("SANCTIONS_LOCAL_CSV", "data/external/missing_sanctions_for_test.csv")
    clear_settings()

    assert RealWebSearchProvider().is_configured() is False
    assert RealNewsSearchProvider().is_configured() is False
    assert RealSanctionsProvider().is_configured() is False
    assert RealCompanyInfoProvider().is_configured() is False

    monkeypatch.setenv("SERPAPI_API_KEY", "test_key")
    monkeypatch.setenv("NEWSAPI_KEY", "test_key")
    monkeypatch.setenv("OPENSANCTIONS_API_KEY", "test_key")
    monkeypatch.setenv("OPENCORPORATES_API_TOKEN", "test_key")
    clear_settings()

    assert RealWebSearchProvider().is_configured() is True
    assert RealNewsSearchProvider().is_configured() is True
    assert RealSanctionsProvider().is_configured() is True
    assert RealCompanyInfoProvider().is_configured() is True
