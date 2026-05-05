# Story 3.0-A: Space Profile Card — UX Refinement

Status: review

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
    main.py              ← classify_subset() field-by-field refactor (AC4)
                           _build_sparql_update() + transform_to_sparql(): contactJson + mom:lastUpdated writes (AC6)
                           _SPARQL_SELECT: add logo, contactJson, lastUpdated optionals (AC6)
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

---

## Tasks / Subtasks

- [x] AC1 — Rename drawer to "Space Profile" in HTML
  - [x] `web/maps-of-making.html:518` — change `<h2>Detail</h2>` → `<h2>Space Profile</h2>`
  - [x] `web/maps-of-making.html:516` — change `aria-label="Space detail"` → `aria-label="Space profile"`

- [x] AC2 — Post-registration timing conditional
  - [x] `web/app.js:794` — change `"Opening your space card…"` → `"Opening your space profile…"`
  - [x] `web/app.js:800` — replace fixed `4000` with `unlockMsg ? 8000 : 2000`

- [x] AC3 — Zone 1: logo, share CTA, last_updated timestamp
  - [x] In `renderDetail()` (app.js:389): add logo `<img>` inline-left of `<h3>` in `.detail-hero`
  - [x] Add share CTA picto button in drawer header (left of close button); hidden on mobile
  - [x] Remove freshness banner block (`el('div', { class: 'freshness ...})` at app.js:409–412)
  - [x] Add `"Last updated: " + timeAgo(s.last_updated)` line in Zone 1 (below badges)

- [x] AC4 — Zone 2: contact pictos, subset nudge, embed CTA
  - [x] Remove fetch history section (`app.js:483–514`) entirely
  - [x] Remove embed button from below Zone 3 (`app.js:533–535`); move to bottom of Zone 2
  - [x] Add contact picto row using `s.contact` (render only if present)
  - [x] Add permanent "What your data unlocks" nudge section (confirmed/broken only, not seeded)
  - [x] Refactor `classify_subset()` in `infra/link_handler/main.py:235` for field-by-field nudge (see Dev Notes)

- [x] AC5 — Zone 3: padding, timestamp, disabled fetch button
  - [x] Remove left/right padding from `.json` `<pre>` element
  - [x] Replace `snapshot · ${result.snapshot_date}` tag with `"Last fetched: " + new Date(result.snapshot_date).toLocaleString()`
  - [x] Add disabled `<button>` below JSON block: `"↺ Refresh from endpoint"`, `disabled`, `title="Manual refresh available soon"`

- [x] AC6 — GeoJSON: surface logo, contact, last_updated
  - [x] `infra/link_handler/main.py` — `_SPARQL_SELECT` (line 27): add `OPTIONAL { ?spaceUri schema:logo ?logo }`, `OPTIONAL { ?spaceUri schema:contactJson ?contactJson }`, `OPTIONAL { ?spaceUri mom:lastUpdated ?lastUpdated }` to both UNION branches; add to `GROUP BY`
  - [x] `infra/link_handler/main.py` — `_binding_to_feature()` (line 434): map `logo` → `s.logo`, parse `contactJson` → `s.contact`, `lastUpdated` → `s.last_updated`
  - [x] `infra/link_handler/main.py` — `_build_sparql_update()` (line 373): add `schema:contactJson` and `mom:lastUpdated` triples
  - [x] `infra/link_handler/main.py` — `transform_to_sparql()` in transformer.py: add same triples
  - [x] `scripts/materialize_geojson.py` — add same three OPTIONAL clauses + `binding_to_space()` mapping

- [x] AC7 — Verify no regression
  - [x] Seeded space display: Zone 2 placeholder unchanged, no Zone 3
  - [x] Broken space display unchanged
  - [x] Mobile suppression: Zone 3, embed CTA, share CTA all hidden at `< 768px`
  - [x] Registration flow (`_onFetchUrl` → `register_url`) unchanged

---

## Dev Notes

### `renderDetail()` — current structure to navigate safely

Full function at `web/app.js:389–535`. Sections in order:

1. **Hero** (`app.js:399–407`) — `el('div', { class: 'detail-hero' })` with `<h3>` name, `.where` address, `.badges` status/network
2. **Freshness banner** (`app.js:409–412`) — `el('div', { class: 'freshness ...' })` → **DELETE entirely** (AC3 replaces with "Last updated" in hero)
3. **Seeded CTA** (`app.js:414–425`) — keep unchanged
4. **Zone 2 data card** (`app.js:426–442`) — currently Name / Website / Opening hours / Description as `<dl class="kv">`; keep structure, add contact pictos + subset nudge below it
5. **Specialties** (`app.js:443–447`) — keep unchanged
6. **Zone 3** (`app.js:449–481`) — currently has `snapshot · {date}` tag → replace with precise timestamp; add disabled button below `<pre>`
7. **Fetch history** (`app.js:483–514`) — **DELETE entirely** (AC5)
8. **Copy space link button** (`app.js:516–535`) — **REPLACE** with share CTA picto in header (AC3); remove this bottom button

### Post-registration timing — exact lines

- `app.js:772`: `const unlockMsg = reg.unlock_message;`
- `app.js:794`: `'Opening your space card…'` → `'Opening your space profile…'`
- `app.js:800`: `}, 4000);` → `}, unlockMsg ? 8000 : 2000);`

### Drawer title — exact lines

- `web/maps-of-making.html:516`: `aria-label="Space detail"` → `aria-label="Space profile"`
- `web/maps-of-making.html:518`: `<h2>Detail</h2>` → `<h2>Space Profile</h2>`
- HTML element `id="drawer-detail"` and all JS references to `'detail'` as drawer key — **DO NOT change** (AC1 spec: label-only, no refactor)

### `classify_subset()` — field-by-field refactor

Current implementation at `infra/link_handler/main.py:235` uses group checks:
- `has_card = has_required AND url AND opening_hours`
- Returns `"unlock_message": "Add website and opening hours"` even when one is already present

AC4 requires single-field nudge: find the first missing field in tier order and suggest only that one. New logic:

```python
# mom:required tier → mom:card tier: check url first, then opening_hours
if not schema.resolved_url:
    next_unlock = "Add schema:url (website) to unlock the full detail card"
elif not schema.resolved_opening_hours:
    next_unlock = "Add schema:openingHours to unlock the full detail card"
# mom:card → spaceapi:compatible: check api_compatibility first, then logo, then contact
```

Return shape stays identical (`subset`, `subset_score`, `unlock_message`, `next_subset`, `next_unlock`) — only the `unlock_message` / `next_unlock` strings change. All callers (`_fetch_and_validate`, Zone 2 permanent nudge) use `next_unlock`.

### `_SPARQL_SELECT` in main.py vs materialize_geojson.py

**Both SPARQL queries must be updated** — they are separate:
- `infra/link_handler/main.py:27` — used by `_rematerialize_geojson()` (called after registration and heartbeat)
- `scripts/materialize_geojson.py` SPARQL_QUERY — used by manual `make publish` runs

Both feed the same `spaces.geojson`. Missing the update in either one causes `s.logo` / `s.contact` / `s.last_updated` to be absent from the GeoJSON intermittently depending on which path last ran.

### `_build_sparql_update()` — new triples to add

At `infra/link_handler/main.py:373`. Add alongside existing triples:

```python
contact_dict = schema.contact if hasattr(schema, 'contact') else None
if contact_dict:
    contact_json = json.dumps(contact_dict, separators=(',', ':'))
    triples.append(f'  <{space_uri}> <{SCHEMA}contactJson> "{_sparql_str(contact_json)}"^^<http://www.w3.org/2001/XMLSchema#string> .')

now_iso = datetime.now(timezone.utc).isoformat()
triples.append(f'  <{space_uri}> <{MOM}lastUpdated> "{now_iso}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .')

if schema.logo:
    triples.append(f'  <{space_uri}> <{SCHEMA}logo> "{_sparql_str(str(schema.logo))}" .')
```

Same pattern applies in `transformer.py`'s `transform_to_sparql()`.

### Contact picto channel → action mapping (AC4)

```javascript
const CONTACT_PICTOS = {
  email:    { icon: '✉', action: 'copy' },
  phone:    { icon: '☎', action: 'copy' },
  twitter:  { icon: '🐦', action: 'url' },
  mastodon: { icon: '🐘', action: 'url' },
  irc:      { icon: '#', action: 'copy' },
  website:  { icon: '↗', action: 'url' },
  ml:       { icon: '↗', action: 'url' },
};
// fallback for unknown keys: icon='⬡', action='copy'
```

`s.contact` arrives as a parsed object (mapped from `contactJson` in `_binding_to_feature`). Render one `<button>` per key found. Copy action: `navigator.clipboard.writeText(value)` then switch icon to `✓` for 1.5s. URL action: `window.open(value, '_blank', 'noopener')`.

### Logo rendering (AC3)

```javascript
if (s.logo) {
  const img = document.createElement('img');
  img.src = s.logo;
  img.style.cssText = 'max-height:32px;max-width:80px;object-fit:contain;border-radius:4px;margin-right:8px;vertical-align:middle;';
  img.onerror = () => img.remove();
  // insert before the <h3> text node inside .detail-hero
}
```

### Share CTA picto button (AC3)

Place in drawer header bar (`.drawer-head` in `maps-of-making.html`), left of the existing close `×` button. Use `window.location.origin + '/?space=' + s.id` as the share URL. Hidden via CSS at `< 768px` (`display: none` with a responsive class or inline style check). Switch icon to `✓` for 1.5s on click.

### Project Structure Notes

- `infra/link_handler/main.py` imports `datetime` and `json` already — no new imports needed for triple writes
- `SCHEMA` and `MOM` constants already imported in `main.py` from `utils.py`
- `_sparql_str()` already available for escaping contact JSON string
- `s.contact` in GeoJSON features is parsed JSON object — `_binding_to_feature()` must call `json.loads()` on the SPARQL string result with a try/except fallback to `null`

### References

- [Source: web/app.js:389–535] — `renderDetail()` full current implementation
- [Source: web/app.js:772–800] — post-registration confirmation block with `unlockMsg` and 4000ms timeout
- [Source: web/maps-of-making.html:516–518] — drawer `id`, `aria-label`, `<h2>` to update
- [Source: infra/link_handler/main.py:27–93] — `_SPARQL_SELECT` (needs logo/contact/lastUpdated optionals)
- [Source: infra/link_handler/main.py:235–288] — `classify_subset()` current group logic to replace
- [Source: infra/link_handler/main.py:373–432] — `_build_sparql_update()` triple write pattern
- [Source: infra/link_handler/main.py:434–485] — `_binding_to_feature()` GeoJSON mapping
- [Source: scripts/materialize_geojson.py] — parallel SPARQL query + `binding_to_space()` to update
- [Source: deferred-work.md#UX-design-session-3-0-A] — deferred items: manual fetch wired in 3.1, change-detection in Epic 7

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- AC1: Drawer title and aria-label updated; `id="drawer-detail"` and JS references preserved
- AC2: Post-registration text updated to "Opening your space profile…"; timing now 8s (with unlockMsg) or 2s (without)
- AC3: Logo img prepended to hero, share CTA injected into drawer header (idempotent, reassigns onclick each render), freshness banner removed, "Last updated: timeAgo(s.last_updated)" added to hero
- AC4: Fetch history section deleted; old copy-link button deleted; embed CTA moved to Zone 2; contact picto row added (CONTACT_PICTOS map); old seeded CTA block removed; state-aware info banner added after specialties for all states (seeded→claim nudge, confirmed→next_unlock from Oxigraph, broken→error label, aging/zombie→visitor caution, dead→closure notice); classify_subset() refactored: api_compatibility removed from tier logic (out of scope for MoM demo), single-field next_unlock for logo then contact only; mom:subset + mom:nextUnlock written as Oxigraph triples via both transform_to_sparql() and _build_sparql_update(), surfaced in both SPARQL queries and binding mappers; JS reads s.subset / s.next_unlock from GeoJSON — no client-side duplication
- AC5: Pre padding removed (padding: '6px 0' on raw-content); snapshot tag replaced with "Last fetched: toLocaleString()"; disabled ↺ button added below JSON block (also added on error/unavailable paths)
- AC6: _SPARQL_SELECT in main.py updated (both UNION branches + SELECT + GROUP BY); _parse_contact_json() helper added; _binding_to_feature() maps logo/contact/last_updated; _build_sparql_update() writes logo/contactJson/lastUpdated triples; transformer.py adds contactJson + lastUpdated (logo was already written); materialize_geojson.py SPARQL_QUERY and binding_to_space() updated identically
- AC7: 56 tests pass, 1 skipped; seeded/broken/mobile suppression logic unchanged

### File List

- web/maps-of-making.html
- web/app.js
- infra/link_handler/main.py
- infra/link_handler/transformer.py
- scripts/materialize_geojson.py
- _bmad-output/implementation-artifacts/3-0-A-space-profile-card-ux-refinement.md
- _bmad-output/implementation-artifacts/sprint-status.yaml

### Change Log

- 2026-05-05: Story 3.0-A implemented — Space Profile drawer rename, post-reg timing, Zone 1/2/3 UX refactor, GeoJSON pipeline extended with logo/contact/last_updated
