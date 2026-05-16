# Handoff Brief: Story 3.3 Narrowing + Epic 8 Stub + Bernard Lore

**Date:** 2026-05-15
**From:** Nicolas (planning session with Claude)
**To:** Claude Code
**Status:** superseded — story creation, epics.md update, mom_lore.md creation

---

## TL;DR

Three deliverables:

1. **Narrow Story 3.3** — drop continuous time-bubble, keep on-demand scenario injection via Makefile commands. Add specific acceptance: canary must reproduce the "fetched-but-stayed-seeded" production bug and `make c-revive` must resolve it.
2. **Create Epic 8 stub** — MOM as Living Space (website, profile card, lore, easter egg, deferred time-bubble demo mode). Parallel to Epic 5, not on demo critical path.
3. **Create `mom_lore.md`** — repo-as-source, website-as-rendered. Structured skeleton with Bernard character, Mother Sands concept, lifecycle metaphor map, milestone events.

Plus a small janitorial item: `.com` → `.org` cleanup pass.

---

## Decision Log (locked in this session)

### Story 3.3 — diagnostic canary

- **Dropped:** continuous time-bubble (1 day = 1h compressed cycle)
- **Kept:** on-demand scenario injection via `mom:simulatedAge` seam
- **Added:** Makefile commands as primary operator interface
- **Added:** 30–60s scripted demo cycle (`make c-demo-cycle`) for presentations
- **Added:** canary must reproduce production bug (fetched-but-stayed-seeded) as acceptance criterion
- **Added:** canary lives in `<urn:mak:canary>` named graph, not `<urn:mak:space/...>` — exempt from production PII rules, materialization query unions both graphs

### Epic 8 — MOM as Living Space (new)

- **Scope:** website at `mom.mapsofmaking.org`, wiki, contact form, Bernard lore page, time-bubble demo mode (deferred from Story 3.3)
- **Critical path:** no — parallel to Epic 5 polish
- **Bernard activation:** before federated PoC demo, gradual awakening as opportunities arise
- **Logo behavior:** standard cursor (no special hover affordance), but click zooms to Mother Sands profile drawer instead of opening a new page — that's the innovation
- **Changelog:** git-commits + curation in Bernard's voice (Phase 3 nanobot-generated entries, deferred)

### Domain + DNS

- **Canonical:** `.org`
- **`.com`:** redirect at DNS or nginx level; remove from docs
- **Subdomains:** `admin.mapsofmaking.org` exists with stub; `mom.mapsofmaking.org` to be added (DNS + nginx + certbot, ~10min, not blocked)

### Tombstones + immutable records (deferred but seeded)

- Tombstones **are queryable** as part of federated graph
- Storage: Oxigraph (queryable) + IPFS/IPLD (permanence)
- Captured milestones: birth, shell change, schema upgrade (molt), death, rebirth
- Phase 3 territory, but canary should prototype shorter lifecycle versions
- Possible Story 3.3b addition: tombstone minting on `make c-death`

---

## Bernard — character bible (for `mom_lore.md`)

**Pronouns:** they/them
**Gender-play tension:** Bernard (commonly male name) + Mother (Mother Sands) — intentional, do not resolve
**Species:** hermit crab, TBD which species (could inform default shell-change cadence)

### Personality vector

**Ron Swanson on a North Sea fort, with notes of Dredge.**

- Lead admin, grumpy, competent, prefers solitude
- Woodworking, meat, Lagavulin (specifically)
- Loup de mer / briscard / vieux marin register
- Hard shell, soft inside — but the softness is private, not displayed
- Factual, no-nonsense, weathered
- Does not complain. "Sands in our underwear is why we never sit (never being idle)" — discomfort is baseline, not topic
- Maintenance as worldview, not chore
- Claw puns: rationed, earned by surrounding terseness

### Voice guide

- Short sentences. No exclamation marks.
- Observation over explanation
- If something is good, they say it is fine
- If something is broken, they say what broke
- Dry humor lands precisely because surrounding text is sparse
- Maintenance-log voice, not influencer voice
- Does not perform enthusiasm

### Reference inspirations

- **Ron Swanson** (Parks & Rec) — laconic, principled, woodworking, solitude
- **Dredge** (fishing horror game, Iron Rig DLC) — North Sea horror, dredging, salvage, isolation; Ironhaven Corp as antagonist-flavored maker corp, Dark Fluid as creeping danger; offshore platform as home base; upgrades unlocked from dredged materials
- **WWII Maunsell forts** — military leftover, anti-aircraft platforms, the seven that exist
- **Hermit crab biology** — shell-changing, molting, lifecycle stages (zoea → megalopa → juvenile → adult)
- **Pass the Salt** (https://2025.pass-the-salt.org/) — security/privacy hacker conference; Bernard is a strong follower; name fits the salt/sea theme perfectly

---

## Mother Sands — space concept

### What it is

The **8th Maunsell fort that was never planned and never built.** Bernard didn't move into a documented historical gap — they **squatted a gap on the map**. Maker-hacker mindset: if it's not used, we'll use it.

### Why this framing matters

This is MOM's argument made flesh. Existing directories ask "are you registered with us?" MOM asks "do you have an endpoint?" Mother Sands embodies the inversion. **A space exists because it publishes, not because anyone authorized it.**

The lore tension is structural, not argued. Mother Sands is unrecognized by officials. That's not a problem to solve — it's the point.

### Geography — fort rotation array (U2–U7)

Bernard relocates between forts on each lifecycle rebirth. The shell-change: a space skipping from platform to the next, each fort a new shell.

| Code | Name | Lat | Lng |
|---|---|---|---|
| U2 | Sunk Head | 51.7347° N | 1.2369° E |
| U3 | Tongue Sands | 51.4964° N | 1.2344° E |
| U4 | Knock John | 51.5039° N | 0.9928° E |
| U5 | Nore | 51.4431° N | 0.7441° E |
| U6 | Red Sands | 51.4656° N | 0.9725° E |
| U7 | Shivering Sands | 51.5261° N | 1.0814° E |

U1 (Roughs Tower) excluded — Sealand's platform.

### Endpoint architecture

- **`mom.mapsofmaking.org`** = the space's **website** (MOM explainer, wiki, lore page)
- **`mom.mapsofmaking.org/mom_v15status.json`** = the space's **SpaceAPI endpoint** (machine-readable)
- These are two different things on the same host. Do not conflate.
- Bernard's `schema:url` → `https://mom.mapsofmaking.org` (human site)
- Heartbeat polls `https://mom.mapsofmaking.org/mom_v15status.json` (machine endpoint)

### The JSON content — whimsical but plausible

**Decision:** deliberately weird, but mapping real space behavior. Sea-themed, salvage-framed.

Ideas to develop during Epic 8 story creation:

- **Open hours tied to tide tables** at the current fort's coordinates — closed during low tide because Bernard is out dredging sea floor for salvage material. Fetch real tide times from a public API at the current geolocation. Obviously imaginary; surprisingly rich detail.
- **Salvage-themed inventory** — tide-powered fabrication, salt-tolerant 3D printer, dredged-WWII-artifact recycling workshop
- **Specialties** — Bernard follows pass-the-salt.org (security/privacy, fits the salt/sea frame)
- **WWII salvage context** — ammo shells, sunken ships, downed aircraft, spiky mines as raw materials. Real sea floor in the Thames estuary has this debris. The lab runs on what the sea gives up.

The lore writes itself once the salvage frame is locked. Bernard doesn't buy materials. They dredge.

---

## Hermit crab lifecycle → MOM mechanics map

The metaphor earns its keep. Each lifecycle stage maps to a federation event.

**Canonical biology reference:**

- **Eggs** — carried by the female for ~1 month on abdomen, released at high tide
- **Zoea** — free-floating planktonic larva, 4–6 molting stages over several months. Drifts. No shell.
- **Megalopa** (glaucothoe) — miniature crab/lobster transitional form. Seeks first shell. Begins spending time out of water.
- **Juvenile** — buries in sand to molt, gills modify for air-breathing, becomes terrestrial. Shell changes every **4–14 days** during rapid growth.
- **Adult** — shell changes every **6–18 months**, linked to molting cycles. Lifespan 10–15 years captivity, 40+ wild.

**Shell change frequency by species:**
- Caribbean hermit crabs — active house-hunters (change often)
- Ecuadorian hermit crabs — reluctant (change only when necessary)

Bernard's species TBD — could inform whether Mother Sands relocates eagerly or stubbornly.

**Mechanic mapping:**

| Biology | MOM mechanic | Notes |
|---|---|---|
| Eggs released at high tide | Workshop onboarding batches | Future: RFF/VOW workshop releases batches of new coordinators |
| Zoea (planktonic, no shell) | Pre-registration: space exists conceptually, no endpoint yet | ⚪ seeded |
| Megalopa finds first shell | First successful registration | ⚪ → 🔵 transition |
| Juvenile (frequent changes, 4–14d) | Early-phase instability, rapid iteration | Mother Sands demo: fast relocations during lifecycle demo |
| Adult (slow changes, 6–18mo) | Mature canary cadence | Rare relocations, mostly stable |
| Molting (shed exoskeleton to grow) | Schema upgrade / JSON version bump | Vulnerable moment, worth marking as milestone |
| Shell change (move to new shell) | Endpoint relocation / host migration | Fort rotation U2–U7 |
| Death | Confirmed closure or N-cycle failure → tombstone | Public immutable record minted |
| Rebirth / new shell | Previously dead space registers new endpoint | Bernard finds next fort in rotation |

---

## The production bug the canary must resolve

Three populations of pins currently on the map:

1. **SpaceAPI directory imports** — real endpoints, heartbeat triggered after import
   - Some correctly `confirmed` ✓
   - Some correctly `open-now` (state.open honored) ✓
   - **Some stuck on `seeded` with `lastUpdated unknown`, despite `last-fetched` showing ~5h ago** ← bug surface
2. **VOW list** — seeded, no endpoint, by design (not expected to advance)
3. **RFF list** — mockup status, no endpoint, by design (not expected to advance)

The bug is population 1, third category: fetched successfully but never advanced `seeded` → `confirmed`.

**Hypotheses (canary discriminates between these):**

- Heartbeat fetched 200, but ingestion didn't write `mom:lastUpdated` (transformation layer / ADR-015 gap)
- Ingestion wrote `mom:lastUpdated`, but `classify_lifecycle` doesn't read it correctly during materialization
- First fetch treated as "no change vs nothing" — diff logic compares against empty baseline incorrectly, skips `mom:lastUpdated` write

**Story 3.3 acceptance must include:** canary reproduces the stuck-seeded state, then `make c-revive` (content diff) transitions it to confirmed. Validates the canary AND gives a path to debug the production bug.

---

## Story 3.3 — Makefile interface

```makefile
# Canary scenario injection — Mother Sands lifecycle exercises
make c-open        # flip state.open true → verify lifecycle clock reset
make c-close       # flip state.open false → no lifecycle reset (sensors-style change)
make c-age         # set simulatedAge=45 → expect aging marker
make c-zombie      # set simulatedAge=120 → expect zombie marker
make c-death       # set simulatedAge=200 → expect dead marker
make c-broken      # endpoint returns 503 → expect broken health
make c-revive      # content diff → reset lifecycle clock, marker back to confirmed
make c-reset       # restore canary to baseline confirmed state
make c-demo-cycle  # full lifecycle in 30–60s — for live demos
```

Each target is a thin wrapper around `scripts/canary_scenario.py --scenario <name>`. Discoverable via `make help`.

---

## `mom_lore.md` skeleton

Suggested structure for Claude Code to scaffold. Sections marked TBD land empty and fill in as Epic 8 develops.

```
mom_lore.md
├── Purpose (internal narrative guardrails + nanobot persona reference)
├── Bernard
│   ├── Character (pronouns, vibe, gender-play tension)
│   ├── Personality vector (Ron Swanson + Dredge + loup de mer)
│   ├── Voice guide (do/don't, register, sample posts — TBD)
│   └── Hermit crab biology (canonical reference, species notes)
├── Mother Sands
│   ├── Concept (8th fort, never planned, squatted occupation)
│   ├── Geography (U2–U7 rotation array with coordinates)
│   ├── Endpoint architecture (website ≠ endpoint, both on mom.mapsofmaking.org)
│   ├── JSON content character (whimsical-but-plausible, salvage-themed — TBD)
│   └── Conflictual occupation (structural, embodied, not argued)
├── Lifecycle metaphor map (biology → MOM mechanics table)
├── Milestone events (birth, shell change, molt, death, rebirth)
├── Reference inspirations (Ron Swanson, Dredge, Maunsell forts, hermit crab biology)
└── Open lore questions
```

---

## Open threads (deferred but documented)

### Time-bubble demo mode

Dropped from Story 3.3 as a diagnostic tool. Deferred to Epic 8 as an engagement loop: visitors can return periodically and watch Bernard move between forts. The full lifecycle in 30–60s (`make c-demo-cycle`) is the Story 3.3 demo artifact. The slow ambient cycle — juveniles change every 4–14 days, adults every 6–18 months — is Epic 8 territory and the reason visitors have a reason to come back.

### Community engagement with Bernard

How far to let community contribute on Bernard's narration and lifecycle? Codebase contributions (GitHub) are straightforward. Lore contributions — newsletter posts in Bernard's voice, fort-specific stories — are interesting but governance unclear. Goal: nudge/hook for people to return and care about their own endpoint. Bernard features new updates and schema "unlocks" from MOM's architecture progression. TBD during Epic 8.

### Monetization (Phase 3+, handle carefully)

What if Bernard dredges the sea floor and creates art from salvaged material — NFTs or similar — that people could buy to fund dev and backend infra while keeping the system independent? The salvage lore frame makes this fit naturally. Out of scope now. Worth a note for later.

### Directory imports (governance question)

Loading full directories like `directory.spaceapi.io` is a shortcut for VOW/RFF to push their network into MOM. Issues:

- Duplicates from spaces member-of multiple directories
- Silent opt-in pushed top-down from network/federation without space's consent or awareness

Mitigation: consent can be inherited via Solid POD + ACLs (next stage). If a space already has a compatible JSON endpoint, they're arguably already aware — this is the SpaceAPI directory situation. Counter-example: fablabs.io — fully incompatible, no endpoint method, large known network of stale records.

Decision: worth considering for demo-pilot phase only, not a permanent ingestion path. Revisit when consent model is clearer.

### Mother Sands JSON content

Deliberately weird, sea-themed, plausible. Specifics TBD pending Bernard's voice being locked. Worth a dedicated session.

### Bernard's voice samples

After `mom_lore.md` exists: write 3–4 sample changelog posts in-character to lock the voice. Future contributors (or the nanobot in Phase 3) can match it.

### Tombstones — what data is captured

Open questions not yet decided:
- Who pins the IPFS/IPLD records? Funding model for persistence?
- Who can mint a tombstone — only MOM, or can the coordinator co-sign?
- Does the pin stay on the map forever as a 🪦 marker?
- Which milestone events beyond death are worth minting? (Birth? Shell change? Molt/schema upgrade?)

Canary's `make c-death` can prototype the flow before these are answered.

---

## Implementation order suggestion

1. **Create `mom_lore.md`** with skeleton + all populated sections from this brief
2. **Narrow Story 3.3** in `epics.md` — replace existing content with Makefile-driven scenario injection + production-bug-reproduction acceptance criterion + `<urn:mak:canary>` named graph decision
3. **Add Epic 8 stub** to `epics.md` — one-paragraph placeholder with scope sketch, parallel/non-blocking status
4. **DNS + nginx prep** for `mom.mapsofmaking.org` — manual task for Nicolas, not blocked
5. **Janitorial:** `grep -r 'mapsofmaking.com' .` cleanup pass, redirect `.com` at DNS or nginx

Story 3.3 implementation work itself comes after this scaffolding is in place.

---

*End of handoff brief.*
