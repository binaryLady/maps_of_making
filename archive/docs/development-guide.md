# Development Guide: Maps of Making

> **Updated:** April 2026

---

## What's Running Now

The only working code is the **Python scraping pipeline** in `scraped/`. The core platform (Oxigraph, heartbeat agent, web app) is not yet implemented.

---

## Scraping Pipeline

### Prerequisites

- Python 3.11+
- A Mistral AI API key (for LLM extraction)
- Internet access (scrapes public websites)

### Setup

```bash
cd scraped/
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

pip install -r requirements.txt

cp .env.template .env
# Edit .env and add your MISTRAL_API_KEY
```

### Running

```bash
# Full pipeline (all phases)
python scripts/run_full_pipeline.py

# Individual phases
python scripts/extract_lifetech_members.py      # Phase 2: member list
python scripts/fetch_member_websites.py          # Phase 3: crawl websites
python scripts/extract_company_data.py           # Phase 4: LLM extraction
python scripts/export_for_map.py                 # Phase 5: GeoJSON output
```

### Output

- `scraped/lifetech.brussels/` — TOML profiles per member
- `scraped/deviceMed.fr/` — TOML profiles for DeviceMed members
- SQLite log at `lifetech.brussels/extraction_log.db`

### Tests

```bash
cd scraped/
source venv/bin/activate
pytest scripts/test_extraction_pipeline.py -v
```

---

## Isolation Notes

- `distrobox-host-exec` works perfectly for accessing podman containers from within a distrobox environment.
- The scraping pipeline runs cleanly in a venv inside distrobox.

---

## Planned Stack (Not Yet Implemented)

See [architecture/architecture.md](architecture/architecture.md) for the full design.

Quick reference for what needs to be built:

| Component | Language/Tech | Notes |
|-----------|--------------|-------|
| Oxigraph server | Rust (binary) | Download from oxigraph.org or `cargo install oxigraph` |
| TOML→JSON-LD converter | Python | Extend existing scraped/ pipeline |
| Heartbeat agent | Python + nanoclaw/openclaw | New component |
| NL→SPARQL bridge | Python + LLM harness | New component |
| Web map | HTML/JS + Leaflet | Prototypes exist (Maps_of_Making.html) |
| Channel bot | Python webhooks | Mattermost or Matrix |

---

## Environment Variables

```bash
# scraped/.env
MISTRAL_API_KEY=...          # Required for LLM extraction
FIRECRAWL_API_KEY=...        # Optional: fallback web scraping
```

Future (when Oxigraph is running):
```bash
OXIGRAPH_ENDPOINT=http://localhost:7878/query
OXIGRAPH_UPDATE_ENDPOINT=http://localhost:7878/update
LLM_HARNESS=nanoclaw         # or openclaw
```
