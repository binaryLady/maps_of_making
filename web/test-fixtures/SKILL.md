---
name: space-jsonld-generator
description: Generate a Maps of Making (MOM) ontology-compliant Space JSON-LD document for a makerspace. Use when users ask to "create a space JSON-LD", "generate a coordinator URL document", "make a test space file", "draft a JSON-LD for [space name]", "set up a makerspace entry", or "register a makerspace" for the Maps of Making registry.
---

# Space JSON-LD Generator

Produces a single JSON-LD document describing one making space (fab lab, hackerspace, repair café, makerspace, etc.) that:

1. Validates against the Maps of Making `mak-link-handler` `/api/validate-url` endpoint.
2. Conforms to the `mom` ontology at `https://nicolasdb.github.io/mapsofmaking_ontology/`.
3. **Is byte-compatible with the SpaceAPI v14 validator at `validator.spaceapi.io`** when the optional fields are filled in.
4. Can be hosted at any public URL (GitHub Pages, gist raw, S3, the space's own website) and registered via the "Add your space" flow.

This skill is the human/LLM-facing counterpart to `infra/link_handler/main.py:_fetch_and_validate`. The validator is the source of truth — when in doubt, mirror its expectations.

## Core principle: one file, two validators

We do NOT publish two separate files (one for mom, one for SpaceAPI). Instead, we use **SpaceAPI v14's flat key shape** as the document body, and add a JSON-LD `@context` that aliases each flat key to its mom/schema.org IRI. Both validators see what they expect:

- The SpaceAPI validator reads `space`, `location.lat`, `location.lon`, `state`, `contact`, `api_compatibility` — the keys it requires.
- The mom validator (and Oxigraph ingest) reads the same JSON, but resolves keys through `@context` to RDF triples (`schema:name`, `schema:geo.schema:latitude`, `mom:operationalState`…).

The document can be partial — coordinators publish what they have, and adding fields unlocks more features. A doc with just `space` + `location.lat/lon` won't pass SpaceAPI v14 (which mandates more fields), but it WILL pass mom validation and earn a pin on the map.

## Subset tiers — what your JSON unlocks

| Tier | `subset_score` | Required fields | What it unlocks |
|------|---------------|-----------------|-----------------|
| `none` | 0 | (validation failed or missing name/coords) | Nothing — not registered |
| `mom:required` | 1 | `space` (or `schema:name`) + coords | Pin on the map |
| `mom:card` | 2 | + `url` + `opening_hours` (`schema:openingHours`) | Full detail card (Zone 2) |
| `spaceapi:compatible` | 3 | + `api_compatibility` + `logo` + `contact` + `state` | Passes `validator.spaceapi.io`; interop with mapall.space etc. |

> **Note:** Tier names are application-level classification labels in `classify_subset()`, not ontology terms. The vocabulary lives in `mom.ttl`.

## Inputs to gather

### Required (mom:required tier)
- **name** (→ `space`) — human-readable space name
- **latitude / longitude** (→ `location.lat`, `location.lon`) — decimal degrees, WGS84

### To reach mom:card tier
- **website** (→ `url`)
- **opening hours** (→ `opening_hours`, aliased to `schema:openingHours`) — schema.org string format, e.g. `"Mo-Fr 10:00-18:00"`

### To reach spaceapi:compatible tier
- **api_compatibility** — list of SpaceAPI versions, e.g. `["14"]`
- **logo** — URL to the logo image
- **contact** — object with at least one of `email`, `phone`, `twitter`, `mastodon`, `matrix`, etc. (only fields the space publishes publicly)
- **state** — SpaceAPI dynamic state object, e.g. `{"open": null}` or `{"open": true, "lastchange": ...}`

### Strongly recommended
- **address** (→ `location.address` as a string)
- **country_code** (→ `location.country_code`, ISO-3166-1 alpha-2)
- **description**
- **knowsAbout** (→ `schema:knowsAbout`) — list of activity tags (lowercase-hyphenated)
- **mom:operationalState** — `seed` | `active` | `dormant` | `closed`. Different from SpaceAPI `state` (which is dynamic open/closed).
- **mom:geolocationFidelity** — `exact` | `approximate` | `city-only`

### PII caution
The validator scans for `foaf:mbox`. Organisational `contact.email` is allowed (LocalBusiness contact ≠ PII), but only include it if the space publishes it on their public site.

## Output format — canonical dual-shape template

```json
{
  "@context": {
    "mom": "https://nicolasdb.github.io/mapsofmaking_ontology/ns#",
    "schema": "https://schema.org/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "space": "schema:name",
    "url": "schema:url",
    "logo": "schema:logo",
    "location": "schema:geo",
    "lat": "schema:latitude",
    "lon": "schema:longitude",
    "address": "schema:address",
    "country_code": "schema:addressCountry",
    "description": "schema:description",
    "opening_hours": "schema:openingHours",
    "knowsAbout": "schema:knowsAbout",
    "contact": "schema:contactPoint",
    "api_compatibility": "mom:apiCompatibility",
    "state": "mom:dynamicState"
  },
  "@type": "mom:Space",
  "@id": "https://example.org/spaces/example",
  "api_compatibility": ["14"],
  "space": "Example Space",
  "logo": "https://example.org/logo.png",
  "url": "https://example.org",
  "description": "A community making space.",
  "location": {
    "lat": 50.8503,
    "lon": 4.3517,
    "address": "Rue de l'Exemple 12, 1000 Brussels, BE",
    "country_code": "BE"
  },
  "state": { "open": null },
  "contact": { "email": "contact@example.org" },
  "opening_hours": "Mo-Fr 10:00-18:00, Sa 10:00-16:00",
  "knowsAbout": ["3d-printing", "electronics", "laser-cutting"],
  "mom:operationalState": "active",
  "mom:geolocationFidelity": "exact"
}
```

### Output Notes
- `@id` is the semantic IRI for the space-as-entity. It does NOT need to equal the file's hosting URL (the validator ignores `@id`). Convention: a stable URL the space controls.
- Coordinates MUST be numeric, not strings.
- `state` (SpaceAPI dynamic) ≠ `mom:operationalState` (long-term lifecycle). Both can coexist.
- Keys outside SpaceAPI v14 (`mom:*`, `@type`, `@id`, `@context`) are ignored by SpaceAPI validators and parsed by mom.
- Fields can be omitted to publish a partial doc — adding them unlocks higher tiers.

## Validator contract (must satisfy)

The mom `/api/validate-url` endpoint requires:
- HTTP 200 with `Content-Type: application/json` (or anything `httpx` parses as JSON)
- Either `space`, `schema:name`, or `name` present and non-empty
- Either `location.lat`/`lon` or `schema:geo.schema:latitude`/`schema:longitude` present and float-coercible
- HTTPS preferred; `http://` allowed
- Response under ~10s, no redirects (`follow_redirects=False`)

The SpaceAPI v14 validator additionally requires `api_compatibility`, `logo`, `state`, `contact` and a `location.address` string.

## Workflow

1. **Identify intent** → confirm it is a JSON-LD generation request.
2. **Determine target tier** → ask which fields the coordinator has. Default goal: reach `mom:card` (pin + card). `spaceapi:compatible` is a stretch goal.
3. **Gather required fields** → batch question for name + lat/lon (or address).
4. **Geocode if needed** → if address provided but no coordinates: call geocoding service → set `mom:geolocationFidelity: "approximate"`.
5. **Check for PII fields** → warn if user includes personal email/phone, ask for confirmation, don't block.
6. **Emit JSON-LD** → use the dual-shape template, omitting fields the coordinator doesn't have.
7. **Provide next steps** → hosting options + dual-validation command + what each tier unlocks.

### Error recovery
- **If validation fails** → parse error message, identify missing fields, re-prompt user.
- **If geocoding fails** → ask user for manual coordinates.
- **If address is ambiguous** → present top 3 candidates and ask user to confirm.

## Common Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `latitude/longitude must be numeric` | String coordinates | Convert to float |
| `name is required` | Missing space/schema:name | Add from user input |
| SpaceAPI: `'logo' is a required property` | Missing logo for tier 3 | Add logo URL or accept mom:card tier |

## Edge Cases

- **No coordinates available**: Ask for address, geocode via Nominatim, set fidelity to `approximate`.
- **Address in non-Latin script**: Request transliteration before geocoding.
- **Multiple locations**: Generate separate JSON-LD for each location.
- **Affiliated with larger org**: Consider adding `schema:memberOf` if applicable.

## Validation command

```bash
# mom validator (local)
curl -X POST http://localhost/api/validate-url \
  -H 'Content-Type: application/json' \
  -d '{"url":"<your-public-url>"}'

# Dual validation (mom + SpaceAPI v14):
python scripts/validate_dual.py <your-public-url>
```

## Future promotion path

This skill is the seed for a future `mak-space-bot` service:
- v1 (now): LLM skill, manual hosting.
- v2: a `/api/draft-space` endpoint in `mak-link-handler`.
- v3: a Discord/Telegram bot (Epic 6) that walks a coordinator through the fields and publishes to a Maps-of-Making-hosted gist.

When promoting, keep the validator contract above as the canonical schema — the bot's output and this skill's output must stay byte-compatible with the Pydantic `SpaceAPISchema` model in `infra/link_handler/main.py`.
