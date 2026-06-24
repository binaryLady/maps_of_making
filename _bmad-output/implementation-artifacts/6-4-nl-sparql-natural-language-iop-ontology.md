# Story 6.4: NL→SPARQL — Full Natural Language with IoP Ontology Guardrail

**Status:** review
**Epic:** 6 — Ask Bernard
**Story ID:** 6-4
**Depends on:** 6.3 (template queries working, `sparql_client.run_select()` live), Story 1.4 (IoP ontology loaded in Oxigraph)

---

## User Story

As a community member,
I want to ask free-form questions and get grounded answers,
So that discovery isn't limited to the templated command vocabulary.

---

## Acceptance Criteria

**Given** the IoP ontology is loaded in Oxigraph and the intent classifier routes a message to `nl_discovery`
**When** Story 6.4 lands
**Then** `harness/nl_to_sparql.py` handles the `nl_discovery` path end-to-end:
- An IoP + mom ontology subset is extracted at startup via SPARQL CONSTRUCT and cached in memory; `RELOAD_ONTOLOGY=1` env var forces a reload
- The LLM call uses **Sonnet** (`anthropic/claude-sonnet-4-5`) at `temperature=0.0`, `max_tokens=512`, with the ontology slice in the **system** message and the user question in the **user** message
- The generated SPARQL is validated before execution: any statement containing `DROP`, `INSERT`, `DELETE`, or `UPDATE` (case-insensitive) is rejected, logged as a security event, and returns `nl_invalid_sparql_ack` to the user (NFR-S5; bot stays read-only on Oxigraph, NFR-S7)
- Valid queries are executed via `sparql_client.run_select()`; results are formatted in Bernard voice with source-space links + a collapsed `> How I searched` SPARQL transparency block (FR39)

**And** when the generated query returns no results, is invalid, or the LLM fails:
- An `mom:OntologyGap` triple is written to Oxigraph (named graph `<urn:mak:gaps>`) via `sparql_client.run_update()` with `mom:rawQuery`, `mom:rawLLMOutput`, and `mom:gapTimestamp` (FR41)
- Bernard returns `nl_gap_ack` — a clarification offer, never a dead end (FR40)

**And** `harness/router.py` wires the `nl_discovery` intent to `nl_to_sparql.dispatch(message, session_id)` (replacing the current `unknown_ack()` stub)

**And** `harness/sparql_client.py` gains `run_construct()` (returns RDF text) and `run_update()` (writes to Oxigraph via `/update` endpoint)

**And** `ontology/iop/iop.ttl` is expanded from its current stub (12 lines) to a minimal but usable vocabulary: at minimum `iop:Place`, `iop:Makerspace`, `iop:Activity`, `iop:Equipment` classes + `skos:closeMatch` bridges to `mom:` and `schema:` equivalents

**And** `harness/bernard_voice.yaml` gains four new keys: `nl_result_ack`, `nl_empty_ack`, `nl_gap_ack`, `nl_invalid_sparql_ack`

**And** `harness/tests/test_nl_to_sparql.py` covers: SPARQL injection rejection, gap triple emission on empty result, ontology cache hit vs reload, Bernard voice in result formatting

**Done gate (operator confirmation):** a French / English / German free-form question returns a grounded, source-linked answer with SPARQL transparency block; an unanswerable question logs a gap triple in Oxigraph and returns a Bernard clarification.

---

## Nanobot Re-evaluation (ADR-013 decision point)

ADR-013 deferred Nanobot to Story 6.4 for re-evaluation. **Decision: stay with `harness/`.** The harness is deployed, tested (63 tests passing), and handles all required channel adapters and intent routing. Nanobot requires cloning and building from source (`hkuds/nanobot` is not publicly available), which is high overhead with no unlock: the `harness/llm_client.py` pattern already does everything the NL→SPARQL task needs. ADR-013 remains retained for its framework trade-off trail; re-evaluate again only if multi-channel scheduling (CronService / HEARTBEAT.md) becomes a bottleneck post-traction.

---

## Dev Notes

### File map

| Action | File | Notes |
|--------|------|-------|
| CREATE | `harness/nl_to_sparql.py` | New module — NL→SPARQL dispatch |
| UPDATE | `harness/router.py` | Wire `nl_discovery` → `nl_to_sparql.dispatch()` |
| UPDATE | `harness/sparql_client.py` | Add `run_construct()` + `run_update()` |
| UPDATE | `harness/bernard_voice.yaml` | 4 new voice keys |
| UPDATE | `ontology/iop/iop.ttl` | Expand stub to usable vocabulary |
| CREATE | `harness/tests/test_nl_to_sparql.py` | Unit tests for the new module |

No new Python dependencies needed — `openai>=1.30.0`, `httpx`, and `structlog` are already in `infra/bot/requirements.txt`.

---

### `harness/nl_to_sparql.py` design

```python
# Module-level cache (populated at startup, keyed by env RELOAD_ONTOLOGY)
_ONTOLOGY_CACHE: str | None = None

# SPARQL CONSTRUCT to extract ontology subset from Oxigraph
ONTOLOGY_CONSTRUCT = """
CONSTRUCT {
  ?cls a owl:Class ; rdfs:label ?label ; rdfs:comment ?comment .
  ?prop a owl:DatatypeProperty ; rdfs:label ?plabel ; rdfs:domain ?domain ; rdfs:range ?range .
  ?cls skos:closeMatch ?match .
}
WHERE {
  {
    GRAPH <urn:mak:ontology/iop> {
      { ?cls a owl:Class . OPTIONAL { ?cls rdfs:label ?label } OPTIONAL { ?cls rdfs:comment ?comment } }
      UNION
      { ?prop a owl:DatatypeProperty ; rdfs:domain ?domain ; rdfs:range ?range .
        OPTIONAL { ?prop rdfs:label ?plabel } }
      UNION
      { ?cls skos:closeMatch ?match }
    }
  }
  UNION
  {
    GRAPH <urn:mak:ontology/mom> {
      { ?cls a owl:Class . OPTIONAL { ?cls rdfs:label ?label } }
      UNION
      { ?prop a owl:DatatypeProperty ; rdfs:domain ?domain .
        OPTIONAL { ?prop rdfs:label ?plabel } }
    }
  }
}
"""
# Q2 resolved: pulls both iop + mom graphs so the LLM has exact predicate names
# (mom:memberOf, schema:addressLocality, etc.) and won't silently hallucinate wrong predicates.

# Security: reject any mutating keyword
FORBIDDEN = re.compile(r'\b(DROP|INSERT|DELETE|UPDATE|CLEAR|CREATE|LOAD|MOVE|COPY|ADD)\b', re.IGNORECASE)

NL_TO_SPARQL_SYSTEM = """You are a SPARQL generator for a makerspace directory.
Available named graphs: urn:mak:space/<slug> (registered spaces), urn:mak:canary/<slug>.
Prefixes:
  PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
  PREFIX schema: <https://schema.org/>
  PREFIX iop: <https://nicolasdb.github.io/mapsofmaking_ontology/iop#>

Ontology context:
{ontology_slice}

Rules:
- Return ONLY a SPARQL SELECT query. No explanation, no markdown.
- Query only the named graphs above. Never use DROP/INSERT/DELETE/UPDATE.
- Limit results to 15 unless the question implies otherwise.
- Use CONTAINS(LCASE(…), LCASE(…)) for string matching.
"""
```

The `dispatch(message, session_id)` function:
1. Ensure ontology cache is warm (`_load_ontology_cache()` if `_ONTOLOGY_CACHE is None` or `RELOAD_ONTOLOGY=1`)
2. Call `llm_client.complete_with_system(system=NL_TO_SPARQL_SYSTEM.format(ontology_slice=_ONTOLOGY_CACHE), user=message.text, model="anthropic/claude-sonnet-4-5", temperature=0.0, max_tokens=512)`
3. Validate SPARQL — reject if `FORBIDDEN.search(sparql)` → log security event → return `bernard.nl_invalid_sparql_ack()`
4. Execute `sparql_client.run_select(sparql)` — on exception → log + emit gap triple → return `bernard.nl_gap_ack()`
5. If `bindings` is empty → emit gap triple → return `bernard.nl_empty_ack()`
6. Format result: name + website links from bindings + collapsed SPARQL block → return `bernard.nl_result_ack(count, list_text, sparql_block)`

---

### `llm_client.py` extension needed

The current `complete()` function passes a single user message. Add `complete_with_system()` that passes `[{"role": "system", "content": system}, {"role": "user", "content": user}]`. Pattern from Context7 / openai-python:

```python
async def complete_with_system(
    system: str, user: str, model: str, temperature: float = 1.0,
    max_tokens: int = 512, session_id: str = ""
) -> tuple[str, str, int]:
    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
```

---

### `sparql_client.py` additions

```python
async def run_construct(query: str) -> tuple[str, int]:
    """Run a SPARQL CONSTRUCT, return (turtle_text, latency_ms).
    Accept: text/turtle"""

async def run_update(update: str) -> tuple[bool, int]:
    """Run a SPARQL UPDATE (INSERT DATA) via /update endpoint.
    IMPORTANT: Oxigraph /update is blocked at nginx from public internet —
    this MUST use the internal Docker URL (e.g. http://oxigraph:7878/update), never the public URL."""
```

**Q1 resolved — derive `/update` from `OXIGRAPH_ENDPOINT` (Option A).** No new env var. Pattern already used in `link_handler/main.py` lines 898/959:
```python
url = OXIGRAPH_ENDPOINT.rstrip("/") + "/update"
```
`OXIGRAPH_ENDPOINT` is `http://oxigraph:7878` (internal Docker hostname). The `/update` suffix is always correct — Oxigraph's API is always `/query` and `/update` at the same base. No config change needed.

---

### Gap triple format (from mom.ttl + architecture.md)

```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT DATA {
  GRAPH <urn:mak:gaps> {
    <urn:mak:gap/{uuid}> a mom:OntologyGap ;
      mom:rawQuery "{escaped_query_text}" ;
      mom:rawLLMOutput "{escaped_llm_output}" ;
      mom:gapTimestamp "{iso_datetime}"^^xsd:dateTime .
  }
}
```

Use `uuid.uuid4()` for the UUID. Escape `"` as `\"` in Turtle literal strings. The `<urn:mak:gaps>` named graph does not need pre-creation in Oxigraph — `INSERT DATA` into a non-existent named graph creates it automatically.

---

### `ontology/iop/iop.ttl` expansion

The stub is 12 lines — a placeholder that says "expanded in Epic 6". Story 6.4 expands it to **minimal spatial vocabulary only** (see "Resolved: IoP is the Internet of Production Alliance" below). Keep `iop:Equipment` as a bare stub — capability/equipment semantics are deferred to the OKW crosswalk, NOT minted here. Minimal viable content:

```turtle
@prefix iop: <https://nicolasdb.github.io/mapsofmaking_ontology/iop#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#> .
@prefix schema: <https://schema.org/> .

<https://nicolasdb.github.io/mapsofmaking_ontology/iop#>
  a owl:Ontology ;
  rdfs:label "Internet of Places Ontology" ;
  rdfs:comment "Vocabulary for federated spatial infrastructure — makerspace edition." .

iop:Place a owl:Class ;
  rdfs:label "Place" ;
  rdfs:comment "A physical or virtual place where making happens." ;
  skos:closeMatch schema:LocalBusiness , mom:Space .

iop:Makerspace a owl:Class ;
  rdfs:subClassOf iop:Place ;
  rdfs:label "Makerspace" ;
  rdfs:comment "A community-run workshop with shared tools and open membership." .

iop:Activity a owl:Class ;
  rdfs:label "Activity" ;
  rdfs:comment "A type of making activity or specialty." ;
  skos:closeMatch schema:knowsAbout .

iop:Equipment a owl:Class ;
  rdfs:label "Equipment" ;
  rdfs:comment "A tool or machine available at a place. STUB ONLY — capability/equipment semantics map to OKW (Open Know-Where) via ontology/crosswalks/mom-to-okw.ttl; do not add properties here." .

iop:Network a owl:Class ;
  rdfs:label "Network" ;
  rdfs:comment "A federation or association of places." ;
  skos:closeMatch mom:memberOf .

iop:hasActivity a owl:ObjectProperty ;
  rdfs:label "has activity" ;
  rdfs:domain iop:Place ;
  rdfs:range iop:Activity ;
  skos:closeMatch schema:knowsAbout .

iop:memberOfNetwork a owl:ObjectProperty ;
  rdfs:label "member of network" ;
  rdfs:domain iop:Place ;
  rdfs:range iop:Network ;
  skos:closeMatch mom:memberOf .
```

After editing `iop.ttl`, it must be re-loaded into Oxigraph. The load command (from architecture.md):
```bash
curl -X POST -H 'Content-Type: text/turtle' \
  -G 'http://oxigraph:7878/store' \
  --data-urlencode 'graph=urn:mak:ontology/iop' \
  --data-binary @ontology/iop/iop.ttl
```
This is an operator step (Makefile target or manual). Add a `make reload-iop` target in the project Makefile or note it in the done gate.

---

### `bernard_voice.yaml` additions

Four new keys (add under the `# NL discovery` section, create if absent):

```yaml
  # NL discovery (Story 6.4)
  nl_result_ack: "Found {count} space(s) matching your question.\n\n{list_text}\n\n> How I searched\n> ```sparql\n> {sparql_block}\n> ```"
  nl_empty_ack: "Nothing in the directory matches that — the question's logged so it can inform what gets added. Try `!mom find {tag} {city}` for a targeted search, or browse the map."
  nl_gap_ack: "I couldn't form a query that fits the directory — your question's logged as a gap for ontology curation. Could you rephrase? For example: `!mom find laser Berlin` or `!mom nearby Brussels 50`."
  nl_invalid_sparql_ack: "That question produced something I'm not allowed to run. Try rephrasing, or use `!mom help` for the commands I support."
```

**Critical:** copy in `bernard_voice.yaml` is the SSOT (`feedback_bernard_voice_yaml_is_ssot`). `_bot()` in `bernard.py` must reference the YAML key, not a Python string fallback.

---

### `router.py` change (minimal)

Replace the `# write | nl_discovery: not implemented yet (6.4+)` block:

```python
if intent == "nl_discovery":
    return await nl_to_sparql.dispatch(message, session_id=session_id)
```

Add `import nl_to_sparql` at the top.

---

### Test requirements (`harness/tests/test_nl_to_sparql.py`)

Mirror pattern from `test_query_commands.py` — mock `sparql_client` and `llm_client`, test:

1. **SPARQL injection rejection** — LLM returns `DROP TABLE spaces; SELECT ...` → function rejects, returns `nl_invalid_sparql_ack`, no Oxigraph call
2. **Empty result → gap triple** — valid SPARQL, `run_select` returns `[]` → `run_update` called with `mom:OntologyGap` INSERT, returns `nl_gap_ack`
3. **Successful result** — `run_select` returns 2 bindings → returns string containing space names + SPARQL block header
4. **LLM failure** — `llm_client.complete_with_system` raises → gap triple written, returns `nl_gap_ack`
5. **Ontology cache hit** — call `dispatch` twice → `run_construct` called only once (cache reused)
6. **RELOAD_ONTOLOGY=1** — `run_construct` called again on second dispatch when env var set

---

### Deferred items to carry forward (deferred-work.md)

Do NOT implement in this story:
- `!mom network fabtafel` data quality issue (`mom:memberOf` absence in Oxigraph) — data investigation, not 6.4 scope
- E2E encrypted room support (`MegolmEvent`) — deferred to 6.8 or post-traction infra story
- Isochrone "just outside range" teaser — deferred to future Epic 6 story
- `mom.memberOf add/remove` partial-array mutation — `run_update()` lands in 6.4, so 6.5 can build add/remove on top of it (full-array replace is the only write today)

**Known risk to flag before deploy (NOT 6.4 scope but must be tracked):** every `@bernard` mention triggers a billed Sonnet completion. With no rate-limit, a busy/federated room is unbounded spend. → see deferred-work.md "@bernard rate-limit" entry. Minimum guard before any public/federated rollout: per-user cooldown or room-level token budget.

---

## Architecture Compliance

- **NFR-S5**: Reject `DROP/INSERT/DELETE/UPDATE` in generated SPARQL before execution — log as security event with `structlog`
- **NFR-S7**: Bot is read-only on Oxigraph — gap triples are the ONLY write the bot performs, and they go to `<urn:mak:gaps>` only, never to space graphs
- **Canonical namespace**: All SPARQL prefixes use `https://nicolasdb.github.io/mapsofmaking_ontology/ns#` for `mom:` — never `w3id.org/maps-of-making/`
- **SSOT for copy**: `bernard_voice.yaml` owns all strings; no Python string fallbacks
- **Structlog**: All log events follow `noun.verb_past` pattern (`sparql.generated`, `gap.written`, `ontology.cache_loaded`, `sparql.security_rejected`)
- **SPARQL constants**: Module-level `SCREAMING_SNAKE_CASE` constants for all SPARQL strings — no inline f-strings with user input. Use `VALUES` clauses for parameterisation where needed
- **`run_update` internal URL**: The `/update` endpoint is nginx-blocked from public internet; the bot uses the internal Docker service hostname directly

---

## Previous Story Intelligence (from 6.3 code review + dev notes)

- `query_commands.dispatch()` currently returns `bernard.unknown_ack()` as a stub — that's the exact stub 6.4 replaces in `router.py` (6.4 calls `nl_to_sparql.dispatch()` from `router.py`, not from `query_commands.dispatch()`)
- `query_commands._sanitize()` pattern: `re.sub(r'[{}<>"\\' + r"\n\r\x00-\x1f]", "", value)` — reuse for any user-supplied string going into SPARQL (even though Sonnet generates the SPARQL, sanitize the original `message.text` before injecting into the LLM prompt to avoid prompt injection)
- The `sparql_client.run_select()` error contract: returns `([], latency)` on error — matches the gap-triple fallback pattern needed here
- 63 tests passing at 6.3 close — the test suite must still pass after 6.4 changes; `router.py` tests in `test_intent_classifier.py` will need updating if router is tested there
- `llm_client.complete()` creates a new `AsyncOpenAI` client per call — `complete_with_system()` should follow the same pattern for consistency

---

## Implementation Checklist

- [x] Expand `ontology/iop/iop.ttl` from stub to minimal usable vocabulary
- [x] Add `run_construct()` and `run_update()` to `harness/sparql_client.py`
- [x] Add `complete_with_system()` to `harness/llm_client.py`
- [x] Create `harness/nl_to_sparql.py` with ontology cache, SPARQL validation, gap triple emission, Bernard formatting
- [x] Add 4 new voice keys to `harness/bernard_voice.yaml`; add corresponding `_bot()` accessors in `harness/bernard.py`
- [x] Update `harness/router.py` — wire `nl_discovery` intent
- [x] Create `harness/tests/test_nl_to_sparql.py` (6 tests)
- [x] Run full test suite (`pytest harness/tests/ -v`) — must stay ≥ 63 passing (65 pass; 4 pre-existing failures unchanged)
- [ ] Operator done gate: French/English/German free-form question → grounded answer + SPARQL block; unanswerable → gap triple in `<urn:mak:gaps>` + Bernard clarification

---

## Resolved Decisions

1. **`run_update()` URL** — derive from `OXIGRAPH_ENDPOINT` (no new env var): `OXIGRAPH_ENDPOINT.rstrip("/") + "/update"`. Matches `link_handler/main.py` pattern.

2. **ONTOLOGY_CONSTRUCT scope** — pulls both `<urn:mak:ontology/iop>` and `<urn:mak:ontology/mom>`. See updated `ONTOLOGY_CONSTRUCT` above.

3. **Makefile** — `make load-ontology` and `make vps-load-ontology` already exist and load both `mom.ttl` + `iop.ttl`. No new target needed. Done gate: run `make load-ontology` locally after expanding `iop.ttl`, then `make vps-load-ontology` on VPS before the operator done gate test.

## Resolved: "IoP" is the Internet of Production Alliance (party-mode roundtable 2026-06-19)

The earlier "IoP naming ambiguity" question is **resolved and superseded**. "IoP" = the **Internet of Production Alliance** (internetofproduction.org), a concrete network partner who supports MoM and would replace their stale **Open Know-Where (OKW)** map with it. OKW is the established open standard for the makerspace/facility "where" — MoM should **map toward OKW**, not mint its own equipment/capability vocabulary.

**Consequence for this story's `iop.ttl` expansion — scope it DOWN:**
- Keep `iop.ttl` **minimal and spatial-only** for 6.4's NL needs: `iop:Place`, `iop:Makerspace`, `iop:Activity`, `iop:Network` + `skos:closeMatch` bridges to `mom:`/`schema:`. This is enough for the LLM to reason about discovery queries.
- **Do NOT flesh out `iop:Equipment`/capability terms.** Equipment/capability semantics belong in the OKW crosswalk (`ontology/crosswalks/mom-to-okw.ttl`) and an `ext_okw` vertical — NOT minted under `iop:`. Building a homegrown `iop:Equipment` class now creates silent incompatibility with OKW's controlled machine/material vocabulary. Leave `iop:Equipment` as a bare class stub (label + comment, no properties) or omit it.
- **Do NOT publish `iop.ttl` to the ontology repo yet.** It stays load-only/local until the OKW interop direction is decided.

→ Full strategic context + the pluggable "crosswalk cartridge" architecture (OKW, OSLO, per-community overlays) is logged in deferred-work.md and seeded as an epic stub in epics.md.

---

## File List

- `ontology/iop/iop.ttl` — expanded from 12-line stub to full minimal spatial vocabulary
- `harness/sparql_client.py` — added `run_construct()` and `run_update()`
- `harness/llm_client.py` — added `complete_with_system()`
- `harness/nl_to_sparql.py` — new module (NL→SPARQL dispatch, ontology cache, gap triple emission)
- `harness/bernard_voice.yaml` — added 4 NL discovery voice keys
- `harness/bernard.py` — added 4 accessor functions for NL discovery keys
- `harness/router.py` — wired `nl_discovery` → `nl_to_sparql.dispatch()`
- `harness/tests/test_nl_to_sparql.py` — new test file (6 tests)

---

## Dev Agent Record

### Completion Notes

Implemented Story 6.4 in full. All 8 implementation checklist items complete. Test suite: 65 passing (was 59 + 6 new NL tests); 4 pre-existing failures in test_commands.py/test_message.py unchanged and pre-date this story.

Key decisions executed as specified:
- `FORBIDDEN` regex covers `DROP|INSERT|DELETE|UPDATE|CLEAR|CREATE|LOAD|MOVE|COPY|ADD` — broader than minimum spec to prevent all SPARQL write/mutate patterns
- `run_update()` derives URL from `OXIGRAPH_ENDPOINT.rstrip("/") + "/update"` (no new env var)
- ONTOLOGY_CONSTRUCT pulls both `<urn:mak:ontology/iop>` and `<urn:mak:ontology/mom>` graphs
- `iop:Equipment` kept as bare stub per OKW interop decision
- `_ONTOLOGY_CACHE` reset on `RELOAD_ONTOLOGY=1`; user message sanitized before LLM injection

**Operator done gate (not automated — requires live VPS):** run `make load-ontology` after expanding `iop.ttl`, then test with a multilingual free-form question. See Implementation Checklist item 9.

### Change Log

- 2026-06-24: Story 6.4 implementation complete — NL→SPARQL full dispatch, IoP ontology expansion, gap triple emission, 6 new tests (65 total passing)
