# Protest discovery crawler

**Package:** `src/ingestion/crawler/`  
**CLI:** `lpp-ingest` (or `python -m ingestion` after `pip install -e .`)

The crawler proposes candidate London marches for human review. It does not feed DuckDB or training; the build uses committed files under `src/ingestion/route_research/seed/`.

Output: `data/candidates.csv` (nine fields per row, `ProtestRecord` in `ingestion.crawler.models`).

## Sources

| `platform_id` | Class | Notes |
|---|---|---|
| `met_police` | `MetPoliceSource` | Met Newsroom Section 12 conditions |
| `marble_arch_security` | `MarbleArchSecuritySource` | Marble Arch BID security feed |
| `psc` | `PscSource` | Palestine Solidarity Campaign events |

Add a source by subclassing `ProtestSource` and registering it in `default_sources()` and `build_platform_catalog()`.

## Commands

```bash
lpp-ingest --list-platforms
lpp-ingest --output-dir data
lpp-ingest --platform met_police --met-limit 5
lpp-ingest --organizer-event-days-back 7 --organizer-event-days-ahead 14
```

## Pipeline

`ProtestIngestionPipeline.discover()` calls `fetch_records_safely()` on each source, merges rows, and writes CSV via `write_candidates_csv()`.

## Review gate

Promote selected rows into `seed/events.csv` and `seed/waypoints.csv`, then run `python ingest.py`.
