---
name: space-jsonld-generator
description: Generate a Maps of Making (MOM) ontology-compliant Space JSON-LD document for a makerspace. Use when users ask to "create a space JSON-LD", "generate a coordinator URL document", "make a test space file", "draft a JSON-LD for [space name]", "set up a makerspace entry", or "register a makerspace" for the Maps of Making registry.
---

# Space JSON-LD Generator

Produces a single JSON-LD document describing one making space (fab lab, hackerspace, repair café, makerspace, etc.) that:

1. Validates against the Maps of Making `mak-link-handler` `/api/validate-url` endpoint.
2. Conforms to the `mom` ontology at `https://nicolasdb.github.io/mapsofmaking_ontology/`.
3. Can be hosted at any public URL (GitHub Pages, gist raw, S3, the space's own website) and registered via the "Add your space" flow.

This skill is the human/LLM-facing counterpart to `infra/link_handler/main.py:_fetch_and_validate`. The validator is the source of truth — when in doubt, mirror its expectations.

## When to invoke

- User asks to "create a space JSON-LD", "generate a coordinator URL document", "make a test space file", "draft a JSON-LD for {space name}".
- User wants test fixtures for the coordinator onboarding flow.
- User is preparing to publish a makerspace's data at a real URL.

## Inputs to gather

### Required
- **name** — human-readable space name (e.g. "Openfab Brussels")
- **latitude / longitude** — decimal degrees, WGS84. If unknown, ask for an address and geocode (or instruct the user to obtain coordinates).

### Strongly recommended
- **streetAddress, postalCode, addressLocality, addressCountry** — full postal address
- **website (schema:url)** — the space's main public website
- **description** — 1–3 sentences
- **specialties (schema:knowsAbout)** — list of activity tags (e.g. "3d-printing", "electronics", "woodworking", "textile", "bio-lab"). Use lowercase-hyphenated.
- **operationalState** — one of `seed`, `active`, `dormant`, `closed`. Default `active`.

### Optional
- **openingHours** — schema.org openingHoursSpecification format
- **founded** (schema:foundingDate, ISO 8601)
- **email / contactPoint** — only if the space explicitly publishes it. Otherwise leave out (the validator scans for PII fields and will warn).

## Output format

Always emit a single JSON document with this shape:

```json
{
  "@context": {
    "mom": "https://nicolasdb.github.io/mapsofmaking_ontology/ns#",
    "schema": "https://schema.org/",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@type": "mom:Space",
  "@id": "https://example.org/spaces/fab-lab-brussels",
  "schema:name": "Fab Lab Brussels",
  "schema:description": "A community fab lab in central Brussels...",
  "schema:url": "https://fablab-brussels.example.org",
  "schema:geo": {
    "@type": "schema:GeoCoordinates",
    "schema:latitude": 50.8503,
    "schema:longitude": 4.3517
  },
  "schema:address": {
    "@type": "schema:PostalAddress",
    "schema:streetAddress": "Rue de l'Exemple 12",
    "schema:postalCode": "1000",
    "schema:addressLocality": "Brussels",
    "schema:addressCountry": "BE"
  },
  "schema:knowsAbout": ["3d-printing", "electronics", "laser-cutting"],
  "mom:operationalState": "active",
  "mom:geolocationFidelity": "exact"
}
```

### Output Notes
- `@id` should be the public URL where the document will be hosted (or a stable IRI for the space).
- Coordinates MUST be numeric, not strings.
- `mom:geolocationFidelity` ∈ {`exact`, `approximate`, `city-only`}. Use `approximate` if you geocoded from an address; `exact` only if the coordinates come from the space itself.
- Do NOT include `email`, `telephone`, `contactPoint.email`, or other PII unless the user explicitly confirms the space publishes it. The validator flags these.

### Additional Schema Properties (Optional)

| Field | Schema Property | Example |
|-------|-----------------|---------|
| Opening hours | `schema:openingHoursSpecification` | See schema.org format |
| Founding date | `schema:foundingDate` | "2015-03-15" |
| Logo/Image | `schema:image` | URL to logo |
| Same-as links | `schema:sameAs` | Social media URLs |

## Validator contract (must satisfy)

The `/api/validate-url` endpoint requires:
- HTTP 200 with `Content-Type: application/json` (or anything `httpx` parses as JSON)
- `schema:name` present and non-empty (also accepts plain `"name"`)
- `schema:geo.schema:latitude` + `schema:geo.schema:longitude` present and float-coercible (also accepts plain `geo.lat`/`geo.lon`)
- HTTPS scheme strongly preferred; `http://` is allowed but discouraged
- Response under ~10s, no redirects (link handler uses `follow_redirects=False`)

## Workflow

1. **Identify intent** → confirm it is a JSON-LD generation request
2. **Gather required fields** → batch question for name + lat/lon (or address)
3. **Geocode if needed** → if address provided but no coordinates:
   - Call geocoding service → set `geolocationFidelity: "approximate"`
   - Document source in response
4. **Check for PII fields** → warn if user includes email/telephone, ask for confirmation, don't block.
5. **Emit JSON-LD** → validate structure matches schema
6. **Provide next steps** → hosting options + validation curl command

### Error recovery
- **If validation fails** → parse error message, identify missing fields, re-prompt user
- **If geocoding fails** → ask user for manual coordinates
- **If address is ambiguous** → present top 3 candidates and ask user to confirm

## Common Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `latitude/longitude must be numeric` | String coordinates | Convert to float |
| `name is required` | Missing schema:name | Add from user input |
| `PII detected: email field` | Email included | Remove or confirm space publishes it |

## Edge Cases

- **No coordinates available**: Ask for address, geocode via Nominatim, set fidelity to `approximate`
- **Address in non-Latin script**: Request transliteration before geocoding
- **Very large/specialized space**: Add `schema:description` with capacity info
- **Multiple locations**: Generate separate JSON-LD for each location
- **Affiliated with larger org**: Consider adding `schema:memberOf` if applicable

## Prompt Templates

### Initial field gathering
```
To create a JSON-LD for [space name], I need a few details:
- Coordinates (decimal degrees, e.g., 50.8503, 4.3517) OR full address
- Specialties (e.g., 3d-printing, electronics, woodworking)

Optional but helpful: website URL, description, founding date.
```

### PII warning
```
Note: The validator flags personal data fields. I will not include email/phone unless your space explicitly publishes these on its website.
```

### Confirmation prompt
```
Here is the JSON-LD for [space name]. Before hosting:

1. Review the data for accuracy
2. Choose a hosting location (GitHub Pages, gist, etc.)
3. Run this command to validate:
   curl -X POST http://localhost/api/validate-url \
     -H 'Content-Type: application/json' \
     -d '{"url":"<your-public-url>"}'
```

## Example Conversations

**User:** "Generate JSON-LD for a fab lab in Berlin"
**Agent:** "To create a JSON-LD for your fab lab, I need: 1) Coordinates (decimal degrees) or full address, 2) Specialties (e.g., 3d-printing, electronics). What are your space's coordinates and main activities?"

**User:** "I have a makerspace called TechHub, it's at 123 Main St, London, and we do 3D printing and electronics"
**Agent:** [Geocodes address, sets fidelity to "approximate", produces full JSON-LD with all provided fields]

**User:** "Can you add our email to the JSON-LD?"
**Agent:** "I can include email only if your makerspace explicitly publishes it on your website. The validator flags personal data. Do you publish this email publicly?"

## Future promotion path

This skill is the seed for a future `mak-space-bot` service:
- v1 (now): LLM skill, manual hosting.
- v2: a `/api/draft-space` endpoint in `mak-link-handler` that takes `{name, address, ...}` and returns the JSON-LD body.
- v3: a Discord/Telegram bot (Epic 6) that walks a coordinator through the fields conversationally and publishes to a Maps-of-Making-hosted gist on their behalf.

When promoting, keep the validator contract above as the canonical schema — the bot's output and this skill's output must stay byte-compatible.
