# Real API Setup

This batch adds API integration skeletons only. No crawler is included, and no paid API is required for the demo.

## Environment Variables

Copy `.env.example` into `.env` and set only the providers you want to test.

Recommended first real integrations:

- SerpApi or Google Custom Search for web search.
- NewsAPI for news search.
- OpenSanctions for sanctions screening.
- OpenCorporates or Companies House for basic company information.

## No-Key Behavior

With `PROVIDER_MODE=real` and no provider keys, company-name tasks must still complete. The timeline will show warnings such as a real provider missing an API key, followed by fallback to the mock provider.

## Safety Notes

- Do not commit real API keys.
- Do not write keys into tests, README examples, agent events, or reports.
- Do not scrape HTML pages. Add official API clients or HTTP calls behind provider classes only.
