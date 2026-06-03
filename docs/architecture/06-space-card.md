# Space card — where every field surfaces

> **The last hop.** [02 · Field traceability](02-field-traceability.md) traces a JSON field *into
> storage*; it stops at the store. This doc closes the loop: **which field surfaces as which element
> on the space-profile card** — the panel that fills the `detail` drawer ([05](05-view-shell.md)) when
> you click a pin. One function builds it: `renderDetail` (`web/app.js:527`). All anchors are exact.

## Three zones, eight sections

The card was designed around **three conceptual zones** (the trust frame), but renders as eight
sections today. The zones still hold:

- **Zone 1 — identity & notifications:** Hero · Status bar · State banner
- **Zone 2 — visitor-actionable:** Quick Facts · Specialties · Embed CTA
- **Zone 3 — the trust receipt:** Source Data (raw JSON)

## Field → section map

| Section | Fields surfaced | Gated by | Anchor |
|---|---|---|---|
| **Hero** | `name`, `logo` (→ placeholder on error), `address` (→ *"address not provided"*), status badge (`computeMarker`), `network_memberships`, `open_for_hosting` | always | `app.js:570` |
| **Canary label** | `observed_at` | `id === 'mother-sands'` only | `app.js:587` |
| **Status bar** | status phrase (from kind), `updated_at` | non-seeded | `app.js:600` |
| **Quick Facts** | `description`, `website`, `opening_hours`, `next_event`, `contact` (→ channel buttons) | non-seeded | `app.js:611` |
| **Specialties** | `specialties` (pills) | has any | `app.js:664` |
| **Embed CTA** | — (opens preset for this space) | non-seeded, desktop | `app.js:671` |
| **State banner / unlocks** | seeded → register prompt · `last_fetch_error`+`observed_at` (broken) · aging/zombie/dead notices · `subset`+`next_unlock` (confirmed unlock steps) | by kind | `app.js:677` |
| **Source Data (Zone 3)** | `endpoint_url`, raw JSON via `/api/space/{id}/raw`, `observed_at` (timestamp) | non-seeded, **desktop only** (`innerWidth ≥ 768`) | `app.js:747` |

## Design rules the card enforces

### Empty states are honest, not hidden
Quick-Facts rows render **even when the field is missing**, showing an em-dash placeholder
(`sp-fact-empty`, e.g. `app.js:615,625`). Address falls back to *"address not provided"*
(`app.js:575`). The gap is shown, never silently dropped — a visitor sees what the source *didn't*
publish. (Mirrors the pipeline's no-silent-drops stance at the UI layer.)

### The card is gated by lifecycle kind
`computeMarker(s)` (the [03](03-freshness-axes.md) computation) decides *which* sections render, not
just the badge colour:
- **seeded** — minimal card: hero + a *"Is this your space? Register…"* banner that opens `addurl`
  (`app.js:681`). No Quick Facts, no Zone 3 — there's no fetched data yet.
- **confirmed** — full card + *"What your data unlocks"* stepped progression (`subset`,
  `next_unlock`, `app.js:713`).
- **broken / aging / zombie / dead** — full card + a kind-specific heads-up banner sourced from
  `last_fetch_error` / `observed_at` (`app.js:690`).

So the same function produces a register-me stub or a rich profile depending on one token-derived
kind — no separate templates.

### Zone 3 is a trust receipt, not a debug panel
The Source Data section (`app.js:747`) is the transparency half of the dual guarantee:
- Renders the raw endpoint JSON verbatim in a terminal frame (`jsonHighlight`, `app.js:781`), with
  the fetch timestamp (`observed_at`) in the header and a linkable `↗ Open source` to `endpoint_url`.
- Carries an explicit trust line: *"The map only reads & enhances your data — it never edits the
  source."* (`app.js:784`).
- Degrades loudly: `Source unavailable.` / `Source data exceeds display limit.` on error/truncation
  (`app.js:766`) — never a blank panel.
- **Desktop-only** by deliberate design (no room on mobile; the trust-evaluator audience is at a
  desk anyway).

### The card can re-fetch on demand
Zone 3 includes a **Refresh from endpoint** button (`_makeRefreshBtn`, `app.js:802`) that POSTs
`/api/heartbeat-space/{id}` — a single-space heartbeat run. This is the only place the *view layer*
triggers the *pipeline*: on success it re-pulls `spaces.geojson` and re-renders (`app.js:830`);
on `429` it surfaces a rate-limit message with `retry_after_seconds` (`app.js:818`). It respects
the same fetch cadence the cron uses — the user can't hammer the source.

## Backlog surfaced by this trace (verified against current code)

- ✅ **`open_for_hosting` is live** — renders as a hero badge (`app.js:579`). _(Earlier notes filed
  it as a dormant placeholder; correct that — it surfaces now.)_
- ⬜ **`mom:sdgs` is NOT surfaced** — extracted into storage but absent from `renderDetail`. Still
  the open "intended for the space-profile card" item.
- ⬜ **`founded` / `capacity`** — no card section yet (grant-matchmaking use case, deferred).

---

This completes the schematic set: [01](01-walking-skeleton.md) pipeline · [02](02-field-traceability.md)
net-list · [03](03-freshness-axes.md) marker mechanics · [04](04-design-rules.md) map visual grammar ·
[05](05-view-shell.md) drawer shell · **06 card field-surface** (this doc). A field's full life is now
traceable end to end: *endpoint JSON → store → materialize → marker → card element.*
