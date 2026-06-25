# Provider Integration

SupplyGuard uses `EvidenceProviderManager` as the only orchestration entry point for external evidence. Providers return normalized candidates; they do not write database records and they do not decide the final risk level.

## Modes

- `PROVIDER_MODE=mock`: use mock company info, mock news, mock sanctions and internal CSV records.
- `PROVIDER_MODE=real`: prefer real provider skeletons. Missing API keys or runtime failures fall back to mock providers when `PROVIDER_FALLBACK_TO_MOCK=true`.
- `PROVIDER_MODE=disabled`: skip external providers and keep internal records only.

Per-provider switches can be set with `WEB_SEARCH_PROVIDER`, `SANCTIONS_PROVIDER`, and `COMPANY_INFO_PROVIDER`, using `mock`, `real`, or `disabled`.

For Tencent Cloud web search, set:

- `WEB_SEARCH_PROVIDER=real`
- `WEB_SEARCH_API=tencent`
- `TENCENTCLOUD_SECRET_ID`
- `TENCENTCLOUD_SECRET_KEY`
- `TENCENTCLOUD_REGION`
- `TENCENT_WEB_SEARCH_ENDPOINT`
- `TENCENT_WEB_SEARCH_MAX_QUERIES`
- `TENCENT_WEB_SEARCH_TOP_K`

The search planner limits query count to at most 8 and defaults to 6. The Tencent provider only uses returned title, snippet/summary and URL; it does not crawl page content.

## Provider Contract

Each provider implements:

- `is_configured()`: returns whether required environment variables or local files exist.
- `collect(company_name, resolved_company, context)`: returns evidence candidates only.

The manager sends every candidate through `ExternalEvidenceNormalizer`, then the agent stores normalized evidence in `evidence_items`.

## Fallback

If a real provider is not configured or fails, the manager writes a warning event and falls back to the mapped mock provider when fallback is enabled. API keys and tokens are never written to agent events.

`web_search` evidence is extracted by keyword rules from search result title/snippet. Search results are public web signals, not official business registry verification, and reports keep that uncertainty note.
