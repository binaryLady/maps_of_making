# Story 3.0-A: Space Profile Card — UX Refinement

Status: ready-for-dev

## Story

As Luca, a space coordinator who just registered his lab,
I want the space profile to reflect my data accurately and give me direct control over refreshing it,
So that I trust what visitors see, know what my endpoint unlocks next, and can push an update without waiting 10 minutes.

As a visitor,
I want a clean, readable profile with honest freshness signals,
So that I can trust the information and share it easily.

**Design rationale:** MoM's value proposition is that Luca shares one URL and gets a maintained profile — no account, no form, no password. The card should make that moment tangible: what you see is what your endpoint says, timestamped and unaltered.

---

## Scope

This story refines the post-registration experience and the space profile card (formerly "detail drawer"). It does not touch ingestion, Pydantic validation, or Oxigraph write logic beyond adding three new triples.

---

## Acceptance Criteria

### AC1 — Drawer renamed to "Space Profile"

**Given** any drawer or UI string currently labelled "detail" or "card" in user-facing context

**When** rendered

**Then** it uses "Space Profile" (drawer title, any aria-label, any internal comment referencing it as a user-facing name)

**And** the HTML element id `drawer-detail` and JS references remain unchanged — this is a label-only change, not a refactor

---

### AC2 — Post-registration confirmation timing

**Given** `POST /api/register-url` succeeds and the confirmation screen renders

**When** `unlockMsg` is non-empty (subset guidance to display)

**Then** the auto-transition to the space profile fires after **8 seconds**

**When** `unlockMsg` is empty (full SpaceAPI compatibility, no guidance)

**Then** the auto-transition fires after **2 seconds**

**And** the "Opening your space card…" hint text is updated to "Opening your space profile…"

---

### AC3 — Zone 1: logo, share CTA, "last updated" timestamp

**Zone 1 layout (top to bottom):**

1. Logo thumbnail (if available) inline left of space name + `h3` name on the same line
2. Address line
3. Status badge + network membership badges
4. "Last updated: {relative time}" — replaces current freshness banner

**Logo:**
- Source: `logo` field from SpaceAPI JSON, stored as `schema:logo`, surfaced in GeoJSON as `s.logo`
- Rendered as `<img>` with `max-height: 32px; max-width: 80px; object-fit: contain; border-radius: 4px;` inline before the name text
- `onerror` handler removes the element — no broken image, no placeholder

**Share CTA:**
- Picto button in the drawer header bar, left of the existing close button
- On click: copies `window.location.origin + '/?space=' + s.id` to clipboard
- Visual feedback: picto switches to checkmark for 1.5s then reverts
- Hidden on mobile (`< 768px`)

**"Last updated" timestamp:**
- Source: `s.last_updated` from GeoJSON (new field, see AC6)
- Rendered: `"Last updated: " + timeAgo(s.last_updated)` using existing `timeAgo()`
- Replaces the current freshness banner — `freshnessText()` and the freshness dot are removed from Zone 1
- If `s.last_updated` is absent: show `"Last updated: unknown"`

---

### AC4 — Zone 2: contact pictos, embed CTA, subset nudge always present

**Contact row:**
- A row of icon buttons, one per contact channel found in `s.contact`
- Supported channels:

| Key | Picto | Action |
|-----|-------|--------|
| `email` | ✉ | copy to clipboard |
| `phone` | ☎ | copy to clipboard |
| `twitter` / `mastodon` | 🐦 / 🐘 | open URL in new tab |
| `irc` | # | copy to clipboard |
| `website` / `ml` | ↗ | open URL in new tab |
| any other key | ⬡ | copy to clipboard |

- Each button: `title="{key}: {value}"` for accessibility; click-to-copy shows checkmark for 1.5s
- If `s.contact` is absent or empty: row not rendered

**Subset nudge — permanent in Zone 2:**
- Section label: `"What your data unlocks"` (`.wf-label`)
- Always rendered for confirmed/broken spaces (not seeded)
- Shows current subset badge + one single next-field suggestion:
  - `"Add {field_name} to unlock {feature}"` — one field at a time, lowest-effort first
  - If `spaceapi:compatible` already reached: `"Full SpaceAPI compatibility — interoperable with mapall.space"`, no further nudge
- **Field-by-field classification** — `classify_subset()` updated to identify the single missing field for the next tier, not a list
- This is the permanent home for the nudge; the post-registration confirmation screen continues to show it too

**Embed CTA:**
- Moved from below Zone 3 to the bottom of Zone 2
- Suppressed on mobile (`< 768px`)
- Wording unchanged

---

### AC5 — Zone 3: raw JSON refinement + manual fetch button

**Layout changes:**
- Remove left and right padding from `<pre class="json">` — content flush to section edges
- Section header unchanged: `"Source data"` left, `"↗ Open source"` right
- Below header, before JSON block: `"Last fetched: {precise local datetime}"` in `var(--muted)` at `11px`
  - Format: `new Date(result.snapshot_date).toLocaleString()` (local time, precision to seconds)
  - Replaces current `snapshot · {date}` tag

**Manual fetch button:**
- Rendered below the JSON block (or below error message if fetch failed)
- Label: `"↺ Refresh from endpoint"`
- Rendered **disabled** in this story — the backing endpoint ships in Story 3.1
- `title="Manual refresh available soon"` on the disabled button so intent is clear
- Full click behaviour (fetch, re-render, cooldown) implemented in Story 3.1

**Removed:**
- Fetch history section — deleted entirely
- Embed button from below Zone 3 — moved to Zone 2 (AC4)

---

### AC6 — GeoJSON: surface `logo`, `contact`, `last_updated`

**Given** `scripts/materialize_geojson.py` runs

**When** building the SPARQL query (both UNION branches)

**Then** these optionals are added:

```sparql
OPTIONAL { ?spaceUri schema:logo ?logo }
OPTIONAL { ?spaceUri schema:contactJson ?contactJson }
OPTIONAL { ?spaceUri mom:lastUpdated ?lastUpdated }
```

**And** `binding_to_space()` maps:
- `logo` → `s.logo` (default `""`)
- `contactJson` → `s.contact` (JSON-parsed from string, default `null`)
- `lastUpdated` → `s.last_updated` (ISO string, default `""`)

**And** `_build_sparql_update()` in `link_handler/main.py` is updated to:
- Serialise the `contact` dict as compact JSON string and write `schema:contactJson "{escaped}"^^xsd:string`
- Write `mom:lastUpdated "{iso_datetime}"^^xsd:dateTime` on the space URI in the main graph at registration time

---

### AC7 — No regression

**Given** Stories 2.1, 2.2, 2.6, 2.7 behaviour

**When** 3.0-A changes are applied

**Then** registration flow is unchanged

**And** seeded space display (Zone 2 placeholder, no Zone 3) is unchanged

**And** broken space display is unchanged

**And** mobile suppresses: Zone 3, embed CTA, share CTA (all `< 768px`)

---

## Deferred

- `POST /api/heartbeat-space/{space_id}` endpoint + rate limiting → Story 3.1 (heartbeat refactor is a prerequisite; the manual fetch button in Zone 3 is a stub until then)
- True change-detection for `last_updated` (diff between snapshots) → Epic 7
- `state` open/closed dynamic signal → green marker, freshness sensing → Epic 7
- Space name collision / duplicate space resolution → pilot phase
- Endpoint URL swap / trust attack → pilot phase

---

## Files to touch

```
infra/
  link_handler/
    main.py              ← contactJson + mom:lastUpdated writes
                           (POST /api/heartbeat-space/{id} → Story 3.1)

scripts/
  materialize_geojson.py ← add logo, contactJson, lastUpdated to SPARQL + binding_to_space()

web/
  app.js                 ← Zone 1: logo + share CTA + last_updated, remove freshness banner;
                            Zone 2: contact pictos + subset nudge (permanent) + embed CTA moved;
                            Zone 3: padding + timestamp + manual fetch button;
                            remove fetch history;
                            post-registration timing conditional (8s / 2s)
  maps-of-making.html    ← drawer title → "Space Profile"
```
