# Maps of Making — Design Tokens (SKELETON)

**Created:** 2026-06-06 · **Author:** Winston (architect session) · **Status:** Skeleton — to be filled by extraction from each surface's CSS.
**Purpose:** One source of truth for the **shared visual layer** — typography + base surfaces — that every surface *consumes*. Seeds the future `web/.../tokens.css` extraction flagged in [per-surface palette strategy].

## How to read this doc — consume vs. define

There are two layers of styling, and keeping them separate is the whole point:

- **Shared chrome (this doc DEFINES it):** fonts, base surface colors, spacing/radius primitives. Every surface inherits these so the product feels like one system. Changing a token here changes it everywhere.
- **Semantic palettes (each surface OWNS, this doc only INDEXES):** the map's freshness-state colours (green = alive…), Bernard's voice accent, genjson/admin chrome. These must **not** be hoisted into the shared layer — green means "alive" on the map and must never get reused as a generic accent elsewhere, or the meaning leaks. This doc points at where each lives; it does not absorb them.

> ⚠️ **Known divergence to resolve:** `state-colour-ladder.html` is currently authored in **DM Sans / DM Mono**, but the live map (`maps-of-making.html`) uses **Inter Tight / JetBrains Mono / Caveat**. The ladder must be re-fonted to the system fonts below — it should *consume* shared type, not introduce its own.

---

## 1. Typography (SHARED — authoritative)

| Token | Family | Role |
|---|---|---|
| `--font-display` | `Inter Tight, system-ui, sans-serif` | UI / headings / body across surfaces |
| `--font-mono` | `JetBrains Mono, monospace` | endpoint URLs, codes, technical/"receipt" text, Bernard terminal |
| `--font-hand` | `Caveat, cursive` | the deliberate hand-drawn accent (map "hand" notes) — use sparingly |

*(Note: `maps-of-making.html` also declares a `--font-mono: 'Courier New'…` var that is unused/overridden by JetBrains Mono in practice — reconcile during extraction.)*
*(admin/index.html currently falls back to the system font stack `-apple-system, …` — align to `--font-display` during extraction. genjson/mothersands typography: TODO extract.)*

## 2. Base surfaces & neutrals (SHARED — authoritative)

From the map surface (the most-developed palette; treat as the seed):

| Token | Value | Role |
|---|---|---|
| `--paper` | `#f7f2e7` | primary daylight background |
| `--paper-2` | `#efe9d9` | raised daylight surface |
| `--drawer-bg` | `#faf6ea` | drawer/panel background |
| `--status-bg` | `#f1ebd9` | status strip background |
| `--ink` | `#1a1a1a` | primary text / strong rule |
| `--ink-soft` | `#2a2a2a` | secondary ink |
| `--muted` | `#6a6357` | muted text |
| `--faint` | `#bfb7a4` | faint text / seeded outline |
| `--rule` | `#2a2a2a` | borders/rules |
| `--radius` | `2px` | corner radius primitive |
| `--shadow` | `3px 3px 0 var(--ink)` | the hard offset shadow (brand signature) |

**Dark / "Depth" surface (continental view + Bernard terminal)** — sourced from the colour ladder's Depth palette; promote to shared once the GL Depth surface lands:
`--depth-black #0D0D0F` · `--depth-surface #131319` · `--depth-raised #1C1C24` · `--depth-border #2A2A34` · salt text `--salt #F0EDE0 / --salt-mid #C8C4B4 / --salt-dim #8A8678`.

## 3. Semantic palettes (OWNED per surface — INDEX ONLY, do not hoist)

### 3a. Map — freshness state language ← THE protected semantic set
Owner: `state-colour-ladder.html` (authoritative) + `maps-of-making.html`. Meaning is load-bearing; never reuse these hues for non-state decoration.

| State | Token / value | Meaning |
|---|---|---|
| open / alive | `--green` `oklch(60% 0.14 150)` / ladder `--algae #5DCAA5` | live, healthy, pulsing |
| shut (alive, closed now) | **TBD — remap target**: dimmed/desaturated green outline, **NOT** `--ink` black | open's quieter twin |
| aging | `--yellow` `oklch(82% 0.15 90)` | warming toward neglect |
| zombie | `--muted` (dimmed) | dormant |
| dead | grey tombstone (ladder `#9A9690`), **off the ladder — never just "darker"** | gone quiet |
| broken | `--accent` `oklch(62% 0.18 25)` (red `--red #E24B4A`) | endpoint unreachable |
| seeded / unconfirmed | `--faint` dashed outline | on map, not yet self-attested |
| confirmed (static) | `--accent-2` `oklch(55% 0.17 250)` | attested, no live endpoint |

Accent/glow extras: `--uv #7DF9FF` (depth highlight), `--blue-day #1456A0 / --blue-dep #378ADD`.

### 3b. Bernard — voice / character palette
Owner: TODO (genjson + wizard + map bot surfaces). Bernard's register has its own accent treatment; index here once extracted. Do **not** map Bernard's accent onto `--green`/state colours. See [Bernard character & voice].

### 3c. genjson — wizard/generator chrome
Owner: `web/genjson/index.html`. TODO extract palette.

### 3d. admin — operator tool chrome
Owner: `web/admin/index.html` (Epic 4). Currently system-font + minimal palette. TODO extract; Epic-4 build is the natural trigger to formalize.

### 3e. mothersands — diagnostic canary surface
Owner: `web/mothersands/index.html`. TODO extract palette.

---

## 4. Open actions
- [ ] Re-font `state-colour-ladder.html` from DM Sans/DM Mono → Inter Tight/JetBrains Mono.
- [ ] Extract genjson / mothersands / admin token blocks into §1–§3 (they have no `:root` vars yet — inline styles need promoting).
- [ ] Reconcile the dead `--font-mono: 'Courier New'` declaration in the map surface.
- [ ] When a 2nd surface needs the shared layer for real → promote this doc into `tokens.css` (the actual extraction; this doc is its spec) [per-surface palette strategy].
