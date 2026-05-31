# UX Spec — Bernard's Workshop Wizard

**Status:** Locked principles (v1) — interaction grammar for Epic 9 (Stories 9.6–9.12).
**Author:** Sally (UX) with Nicolas, 2026-05-31.
**Companion to:** `bernard-bible.md` (voice/character SSOT), `9-5-bernard-voice-copy-pass-*.md` (`bernard_copy.yaml`), `schema-roleplay-personas.md`.
**Governs:** `web/genjson/genjson.js` and the map drawer fork in `web/maps-of-making.html`.

> **How to use this file:** Any Epic 9 wizard story (9.6 Tier 2, 9.7 `state.open`, 9.8 go-live,
> 9.9 three-mode, 9.10 Tier 3, 9.11 error UX, 9.12 visual) must cross-check these principles
> first. New interaction decisions are recorded here. Copy lives in `bernard_copy.yaml`; voice
> rules live in `bernard-bible.md`; **interaction grammar lives here.**

---

## 0. Why this exists

The map is nothing more than a map. The little content we layer on top of it must therefore be
**awesomely crafted** — small surface, nowhere to hide, every word and beat load-bearing.

Two distinct jobs were being conflated in the backlog:

- **Interaction grammar** (the bones) — how Bernard takes a turn, how a step reveals, how the
  file accrues, how ownership is felt. ← *this document.*
- **Visual skin** (Story 9.12) — colour, layout, contrast, spacing, mobile.

You cannot skin bones that are still moving. The grammar is locked here **before** 9.6 stamps
the pattern five more times. Story 9.12 inherits a settled flow and becomes "lock the visual
frame the next stories inherit," not "pick colours on a moving target."

**The reframe in one line:** *the wizard is not a form — it is text-based storytelling narrated
by Bernard.* Same data the form collected; a conversation instead of a wall of boxes.

**Method:** principles-first, fog-of-war. We lock what we know and the wins already built
(Tier 0+1). We deliberately do **not** pre-design Tier 2/3 UX — those flows must emerge from a
natural progression that respects these principles, as development surfaces the real challenges.

---

## 1. The six principles

### P1 — Ownership is the drumbeat
*Your* bedrock, *your* endpoint, *your* URL, *your* data. You self-host, you're in charge, all
along. The possessive is relentless and deliberate (it pairs with the drawer's "your endpoint
URL" jargon-polarization). Concrete obligations:
- **Export your file is always available** — quiet, subordinate to the primary action, but
  present from the first keystroke. It is the proof you can walk at any moment with what's yours.
- Bernard says **"That's *your* bedrock,"** never "the bedrock."

### P1b — Content is sovereign; shape is normalized *(the truth-vs-shape split)*
**Bernard never judges the *truth* of what you give — only the *shape*.** Your name, description,
hours: your call, your truth, never questioned, never ranked. But the *format* triggers Bernard's
compulsive cleaning (the Jacques trait, bible §2): `https://` prepended, Matrix `#` sigil added,
country code uppercased — **reflexively, and always announced** (never silent). Six-word ethic:
**content is sovereign, shape is normalized.**

### P2 — One beat at a time; kill the wall
Reveal a single step at a time, not a form of stacked fields (*Hick's Law*, *Miller's Law*). Each
step is a line of Bernard's; the input is your reply. **The intro is transient** — it launches
like the map's loading phase, then gives way to the first real step. It does not permanently
occupy the top of the screen (see §3, current-state critique).

### P3 — Bedrock is the only gate; Bernard does the location math
Name + address is the only thing ever *required*. Everything above bedrock is invitation, never
demand (*Tesler's Law* — Bernard absorbs complexity: he derives, you don't supply). The
derivation is honest and scoped to **location facts only** (§2 table). When enough fills in,
geocode fires in the background and Bernard narrates the result.
- **Guardrail:** *"dropping the pin here…"* is **narration confirming a derived lat/long** —
  **not** a map preview, mini-map, or redirect to the big map. The wizard stays text. The pin is
  a *word*, not a widget.

### P4 — Acknowledgment, not congratulations
Every field is validated + normalized in the background, **narratively**. Bernard gives a terse
*"Fine." / "There you are."* — never *"Great job."* Filling it is its own reward. And Bernard is
**not needy**: skip what you like — they have other bedrock to dredge. No pestering, no flattery,
no shame, no ranking. (Forbidden patterns: bible §3.)

### P5 — Familiar bones under the story *(the guardrail)*
Narrated ≠ chatbot. Inputs stay inputs, buttons stay buttons (*Jakob's Law*). "Light and dynamic"
means Bernard *frames* conventional controls — it does **not** mean free-text parsing or a chat
UI. This discipline keeps storytelling from tipping into gimmick.

### P6 — The craft is the argument
Special Elite, the em-dash, muted-tombstone hierarchy, the micro-copy, the pin-drop timing,
sub-400ms feedback (*Doherty Threshold*). The voice is the thing that's *different* in a sea of
SaaS onboarding (*Von Restorff*), and pretty reads as usable (*Aesthetic-Usability*). The end is
engineered too (*Peak-End* — the 9.8 go-live "see your space on the map" is the payoff the whole
flow points at).

---

## 2. The honest derivation model

Bernard derives **location facts**, nothing else. The wizard should ask for the address and
*derive* the rest rather than asking for it:

| User gives | Bernard derives |
|---|---|
| Full address | lat/lon · **country code** · **timezone** |
| Street | postcode |
| City alone | centered lat/lon · country code |

Bernard's bedrock line must stay inside this truth (he does **not** derive description, logo,
network, etc.). Candidate copy:
> *— Name, and where you are. That's your bedrock. The coordinates, the country, the timezone —
> those I pull myself.*

**Fog-of-war / dev note:** the geocode proxy returns **lat/lon only today** (`/api/geocode`).
Country-code derivation (Nominatim address components) and timezone derivation (lat/lon → tz
lookup) are **new work** to be surfaced in the geocode story — flagged here, not designed here.
If unbuilt, the country-code field remains a (still-derivable-later) manual input; the principle
("ask address, derive the rest") is the target.

---

## 3. Tier 0, reframed (the worked example)

**Current state (`genjson.js` render, screenshot 2026-05-31):** intro + tier label + bedrock
line + five labelled boxes + two buttons all fire at once. That is a form shouting — too much,
violates P2.

**Target — Bernard discovers your space with you:**

```
   — Hi, I'm Bernard (they/them) from 'Mother Sands'.        ← loads like the loader,
     Let's get your space on the map.                           then recedes
   ─────────────────────────────────────────────────────

   — What does your community call this place?
     [ ______________________ ]

   — Noisebridge. Fine. And where do I find it?
     [ 272 Capp St, San Francisco ____ ]
       …dropping the pin here… 37.76, −122.42 · US · CET    ← narration, not a map

   — That's your bedrock. The rest is yours to give, or not.

                                          [ Continue → ]
  ───────────────────────────────────────────────────────
  noisebridge-san-francisco-2026-05-31.json   ▱▱▰ bedrock   export ⌄
```

Behavioural spec:
- Intro is **transient** (loader-phase → recede), not permanent chrome.
- Steps reveal **one beat at a time**; Bernard *reacts* to the prior answer before asking the next.
- Geocode fires in the **background** once enough address is present; result is **narrated**
  (pin-as-word), country/postcode/timezone **derived and shown**, never separately asked.
- Bedrock confirmation enforces ownership: **"That's *your* bedrock."**

---

## 3b. The visual world — Direction B, locked (2026-05-31)

The wizard is **Direction B: a dark "workshop interior" you cross into** — full-voice Bernard, but
a *threshold*, not the lair. Grounded in Bernard's hermit-crab vision (blue/yellow/green/UV, **no
red** — bernard-bible §1):

- **Base = liminal dusk** (deep blue-green dark), **not** pitch fort-black. The workshop is the
  **border crossing** between the bright MoM map and Mother Sands (the lair — reserved for Epic 8
  lore). It reads as an antechamber, not the inner sanctum.
- **Amber / brass** (yellow band — Lagavulin, lamplight): Bernard's voice, warmth, **primary CTA**.
- **Blue** (in-spectrum; rhymes with the drawer's cobalt + water): **links / navigation**.
- **Green** (in-spectrum): **valid / confirmed / derived-success** (the pin that drops, bedrock held).
- **Red: errors ONLY** — the one color *outside* Bernard's spectrum, so it reads as the alien
  "something's wrong" note. The semantic discipline is the *biology*, not an arbitrary convention.
- **UV** (the band only Bernard sees): a faint cool shimmer for curiosity hooks / hover-focus glow;
  **sparingly** — the secret layer.

It keeps the drawer's shared grammar: Special Elite, underline links, `2px` radius, shadow language
(*Jakob's Law* — P5). Exact hues are an operator-visual call at implementation (one change at a
time); the **direction** is locked, not re-litigated. Implemented by Story 9.12.

## 4. The ownership strip (persistent bottom line)

One shy, ever-present line — the literal home of P1's "always able to walk with your file":

```
  noisebridge-san-francisco-2026-05-31.json   ▱▱▰ bedrock   export ⌄
  └──── live preliminary filename ──────────┘ └ shy bar ┘ └ always ┘
```

1. **Live preliminary filename** — your space's name is on *your* file from the first keystroke;
   updates as you type. Ownership made literal.
   - **Convention:** `<space>-<city>-<YYYY-MM-DD>.json` (e.g. `noisebridge-san-francisco-2026-05-31.json`).
   - **Rationale:** mirrors the seed-ID *basis* (`seed_import.py:34` hashes `name|city`) but stays
     **human-readable** — a hash is wrong for a filename a person must recognize on disk. The date
     stamp is pure Bernard (a dated maintenance-log entry) and reinforces "this snapshot is yours."
   - Supersedes current `slugify(name)`-only export name in `genjson.js`.
2. **Shy progress bar** — hints progression **without ever demanding completion** (P4, non-needy):
   - **bedrock** is the one marked threshold (*goal-gradient* pulls you there);
   - past bedrock the bar keeps growing toward a **faint full-state horizon** — *there is an end,
     softly implied* — but it never flashes "incomplete," never turns red, never nags. Richness
     accruing, not a quota.
3. **Export ⌄** — always present, quiet, never gating anything; available before bedrock too
   (the file is yours even half-built).

---

## 5. Deliberately NOT designed here (fog of war)

Per the principles-first method, the following are left to **emerge** from P1–P6 as dev surfaces
the real challenges — do not pre-spec them:

- Tier 2 flow (9.6 — `memberOf`, `opening_hours`, `mom:sdgs`). The fork's "Go deeper" door.
- `state.open` FSM labels & interaction (9.7).
- The go-live / self-host success moment (9.8) — though P6 marks it as the engineered *end*.
- Three-mode reconciliation (9.9) — wizard / URL-prefill / validator as one model.
- Tier 3 `ext_fab` (9.10).
- Inline per-field error UX (9.11).

Each must arrive as a beat in Bernard's narration, respect bedrock-is-the-only-gate, and feed the
ownership strip — but their specific shapes are intentionally open.

---

## 6. Relationship to the backlog

- **Re-scopes 9.12**: from "visual design pass (colour/layout/contrast)" to **"lock the visual +
  interaction frame the next stories inherit,"** implementing §3 (transient intro, beat-by-beat
  reveal) and §4 (ownership strip). Visual styling still lives here; it now has a grammar to dress.
- **Feeds 9.6+**: every subsequent story references §1 principles and plugs into §4's strip.
- **No new copy invented here** — calibrated lines belong in `bernard_copy.yaml` (Story 9.5 SSOT);
  candidate lines above are illustrative until curated there.

## 7. Open threads

- Geocode proxy: add country-code + timezone derivation (§2 dev note) — needs a story.
- Progress-bar "full-state horizon": what counts as the soft end — all tiers? a richness score?
  Resolve when Tier 2/3 shapes are known (fog of war).
- Whether the transient intro recede is animation or instant (P5 — keep it cheap, no gimmick).
