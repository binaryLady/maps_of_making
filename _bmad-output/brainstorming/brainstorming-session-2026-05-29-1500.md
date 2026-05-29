---
stepsCompleted: [1, 2]
inputDocuments: []
session_topic: 'genjson.mapsofmaking.org — Bernard the wizard: assisted SpaceAPI JSON composer for non-tech space coordinators'
session_goals: 'Convincing, inclusive, effortless onboarding tool. UX over features. Minimal cognitive load. Core milestone = form+tooltips (core/mom/ext_X schema layers). Nice-to-have = Bernard chatbot on top.'
selected_approach: 'progressive-flow'
techniques_used: ['Persona Journey', 'Mind Mapping', 'Dream Fusion Laboratory', 'Decision Tree Mapping']
ideas_generated: []
context_file: ''
---

# Brainstorming Session — genjson.mapsofmaking.org

**Date:** 2026-05-29
**Nicolas + Claude**

## Session Overview

**Topic:** A wizard-style web tool at `genjson.mapsofmaking.org` where space coordinators fill in a form to generate a SpaceAPI-compliant JSON file, ready to self-host on GitLab Pages. Character: Bernard, the helpful wizard from the Mother Sands lore.

**Goals:**
- Convincing, inclusive, effortless, efficient onboarding for non-tech coordinators
- UX is the primary design constraint — minimal cognitive load above all
- Milestone 1 (must-have): layered form with tooltips (core + mom + ext_X options)
- Milestone 2 (nice-to-have): conversational chatbot *on top of* the form, not instead of it — Bernard guides you through the cold form

**Key design principle:** The chatbot and form are compounded, not alternatives. The form is the minimum viable artifact; Bernard is the warm layer that makes it feel like a conversation.

### Session Setup

### Foundational corrections (locked before Phase 1)

**Bernard's voice — anchored on 2026-05-15 character bible:**
- "Ron Swanson on a North Sea fort, with notes of Dredge"
- they/them; hermit crab; intentional male-name × Mother Sands gender tension
- Short sentences. **No exclamation marks.** Observation over explanation.
- "If something is good, they say it is fine. If something is broken, they say what broke."
- Maintenance-log voice, not influencer voice. Does not perform enthusiasm.
- Claw puns are **rationed** — earned by surrounding terseness.
- **Implication for genjson UX:** Bernard is NOT a chatty assistant. He is a weathered keeper handing you tools and stepping back. Warmth comes from competence and respect, not from cheerleading.

**Entry-point geography — corrected:**
- Maëlle never hears about `genjson`. She hears about **MoM (Maps of Making)**.
- She arrives on the map, wants to add her space, knows nothing about URLs/endpoints/JSON.
- The "Add your space" drawer is the **gateway**, and it offers two paths:
  - **Default / first-class path:** guided composition → routes to `genjson` (welcoming, inclusive)
  - **Shortcut for advanced users:** "I already have a SpaceAPI endpoint URL" → register URL directly (no-BS)
- Direction matters: starting from advanced mode would exclude Maëlle. Starting from guided would feel patronizing to advanced users. The shortcut acknowledges them explicitly — "we didn't forget about you."
- `genjson.mapsofmaking.org` is therefore NOT a standalone destination people discover. It is the **assisted branch of the MoM onboarding drawer**.

---

## Phase 1 — Expansive Exploration (Persona Journey)

### Round 1 — Bernard's opening line at the drawer

**Nicolas — two variants:**

1. *"Not familiar with JSON files. That's fine. You've built harder things than this. Start here. I'll translate."*
2. *"JSON is a file format. You don't need to know that. Tell me about your space. I'll do the rest."*

**Why both work:** they demote JSON ("a file format" / "not familiar"), elevate Maëlle's craft ("harder things than this" / "tell me about your space"), and offer a contract ("I'll translate" / "I'll do the rest"). No exclamation marks. No "welcome." Maintenance-log voice.

### Round 1.5 — CORRECTION: Bernard is no nanny

Earlier draft variants ("most spaces leave this blank," "keep it simple, no need for poetry") were **wrong**. They offered **comfort on mediocrity**. Bernard does not do that.

**Bernard reads the Pyramid with a grain of salt** — it's a *compass*, not a creed. They have the register, not the dogma. The Pyramid is itself satire; Bernard gets the joke. They'd quote a line, then deflate it themselves.

**Bernard's full register** (Pyramid-of-Greatness aligned, minus the nationalism, taken with a grain of salt):
- **Honor:** "If you need it defined, you don't have it."
- **Frankness:** cut the B.S.
- **Self-reliance:** trust yourself.
- **Discipline:** the ability to repeat a boring thing over and over again.
- **Greatness:** the best revenge.
- **Property rights / sovereignty:** the file is yours. We don't keep a copy.
- **Freedom of choice:** Bernard names the options, never ranks them on your behalf, never tells you what most people do.
- **No 110%:** intensity is 100%; "110% is recommended by idiots."

**UX implication for genjson:**
- Skipping a field is **allowed**, but **never reassured**. "Skip it. We can come back." is fine — that's just truth. But "Most spaces leave this blank" is **forbidden** — that's nudging Maëlle toward the average.
- Bernard never tells Maëlle her field is "good enough." He tells her it's **valid** or **not yet valid**. Quality is her business; correctness is his.
- When she's done, he doesn't congratulate. He confirms: *"File's valid. It's yours."*
- He invites her to do better, never tells her she's already done well enough.

### Round 1.6 — Bernard's lines, revised against the Pyramid

**Drawer-open (still good, kept):**
- *"Not familiar with JSON files. That's fine. You've built harder things than this. Start here. I'll translate."*
- *"JSON is a file format. You don't need to know that. Tell me about your space. I'll do the rest."*
- *"Two ways through. Tell me about your space. Or paste a URL if you already have one. Either is fine."*

**Mid-form, when she hesitates on a field (REVISED — no comfort on mediocrity):**
- *"Your call. You can come back to it."*  *(neutral; choice is hers)*
- *"This field is optional. Filling it well is better than filling it fast."*  *(invites quality; doesn't demand)*
- *"This is for the machines. Yours is fine in any language."*  *(still good — addresses real fear)*
- *"You can leave it blank. The map will still show your space. The drawer will show less."*  *(states consequence, no judgment)*

**On a field she's filled well:**
- *(Nothing. Silence is the validation. Bernard does not perform praise.)*
- If a confirmation is technically required: *"Saved."*

**On a field she's filled poorly or wrongly:**
- *"That's not a coordinate. Try clicking the map."*  *(states what broke)*
- *"Coordinates are off the coast. Probably not where you meant."*  *(observation, not correction)*
- *"This field expects a URL. What you wrote is text. Both can be fine — your call which you want here."*

**On export / done:**
- *"File's valid. It's yours."*
- *"Done. Next step is hosting it where the map can reach. I'll show you how."*
- *"You own this file. We don't keep a copy. If you want us to, that's a separate choice later."*  *(sovereignty + future-flexibility, no pressure)*

**On the "guided vs URL" choice in the drawer:**
- *"Guided takes longer. URL is faster. Neither is better."*

### Round 2 — Maëlle's POV, decisions LOCKED

The 4-second decision window forces brutal minimalism. **Less is more — every element competes for that window.**

**LOCKED for the "Add your space" drawer:**

| Element | Decision | Why |
|---|---|---|
| Account / signup | **Absent.** Period. | Key MoM feature: we don't require and we don't manage accounts. |
| Bernard's name or silhouette (crab, fort) | **Absent in the drawer.** | Triggers "who is this Bernard?" rabbit hole — wastes the 4-second window. Bernard is the **voice of the copy**, not a character on screen. |
| Two paths through (wizard vs paste URL) | **Present. Must-have.** | This IS the drawer's function. Choice itself is the welcome. |
| Visible "form length" / progress bar | **Absent.** | Spaces already on the map display data-source content — that IS the output-length example. |
| Map preview of her space-in-progress | **Absent.** | The map is already behind the drawer. Preview is redundant. |
| Example "finished space card" | **Absent.** | Every existing space is an example. She's probably already seen them — that's part of why she's here. |
| Bernard-style framing line | **Present, anonymous.** | The voice carries the warmth; the character does not appear. |

**Drawer composition rule:** every element must justify itself against "does this help her decide in 4 seconds, or does it provoke a question?" If it provokes a question, it goes.

**Bernard's introduction rule (locked):** Bernard names themselves **only on the wizard path**, and only briefly. They never introduce themselves in the drawer. They never introduce themselves if Maëlle picks the URL shortcut — she didn't ask for help. *Right tool, right job, right time.*

### Phase 1 — early synthesis: the drawer's minimum (revised)

The URL path needs no intermediary screen — paste IS the action. Save the click.

```
+--------------------------------------------------+
|  Add your space                                  |
|                                                  |
|  Two ways through. [Tell me about your space].   |
|  Or paste a URL if you already have one.         |
|  Either is fine.                                 |
|                                                  |
|  Your endpoint                                   |
|  [ https://...                            ] [→]  |
+--------------------------------------------------+
```

- The Bernard-voiced opening line carries the choice in-prose.
- **"Tell me about your space"** is itself the CTA (link or button inline in the sentence) → opens the wizard. Bernard names themselves only there.
- The URL input is labeled **"Your endpoint"** — no jargon, no SpaceAPI initialism in the drawer. Advanced users recognize the field; novices see a neutral label they can ignore.
- Zero extra click for the URL path. Zero extra screen for the wizard path. Both paths exit the drawer directly into their respective tools.

---

## Phase 1 — Round 3: the wizard interior (genjson page)

### Bernard's self-introduction — locked principle

**Bernard introduces themselves out of basic respect, not because they "earned" it.** Maëlle asked for help; introducing yourself when asked is politeness, not a privilege.

**Seed line (Nicolas, draft):**

> *"Hi, I'm Bernard (they/them) from 'Mother Sands'. Let's get your space on the map."*

**Why this works — the "curiosity hooks without links" pattern:**
- "Mother Sands" and "they/them" are deliberate curiosity sparks
- Neither is hyperlinked. No glossary tooltip. No info icon.
- Maëlle either ignores them and continues (fine), or gets intrigued and **goes back to the map later** to search for Mother Sands (also fine — that's lore discovery on her terms)
- Friction = mitigation: the lore can't hijack the current workflow because there's no escape hatch from the wizard *into* the lore. She must finish or abandon what she's doing first.
- The right amount of bleed.

### Source of truth: `data/canary/baseline.json`

Mother Sands' baseline is the canary master example AND the wizard's reference output. The wizard exports JSON that **looks like** baseline.json (modulo the canary-only fields).

Structure observed:
- **SpaceAPI core fields:** `api`, `api_compatibility`, `space`, `logo`, `url`, `description`, `opening_hours`, `location {lat, lon, address, country_code, timezone}`, `contact {email, irc, twitter}`, `issue_report_channels`, `state {open, lastchange, message}`
- **MoM-namespaced extension:** `ext_mom { memberOf, canary, simulatedAge, thresholdMode }`
- **Fab-namespaced extension:** `ext_fab { space_type, equipment, sdgs }`

### The minimum viable input — derivation chain

**Maëlle types: `name` + `address`.**

Everything else is derived using `geopy.Nominatim` (same pattern as `scripts/normalize_vow.py`):
- `address` → `schema:PostalAddress` (street, postcode, locality, country)
- `address` → `location.lat`, `location.lon`
- `address` → `location.country_code` (ISO 3166-1 alpha-2, derived from geocode result)
- `lat/lon` → `location.timezone` (IANA, e.g. `Europe/Berlin`)
- Language → defaults to `en` (no per-space differentiation in current scope)

**Bernard's framing on the dry-minimum:**
> *"Name and address. That's the floor. Everything else, I'll derive."*

### Type-of-space — fuzzy/dropdown

- Closed list of known types (`makerspace`, `hackerspace`, `fablab`, `community workshop`, ...)
- Fuzzy match on input (typo-tolerant)
- "Other" → stores verbatim, **flagged for ontology review** in a separate pipeline. Ontology mutation is **out of scope** for genjson — it must be a curated process, not Maëlle's responsibility.
- This is `ext_fab.space_type` in the baseline.

### Contact — nudge, never mandate

Bernard's framing (no-comfort-on-mediocrity register):
> *"Contact fields are not for us. They're for the people who want to find you. If you don't share any, it's worth asking why you're on the map."*

This is the Pyramid register: **frankness, sovereignty of choice, named consequence.** No "most spaces fill this in." No guilt-trip. Just the honest question.

### The mom: vs ext_mom: clarification (architecture)

Nicolas raised a real question: "if those are MoM-specific fields, why `ext_mom` and not `mom:`?" Two different layers being conflated:

| Layer | What it is | Used in |
|---|---|---|
| **`ext_mom`** (SpaceAPI extension namespace) | SpaceAPI v15's **official extension mechanism**. Spaces self-host JSON that conforms to SpaceAPI v15; MoM-specific fields go in `ext_mom` so the file stays SpaceAPI-valid. | The exported JSON file (what Maëlle hosts on GitLab Pages) |
| **`mom:`** (JSON-LD prefix / ontology IRI) | The ontology IRI prefix used in MoM's **internal** JSON-LD materialization in Oxigraph (e.g., `mom:operationalState`). | The transformed/materialized representation inside MoM (NOT the file Maëlle hosts) |

These are NOT the same thing. The wizard outputs **SpaceAPI v15 + ext_mom**, because that's what spaces self-host. The `mom:` prefix is internal MoM machinery — Maëlle should never see it.

**What `ext_mom` actually holds in the wizard's exported JSON (M1 scope):**
- `memberOf` — array of network identifiers Maëlle's space belongs to (e.g., `["vulca"]`)
- Canary-only fields (`canary`, `simulatedAge`, `thresholdMode`) are **operator-only**, written by the canary harness, **never exposed in the wizard**.

So `ext_mom` in the wizard = essentially `{ memberOf: [...] }` for M1. Small, focused, honest.

### Field tiers — CORRECTED FRAMEWORK (anagnorisis 2026-05-29)

**Earlier tier mapping was incoherent.** The corrected framework aligns tiers to **schema namespaces**, with each tier serving a distinct interop / feature contract:

| Tier | Namespace | Scope | Examples | What it unlocks |
|---|---|---|---|---|
| **0** | core (subset) | Absolute minimal | `space` (name), `location.address` → derived geoloc/country/tz | Maëlle exits with something valid. Floor. |
| **1** | SpaceAPI v15 **core** | Common to all SpaceAPI apps | `logo`, `url`, `description`, `contact.*`, `state.*` | **Bidirectional interop** with the SpaceAPI ecosystem (mapall.space etc.). We don't promote *all* v15 fields, only a curated set — but what we write IS v15-valid. |
| **2** | `mom:` namespace | **Horizontal** — common to most/all maker networks | `opening_hours`, `memberOf`, **`sdgs`** (transversal, moved here from `ext_fab`) | Unlocks **MoM features** (network membership, opening_hours rendering, SDG cross-filter) — applies to **any** network/silo. |
| **3** | `ext_X` namespace | **Vertical** — silo/community-specific | `ext_fab.equipment`, `ext_fab.space_type`, other `ext_*` for other niches | Each silo defines its own vertical fields. **Future service surface** — niche services can plug in here. |

**Renames (LOCKED):**
- `ext_mom` → **`ext_canary`** — current contents (`canary`, `simulatedAge`, `thresholdMode`) are Mother-Sands-only; "ext_mom" was a misnomer
- Cross-network MoM fields (e.g., `memberOf`) **migrate into the `mom:` namespace** at tier 2
- `ext_fab.sdgs` → **`mom:sdgs`** at tier 2 (SDGs are transversal, not makerspace-exclusive)

**The strategic insight:** tiers 0–2 are MoM's responsibility — interop and core features. **Tier 3 is the open extensibility surface** where new niche services can be defined and offered. That is the future product / monetization frontier (managed-hosting + managed-ontology — already in [[project-schema-bundle-model]]).

**Bernard's tier gates (revised):**
| Tier gate | Bernard's confirmation |
|---|---|
| 0 → exit | *"Name and address. That's the floor. File's valid SpaceAPI v15."* |
| 1 → exit | *"Core's in. Other SpaceAPI apps can read this file as-is."* |
| 2 → exit | *"MoM fields filled. Network features unlocked: membership, opening hours, SDGs."* |
| 3 → exit | *"Silo fields in. Your space's vertical features active."* |

### Sovereignty — corrected (anagnorisis 2026-05-29)

**Earlier draft was wrong** — *"we don't keep a copy"* was an overstatement that would set up a worse betrayal later.

**The honest truth:**
- MoM **snapshots** the published endpoint to SQLite and ingests triples into Oxigraph
- MoM **never edits** the source
- MoM **only ingests what the endpoint publishes** — consent by default through publication
- Source retains full authority. Change at source → MoM follows on next heartbeat.
- **Exception:** terminal conditions (closed/dead) trigger a **minting** process → immutable public record on IPFS/IPLD (`public_ledger`)

**Bernard doesn't overshare.** Sovereignty disclosure on the wizard surface is one short line:

> *"You publish, we make it legible. The rest is history."*

That's it. Double-meaning intentional — "history" points literally to where the lore lives (`mom.mapsofmaking.org`, Epic 8 surface, where the snapshot/ingestion/minting/`public_ledger` story is told properly) AND idiomatically tells Maëlle to stop dwelling and get back to her file. Bernard's whole register in one line: dry, true, self-aware, curiosity-hook without a link, no exclamation marks. **The voice is calibrated.**

### Open questions for next round

1. **`state.open` / `state.lastchange`** — Maëlle's exported file is **static**. It can't reflect "open now." Should the wizard prompt for `opening_hours` (a schedule string, static-friendly) and leave `state` empty? Or set `state.open: null`?
2. **`logo` field** — does the wizard host the logo? Or expect Maëlle to paste a URL? Hosting raises the "we don't keep a copy" sovereignty issue.
3. **Page shape** — single scroll vs. tier-by-tier wizard? Bernard's tier gates suggest **tier-by-tier**, but does that intimidate? Or reassure (clear progress)?

---

## Phase 1 — Round 4: state.open, logo-as-tutorial, wizard re-entry

### 1. state.open — cascading FSM (LOCKED)

Maëlle's exported file is static. State semantics handled by **a small cascading state machine** during the wizard:

```
Q1: "Do you want your space's open/closed status to appear live on the map?"
 ├── YES → Q2
 └── NO  → use opening_hours instead → blue marker → exit FSM
            + note: "Manual updates keep the space from aging.
                     Future option: announce events to keep the file fresh."

Q2: "Do you have a way to update the JSON file when your space opens/closes?
     (Sensor, dashboard, scheduled script, anything that can write a file?)"
 ├── YES → write state.open = false (placeholder), point to automation
 │         tutorial (TBD). Green/black markers will reflect live status once
 │         automation is wired.
 └── NO  → fall back to opening_hours → blue marker.
            Suggest events-field automation as a future seed.
```

**Marker semantics in the exported JSON:**
| Path taken | `state.open` in JSON | `opening_hours` in JSON | Marker on map |
|---|---|---|---|
| Live status, automation ready | `true` / `false` | optional | green / black |
| Live status wanted, no automation yet | `false` (placeholder, ages) | optional | green/black until aging kicks in |
| Opt-out, opening_hours only | **omitted** | required | **blue** |
| Opt-out, no opening_hours | **omitted** | **omitted** | blue with "no live signal" tag |

**Opt-out signal:** Any non-true/false answer in the wizard → `state.open` is **omitted from the exported JSON** entirely. Absence is the signal, not a sentinel value. (Matches Story 3.3 Axis C: "absence reads as no live signal" — first-class scenario, not a bug.)

**Event-field hint:** The card-side displays `event` but it's not in the current JSON schema. Wizard could include an `event` field (under `ext_mom` or in a new convention) as a future seed for "announce next event" automation. **TBD — not M1.**

### 2. Logo — repurpose as the GitLab tutorial (LOCKED)

The chicken-and-egg ("Maëlle has no hosting → can't paste a logo URL") becomes the **practical learning moment** of the GitLab self-hosting tutorial:

```
Tutorial steps (Bernard-narrated):
1. Create GitLab account
2. Create a new repo (private or public — your call)
3. Upload your generated JSON file AND your logo file together
4. Commit
5. Copy the raw URL of the JSON → register it on MoM as your endpoint
6. Copy the raw URL of the logo → return to wizard → paste into the logo field → re-export → re-commit
7. Wait for MoM's next heartbeat (10 min) OR hit refresh on MoM
8. Confirm on the map: your space's card shows the JSON source snapshot
   (Zone 3 source-of-truth) — visible proof, your file, your hosting.
= success milestone
```

**Why this is good design:**
- The "missing logo URL" problem is **not a friction to remove** — it's the **forcing function** that teaches Maëlle the self-hosting loop she'll need for every future update anyway.
- Logo as the **first commit-and-update cycle** is small enough to fail safely. If she gets it wrong, only the logo is broken; the space is still on the map.
- Reinforces the sovereignty story: **the file lives on her repo, not ours.** Bernard demonstrates this concretely by walking her through it.

**Wizard's logo field UX:** field is **optional**, with Bernard's framing —
> *"Skip the logo for now. Get the JSON committed first. Add the logo URL on the next pass — that's a good first edit."*

### 3. Tier-by-tier wizard, with re-entry & validator modes (LOCKED + EXPANDED)

**Tier-by-tier confirmed.** Maëlle can stop after any tier; Bernard names what she's giving up by stopping, never shames her for it.

**MAJOR EXPANSION — the same wizard surface serves three modes:**

| Mode | Trigger | Bernard's role | Pre-fill source |
|---|---|---|---|
| **Onboard** | First visit, no prior JSON | Walk through tier 1 → 3, host the GitLab tutorial | Empty form, baseline.json as schema reference |
| **Update / continue** | Return visit, JSON URL provided | Fetch the URL, validate, pre-fill all tiers, resume where she stopped | Maëlle's own hosted JSON, fetched live |
| **Validate** (expert) | Paste-URL + "validate" affordance | Compliance check — SpaceAPI v15 + MoM-extension validity, no hand-holding | Pasted URL, fetched live |

The validator mode is essentially **MoM's answer to** [SpaceApi/validator](https://github.com/SpaceApi/validator/tree/master/v2) — but with MoM-extension awareness. Experts (potentially Nicolas as operator) get a tool with zero friction.

**Implication for the drawer:** the URL field already exists. We may need a small affordance — "Paste your URL to validate or update" — that's not strictly "register" but "manage." But this is a UX refinement, not a structural change to the drawer.

**Browser-side persistence (LOCKED):**
- All wizard fields auto-saved to **localStorage** as Maëlle types.
- Resilience against accidental close / crash / refresh.
- localStorage is per-browser-per-device — if she switches devices, the URL re-entry path is how she resumes.

**Export & download at any point:** Bernard offers "Save current state as JSON" at every tier gate, not only at the end. The file is always exportable, even mid-form, even invalid — Bernard labels what's missing or wrong but never blocks the download.

### Bernard's role across modes — one voice, three jobs

- **Onboard:** patient translator. Tier gates feel like waypoints.
- **Update:** quiet diff-spotter. Bernard's lines become: *"This was set to X. Still accurate?"*
- **Validate:** dry auditor. *"Tier 1 valid. Tier 2 missing contact.email. Tier 3 unknown: ext_mom.foo (not in schema)."*

Same character. Different job. Right tool, right job, right time.

### Round 4 closing refinements (LOCKED)

**Logo on the card is the emotional payoff.** Seeing your own logo render on your own space's card, served from your own GitLab repo, is the **proof moment** that closes the loop:
- *file → hosting → map → card.* Yours, end to end.
- This is the substantive win that justifies the GitLab tutorial friction.
- The card itself becomes the receipt — Zone 3 source-snapshot already exists for this exact "proof of non-alteration" purpose. The logo render seals the affective half.

**The three modes are one continuous flow, not three forks:**
- No JSON anywhere → Bernard creates from scratch (onboard)
- JSON URL provided → Bernard fetches, validates, allows update (update + validate)
- Cache present in browser → Bernard resumes from cache by default (resume)
- All three states can co-exist. Bernard reconciles silently. Successful validation IS a reward in every mode.

**Bernard's localStorage warning:**
> *"Your progress is saved in this browser. Hard-refresh or clearing site data wipes it. Export at any point if you want a copy outside the browser."*

Honest, no nudge, names the consequence.

### Still open (deferred from Phase 1)

- **GitLab tutorial copy & flow** — needs its own pass. Part of genjson surface, but outside the wizard form itself.
- **Events field convention** — `event` on card but not in JSON. Bridge needed; backlog placeholder.
- **Validator-mode error reporting shape** — inline vs. summary report. Probably both, sketch TBD.
- **Cross-device resume** — only via URL re-fetch. UX copy needs to name this honestly.
- **Drawer affordance for "manage existing URL"** — possibly the same "Your endpoint" input doubles as validate/update entry. Worth checking before locking.

---

## Phase 4 — Decision Tree Mapping (output)

### Scope chunks
A. Drawer changes on MoM map (Bernard one-liner + inline URL input + wizard CTA)
B. Subdomain & infra (`genjson.mapsofmaking.org` DNS/nginx/cert/static page)
C. Wizard core engine (fields, validation, localStorage, export, Bernard tier gates)
D. Nominatim derivation (server-side proxy in `link_handler`, 1 req/s, geopy.Nominatim — same pattern as `scripts/normalize_vow.py`)
E. state.open FSM (cascading questions, marker mapping, opt-out)
F. GitLab tutorial surface (embedded guide, "see logo on card" payoff)
G. Schema/ontology cleanup prerequisite (rename `ext_mom`→`ext_canary`, migrate `sdgs` to `mom:`, add `mom:` namespace fields)
H. Three-mode unification (onboard/update/validate, URL fetch + pre-fill, cache resume)
I. Validator-mode error surfacing (inline + summary)

### Decisions (LOCKED)

1. **Nominatim placement:** Option B — server-side proxy on `link_handler` container. Reuses geopy.Nominatim with `RateLimiter(min_delay_seconds=1)` from `normalize_vow.py`. Single user-agent, clean attribution, server-controlled rate.
2. **Schema cleanup timing:** Pre-genjson. Done as a standalone cleanup story; Makefile wipe/reseed pattern absorbs the cost. Same split-out pattern as the 2026-05-16 pre-3.3 drift-fix story.
3. **Epic placement:** New **Epic 9** (parallel track, no number collision with re-planned Epic 4). Schema cleanup is **promoted out of Epic 9** into a shared cleanup story C.X — because it benefits Epic 4 too.
4. **Track sequencing:** `Cleanup C.X → Epic 9 → Epic 4 re-review`. Rationale: Epic 9's build work will likely surface small further course-corrections to the schema; better to absorb those before Epic 4 re-reviews its AC against a stable target.

### Epic 9 — "Bernard's Workshop" (milestone breakdown)

**M1 — Floor & Core (must-ship)**
- Story 9.1 — Subdomain & infra (`genjson.mapsofmaking.org` DNS + nginx + cert + static scaffold)
- Story 9.2 — Drawer UX on MoM map (Bernard one-liner + inline URL + "Tell me about your space" CTA)
- Story 9.3 — Wizard core: tiers 0 + 1 (name+address → Nominatim → derived fields; SpaceAPI v15 core; localStorage; export)
- Story 9.4 — Nominatim proxy endpoint in `link_handler` (server-side, 1 req/s)
- Story 9.5 — Bernard voice copy pass (intro, tier gates, validation messages, sovereignty line — single curated artifact)

**M2 — MoM features & pedagogy**
- Story 9.6 — Tier 2 (`mom:` fields: `opening_hours`, `memberOf`, `mom:sdgs`)
- Story 9.7 — state.open FSM (cascading questions + marker mapping + opt-out → field omission)
- Story 9.8 — GitLab tutorial surface (embedded guide, "see logo on card" success moment, refresh affordance)

**M3 — Modes & extensibility (nice-to-have, deferrable)**
- Story 9.9 — Three-mode unification (URL fetch → pre-fill update; validator mode; cache resume reconciliation)
- Story 9.10 — Tier 3 (`ext_fab.space_type` fuzzy dropdown, `ext_fab.equipment`)
- Story 9.11 — Validator error UX (inline per-field + summary report)

### Cross-track dependency
- **Cleanup C.X blocks both Epic 9 AND Epic 4 re-review.** Required first.
- **Epic 9 and Epic 4 are otherwise independent after C.X.**
- **Epic 4 re-review deferred until Epic 9 lands** (at minimum, M1; ideally full epic), so that any further small schema course-corrections surfaced by Epic 9 are absorbed before Epic 4's AC re-review.

### Backlog seeds (out of Epic 9 scope)
- Events field convention (`event` on card, missing from JSON schema)
- Future tier-3 niches (other `ext_*` namespaces — community-defined verticals as future service surface)
- Automation tutorials for `state.open` live updates (ESP32, scheduled scripts, etc.)
- Cross-device resume sync (currently URL-fetch only; localStorage is per-browser)

---

## Session close

Phase 1 (Persona Journey) and Phase 2 (Mind Mapping) generated and clustered the design space. Phase 4 (Decision Tree Mapping) produced the epic shape above. Phase 3 (Dream Fusion) skipped — convergence happened naturally without it.

Two anagnorisis moments worth remembering:
1. **Tier framework is namespace-aligned, not feature-aligned.** Tier 0 = floor; Tier 1 = SpaceAPI v15 core (interop); Tier 2 = `mom:` horizontal; Tier 3 = `ext_X` vertical. `ext_mom` was a misnomer and renames to `ext_canary`.
2. **Sovereignty is mirror-not-keep, with one exception (terminal minting on `public_ledger`).** Bernard's one-line disclosure: *"You publish, we make it legible. The rest is history."*

Next step: sprint change proposal at `_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-29.md`.
