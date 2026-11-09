# Ingestion

- **Route build:** `python ingest.py` (repo root) — deterministic pipeline from committed seed files → `data/protest.duckdb`
- **Discovery:** `lpp-ingest` — see [docs/crawler.md](../../docs/crawler.md)

The crawler never feeds the build automatically. Approved candidates are copied into `route_research/seed/` by hand.

## Crawl etiquette

Public Met Police notices, Marble Arch BID security updates, and PSC listings. Requests use a named `User-Agent`, `min_interval_sec` throttling, robots.txt checks, and retries with backoff on transient errors.
