---
name: space-jsonld-generator
description: Generate a Maps of Making (MOM) compliant Space JSON profile for a makerspace. Use when users ask to "create a space JSON", "generate a coordinator URL document", "make a test space file", "draft a JSON for [space name]", "set up a makerspace entry", or "register a makerspace" for the Maps of Making registry.
---

# Space JSON Generator

Produces a single JSON document describing one making space (fab lab, hackerspace, repair café, makerspace, etc.) that:

1. Validates against the Maps of Making `mak-link-handler` `/api/validate-url` endpoint.
2. Conforms to **SpaceAPI v13–15** as the primary format — the format most spaces already use or can easily produce.
3. Can optionally include `@context` and mom-specific fields (`mom:operationalState`, `mom:geolocationFidelity`, `knowsAbout`) for richer ingestion and future JSON-LD export.
4. Can be hosted at any public URL (GitHub Pages, gist raw, S3, the space's own website) and registered via the "Add your space" flow.

This skill is the human/LLM-facing counterpart to `infra/link_handler/main.py:_fetch_and_validate`. The validator is the source of truth — when in doubt, mirror its expectations.

## Core principle: SpaceAPI v15 first

The primary input format is **standard SpaceAPI v15 JSON** with a few optional mom extension fields. No `@context` is required for ingestion. The mom transformer enriches the data internally and stores it as RDF triples in Oxigraph.

- A JSON file with just `space` + `location.lat/lon` earns a pin on the map.
- Adding more SpaceAPI fields unlocks richer cards and SpaceAPI ecosystem interop.
- Adding `knowsAbout` (a mom extension, not in SpaceAPI) tags the space with maker activities.
- JSON-LD export (`@context`, `@type`, `@id`) is a future feature for coordinators who want to export their enriched profile — it is not required for registration.

## Subset tiers — what your JSON unlocks

| Tier | `subset_score` | Required fields | What it unlocks |
|------|---------------|-----------------|-----------------|
| `none` | 0 | (validation failed or missing name/coords) | Nothing — not registered |
| `mom:required` | 1 | `space` (or `schema:name`) + coords | Pin on the map |
| `mom:card` | 2 | + `url` + `opening_hours` | Full detail card (Zone 2) |
| `spaceapi:compatible` | 3 | + `api_compatibility` + `logo` + `contact` + `state` | Passes `validator.spaceapi.io`; interop with mapall.space etc. |

## Inputs to gather

### Required (mom:required tier)
- **name** (→ `space`) — human-readable space name
- **latitude / longitude** (→ `location.lat`, `location.lon`) — decimal degrees, WGS84

### To reach mom:card tier
- **website** (→ `url`)
- **opening hours** (→ `opening_hours`) — schema.org string format, e.g. `"Mo-Fr 10:00-18:00"`

### To reach spaceapi:compatible tier
- **api_compatibility** — list, e.g. `["15"]`
- **logo** — URL to logo image
- **contact** — object with at least one of `email`, `phone`, `twitter`, `mastodon`, `irc`, `discord`, etc.
- **state** — dynamic open/closed state, e.g. `{"open": null}` (unknown) or `{"open": true}`

### Strongly recommended
- **address** (→ `location.address`) — full address as a single string
- **country_code** (→ `location.country_code`) — ISO-3166-1 alpha-2
- **description** — free-text description of the space
- **knowsAbout** — list of maker activity tags (lowercase-hyphenated recommended, e.g. `"3d-printing"`, `"electronics"`, `"laser-cutting"`). **mom extension — not in SpaceAPI spec; ignored by SpaceAPI validators.**
- **mom:operationalState** — `active` | `dormant` | `closed`. Long-term lifecycle status. Different from `state` (which is dynamic open/closed). mom extension.
- **mom:geolocationFidelity** — `exact` | `approximate` | `city-only`. mom extension.

### PII caution
Organisational `contact.email` is allowed (a LocalBusiness contact, not personal data). Only include it if the space publishes it publicly. Personal `foaf:mbox` triggers a warning in the validator.

## Output format — canonical SpaceAPI v15 template

```json
{
  "api_compatibility": ["15"],
  "space": "Example Space",
  "logo": "https://example.org/logo.png",
  "url": "https://example.org",
  "description": "A community making space.",
  "location": {
    "lat": 50.8503,
    "lon": 4.3517,
    "address": "Rue de l'Exemple 12, 1000 Brussels, Belgium",
    "country_code": "BE",
    "timezone": "Europe/Brussels"
  },
  "state": { "open": null },
  "contact": {
    "email": "contact@example.org",
    "twitter": "@examplespace"
  },
  "opening_hours": "Mo-Fr 10:00-18:00, Sa 10:00-16:00",
  "knowsAbout": ["3d-printing", "electronics", "laser-cutting"],
  "mom:operationalState": "active",
  "mom:geolocationFidelity": "exact"
}
```

### Output Notes
- Coordinates MUST be numeric floats, not strings.
- `state` (SpaceAPI dynamic open/closed) ≠ `mom:operationalState` (long-term lifecycle). Both can coexist.
- `knowsAbout` and `mom:*` keys are ignored by SpaceAPI validators — they are mom extensions.
- Fields can be omitted — adding them unlocks higher tiers.
- SpaceAPI validators accept v13, v14, v15. Use `"api_compatibility": ["15"]` for new files.

## Validator contract (must satisfy)

The mom `/api/validate-url` endpoint requires:
- HTTP 200 with `Content-Type: application/json`
- Valid JSON (quoted keys — not HJSON or JSON5)
- Either `space`, `schema:name`, or `name` present and non-empty
- Either `location.lat`/`lon` present and float-coercible
- Response under ~60s; redirects followed by the heartbeat fetcher

The SpaceAPI v15 validator at `validator.spaceapi.io` additionally requires `api_compatibility`, `logo`, `state`, `contact`, and a `location.address` string.

## Workflow

1. **Identify intent** → confirm it is a JSON generation request.
2. **Determine target tier** → ask which fields the coordinator has. Default goal: reach `mom:card`. `spaceapi:compatible` is the stretch goal.
3. **Gather required fields** → batch question for name + lat/lon (or address for geocoding).
4. **Geocode if needed** → if address provided but no coordinates: call geocoding → set `mom:geolocationFidelity: "approximate"`.
5. **Check for PII fields** → warn if user includes personal email/phone, ask for confirmation, don't block.
6. **Emit JSON** → use the SpaceAPI v15 template, omitting fields the coordinator doesn't have.
7. **Provide next steps** → hosting options + validation command + what each tier unlocks.

### Error recovery
- **"Response is not valid JSON"** → most common cause: file served as HJSON (unquoted keys) or with a BOM. Fix: ensure keys are quoted, save as UTF-8 without BOM.
- **"Name not found"** → add `"space": "Space Name"` at the top level.
- **Coordinates not found** → add `"location": { "lat": 50.83, "lon": 4.38 }`.
- **SpaceAPI: `'logo' is a required property`** → add logo URL, or accept mom:card tier (no logo needed).
- **If geocoding fails** → ask user for manual coordinates.

## Common Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Response is not valid JSON` | HJSON / unquoted keys | Quote all keys, save as UTF-8 |
| `Name not found` | Missing `space` key | Add `"space": "Name"` |
| `Coordinates not found` | Missing `location.lat/lon` | Add numeric lat/lon |
| SpaceAPI: `'logo' is required` | Missing logo for spaceapi:compatible tier | Add logo URL |

## Validation commands

```bash
# mom validator (local)
curl -X POST http://localhost/api/validate-url \
  -H 'Content-Type: application/json' \
  -d '{"url":"<your-public-url>"}'

# SpaceAPI official validator:
# https://validator.spaceapi.io  (paste URL)

# Dual validation (mom + SpaceAPI v15):
python scripts/validate_dual.py <your-public-url>
```

## Optional: JSON-LD enrichment

If a coordinator wants their file to be usable as linked data (for export or federation), they can add a `@context` block. This is purely additive — the mom ingest pipeline ignores it and the SpaceAPI validator ignores `@context`, `@type`, and `@id` keys.

```json
{
  "@context": {
    "mom": "https://nicolasdb.github.io/mapsofmaking_ontology/ns#",
    "schema": "https://schema.org/",
    "space": "schema:name",
    "url": "schema:url",
    "location": "schema:geo",
    "lat": "schema:latitude",
    "lon": "schema:longitude",
    "address": "schema:address",
    "opening_hours": "schema:openingHours",
    "knowsAbout": "schema:knowsAbout"
  },
  "@type": "mom:Space",
  "@id": "https://example.org/spaces/example",
  "api_compatibility": ["15"],
  "space": "Example Space",
  ...
}
```

This is the seed for a future `mak-space-bot` export feature — not required for the demo or pilot.

## Future promotion path

- v1 (now): LLM skill, manual hosting, SpaceAPI v15 JSON.
- v2: a `/api/draft-space` endpoint in `mak-link-handler`.
- v3: a Discord/Telegram bot (Epic 6) that walks a coordinator through the fields and publishes to a Maps-of-Making-hosted gist.

When promoting, keep the validator contract above as the canonical schema — the bot's output and this skill's output must stay byte-compatible with the Pydantic `SpaceAPISchema` model in `infra/link_handler/main.py`.
