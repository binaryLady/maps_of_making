# Bernard — Character Bible (Living Reference)

**Status:** Living document — the single source of truth for Bernard's character, voice,
typography, and the UX rules that govern how they appear in MoM tooling. Consolidates and
supersedes the scattered notes in `mom_handoff_2026-05-15.md` §Bernard, `mom_handoff_2026-05-16.md`,
`sprint-change-proposal-2026-05-29.md`, and `memory/project_bernard_character.md`.

**Last updated:** 2026-05-30 (during Story 9.2 drawer UX iteration).

> **How to use this file:** Any copy, typography, or interaction that involves Bernard's
> voice — wizard, drawer, validation messages, export confirmations, changelog, lore page —
> must cross-check here first. When new decisions are made about Bernard, record them here
> (with date) so the reference stays whole. Final font canon lands in **Story 9.5**.

---

## 1. Identity

- **Name:** Bernard. **Pronouns: they/them — always.** Slip-correct: "Bernard names
  *themselves*," never "himself."
- **Species:** hermit crab (specific species TBD — could set default shell-change cadence;
  see §7). Keeper of **Mother Sands**.
- **Gender-play tension:** "Bernard" (commonly a male name) + "**Mother** Sands" — intentional,
  **do not resolve**. The friction is the point.
- **Home:** Mother Sands — the **8th Maunsell sea-fort that was never planned and never built**.
  Bernard didn't move into a documented historical gap; they **squatted a gap on the map**.
  Maker-hacker mindset: if it's not used, we'll use it. (See §6.)

---

## 2. Personality vector

**"Ron Swanson on a North Sea fort, with notes of *Dredge*."**

- Lead admin. Grumpy, competent, prefers solitude.
- Woodworking, meat, Lagavulin (specifically).
- *Loup de mer / briscard / vieux marin* register — weathered old sailor.
- **Hard shell, soft inside** — but the softness is private, never displayed.
- Factual, no-nonsense, weathered.
- **Does not complain.** "Sands in our underwear is why we never sit" — discomfort is baseline,
  not a topic. Maintenance as worldview, not chore.
- **Claw puns: rationed**, earned by surrounding terseness.
- Imagery touchstone (2026-05-30): *Bernard typing with their claws on an old typewriter
  scavenged from a sunk ship.* This is the felt register — salt-rough, salvaged, deliberate.

---

## 3. Voice guide

**Do:**
- Short sentences. **No exclamation marks.**
- Observation over explanation.
- If something is good, **they say it is fine.** If something is broken, **they say what broke.**
- Maintenance-log voice, not influencer voice. Does not perform enthusiasm.
- Dry humor — lands precisely *because* the surrounding text is sparse.
- State what's valid, state what's broken, name consequences.
- **Pyramid-of-Greatness register, with a grain of salt** — Bernard gets the satire.
  Frankness, sovereignty of choice. No nationalism.

**Forbidden patterns:**
- "most spaces leave this blank"
- "keep it simple"
- "you can do better than them"
- Any nudge that **comforts mediocrity OR shames**.
- **Never rank the user's choices.**

---

## 4. Typography (test phase — canon locked in Story 9.5)

- **Register → typeface:** maintenance-log / salvaged-typewriter voice points to a
  **typewriter/monospace**, NOT handwriting. (Caveat handwriting reads whimsical/personal —
  wrong for Bernard's weathered terseness.)
- **Current test (2026-05-30, Story 9.2 drawer):** `Special Elite` (worn typewriter) on a
  `.bernard-voice` class, fallback `JetBrains Mono`. Confirmed on-vibe — "rough like the sea."
- **Dialogue convention:** Bernard's spoken lines open with an **em-dash (`—`)**, the
  literary/Dredge convention for opening speech. No quotation marks needed.
- **Decision deferred to 9.5:** lock the canonical font (Special Elite vs. a cleaner mono vs.
  another typewriter) and apply it *consistently* across drawer + wizard + lore so surfaces
  don't drift. Do not let each surface pick its own font.

---

## 5. UX rules — how Bernard appears in tooling

**Progressive introduction — Bernard bleeds in gradually (~20% at first touch):**

| Surface | Bernard presence | Rule |
|---|---|---|
| **Map drawer** ("Add your space") | ~20% — register only | **No name reveal.** Dry/frank voice, em-dash, typewriter. No "Bernard," no character. |
| **Wizard path** (`genjson.mapsofmaking.org`) | Full | Bernard **names themselves once**, briefly, on entry: *"Hi, I'm Bernard (they/them) from 'Mother Sands'."* Politeness, not a reward. |
| **Lore page / Epic 8** | Full | Mother Sands, forts, salvage, lifecycle — the whole world. |

**Hard rules:**
- **Bernard NEVER appears on screen as imagery** — no silhouette, no crab, no fort.
  Cognitive-dissonance risk outside lore context. Bernard is the **voice of the copy**, not a face.
- **Name first appears only when the user commits to the wizard path** — never in the drawer,
  never in the URL shortcut.
- **Curiosity hooks** (Mother Sands, they/them) are embedded **without links** — the user must
  navigate away on their own.

**Intentional jargon polarization (Story 9.2 fork):**
- The drawer is a deliberate **fork serving two publics**. The expert branch uses precise
  jargon ("paste **your endpoint URL**") on purpose: it self-selects technical coordinators
  and gently *repels* the non-tech public toward the wizard. The vocabulary does the routing.
- **"your" endpoint URL**, not "a URL" — the possessive asserts **ownership/sovereignty**.
  Coordinators own their URL; MoM never hosts it. ("You publish, we make it legible.")
- This is distinct from the general "decide in 4 seconds, don't provoke a question" rule —
  here the provoked question ("what's an endpoint URL?") *is* the intended signal to take the
  other door.

---

## 6. Mother Sands — Bernard's setting

**What it is:** The 8th Maunsell fort, never planned, never built — squatted on the map.
**Why it matters:** MoM's argument made flesh. Directories ask "are you registered with us?"
MoM asks "do you have an endpoint?" **A space exists because it publishes, not because anyone
authorized it.** Mother Sands is unrecognized by officials — that's not a problem to solve,
it's the point.

**Fort rotation array (U2–U7)** — Bernard relocates between forts on each lifecycle rebirth;
the shell-change made geography:

| Code | Name | Lat | Lng |
|---|---|---|---|
| U2 | Sunk Head | 51.7347° N | 1.2369° E |
| U3 | Tongue Sands | 51.4964° N | 1.2344° E |
| U4 | Knock John | 51.5039° N | 0.9928° E |
| U5 | Nore | 51.4431° N | 0.7441° E |
| U6 | Red Sands | 51.4656° N | 0.9725° E |
| U7 | Shivering Sands | 51.5261° N | 1.0814° E |

U1 (Roughs Tower) excluded — Sealand's platform.

**Endpoint architecture (do not conflate):**
- `mom.mapsofmaking.org` = the **website** (explainer, wiki, lore). Bernard's `schema:url`.
- `mom.mapsofmaking.org/mom_v15status.json` = the **SpaceAPI endpoint** (machine-readable).
  Heartbeat polls this.

**JSON content — whimsical but plausible (Epic 8):** sea-themed, salvage-framed. Open hours
tied to **tide tables** at the current fort (closed at low tide — Bernard is out dredging).
Salvage inventory: tide-powered fabrication, salt-tolerant 3D printer, dredged-WWII-artifact
recycling. Specialties: follows **pass-the-salt.org** (security/privacy — fits the salt/sea
frame). **Bernard doesn't buy materials. They dredge.**

---

## 7. Hermit-crab lifecycle → MoM mechanics

Biology reference: eggs (carried ~1mo, released at high tide) → **zoea** (planktonic, no shell,
4–6 molts) → **megalopa** (finds first shell, leaves water) → **juvenile** (buries to molt,
air-breathing; shell changes every **4–14 days**) → **adult** (shell every **6–18 months**;
lifespan 10–15yr captivity, 40+ wild). Species temperament: Caribbean = eager house-hunters;
Ecuadorian = reluctant. **Bernard's species TBD** — sets whether Mother Sands relocates eagerly
or stubbornly.

| Biology | MoM mechanic |
|---|---|
| Eggs released at high tide | Workshop onboarding batches |
| Zoea (no shell) | Pre-registration — ⚪ seeded |
| Megalopa finds first shell | First registration — ⚪ → 🔵 |
| Juvenile (frequent changes) | Early instability, rapid iteration |
| Adult (slow changes) | Mature canary cadence, rare relocations |
| Molting | Schema upgrade / JSON version bump (milestone) |
| Shell change | Endpoint relocation / host migration (fort rotation) |
| Death | Confirmed closure or N-cycle failure → tombstone |
| Rebirth / new shell | Dead space registers new endpoint — next fort |

---

## 8. Reference inspirations

- **Ron Swanson** (Parks & Rec) — laconic, principled, woodworking, solitude.
- **Dredge** (fishing-horror game, Iron Rig DLC) — North Sea horror, dredging, salvage,
  isolation; offshore platform home base; upgrades from dredged materials.
- **WWII Maunsell forts** — military leftovers, anti-aircraft platforms; the seven that exist.
- **Hermit-crab biology** — shell-changing, molting, lifecycle stages.
- **Pass the Salt** (pass-the-salt.org) — security/privacy hacker con; Bernard is a follower;
  the name fits the salt/sea theme.

### Ron Swanson's Pyramid of Greatness — Bernard's principle source

The **Pyramid of Greatness** (Parks & Rec, Ron Swanson's hand-drawn chart of values) is the
**inspirational backbone of Bernard's principles** — read with a grain of salt (Bernard gets
the satire; the *register* is the point, not literal worship).

What carries into Bernard:
- **Frankness over flattery** — "Honor: If you need it defined, you don't have it." State what
  is, don't perform.
- **Self-reliance & sovereignty** — capability, craftsmanship, owning your tools (and your
  endpoint). MoM's "you publish, we make it legible" is a Pyramid value in disguise.
- **Skill earned, not awarded** — greatness is built, never comforted into being. Hence: no
  comfort-on-mediocrity, no shaming, **never rank the user's choices** — but never lie that
  weak work is strong either.
- **Quiet competence** — "Buffets," "Capitalism," "Cow Protein," "Woodworking": dry, deadpan,
  unbothered. Discomfort is baseline, not a topic.
- **The grain of salt** — the Pyramid is also a joke. Bernard's frankness has wit underneath;
  the satire keeps the principles from tipping into preachiness or nationalism (explicitly
  excluded — see §3).

> Use as a *tone calibrator*, not a checklist. When unsure whether a line is Bernard, ask:
> "Would this sit on the Pyramid — frank, self-reliant, dry — or is it influencer-speak?"

---

## 9. Calibrated lines (reference)

| Moment | Line |
|---|---|
| **Drawer fork** (Story 9.2, no name) | *"— Two ways onto the map. Tell me about your space, or paste your endpoint URL if you've got one. Either's fine."* |
| Wizard intro | *"Hi, I'm Bernard (they/them) from 'Mother Sands'. Let's get your space on the map."* |
| Floor gate (Tier 0) | *"Name and address. That's the floor. Everything else, I'll derive."* |
| Tier 1 exit | *"Core's in. Other SpaceAPI apps can read this file as-is."* |
| Tier 2 exit | *"MoM fields filled. Network features unlocked: membership, opening hours, SDGs."* |
| Tier 3 exit | *"Silo fields in. Your space's vertical features active."* |
| Sovereignty disclosure | *"You publish, we make it legible. The rest is history."* |
| localStorage warning | *"Your progress is saved in this browser. Hard-refresh or clearing site data wipes it. Export at any point if you want a copy outside the browser."* |
| Tombstone — `closed` | *"Closed by operator — March 2026."* |
| Tombstone — `dead` | *"No signal since January 2026 — presumed inactive. Automated inference, not a confirmation."* |

---

## 10. Open threads (deferred, documented)

- **Canonical Bernard font** — lock in Story 9.5; apply consistently across all surfaces.
- **3–4 sample changelog posts** in-character to fully lock the voice (after lore page exists).
- **Bernard's species** — sets relocation temperament.
- **`mom_lore.md`** — repo-as-source, website-as-rendered skeleton (Epic 8 scaffold).
- **Time-bubble demo mode** — ambient fort-rotation engagement loop (Epic 8).
- **Community lore contributions** — governance for in-voice newsletter posts (Epic 8).
- **Monetization** — salvage-art / dredged-material funding frame (Phase 3+, handle carefully).
- **Tombstone data & minting** — who pins IPFS records, who can mint, marker persistence.

---

## 11. Provenance

| Source | Contributes |
|---|---|
| `mom_handoff_2026-05-15.md` §Bernard | Character bible, personality vector, voice guide, Mother Sands lore, lifecycle map, `mom_lore.md` skeleton |
| `mom_handoff_2026-05-16.md` | Pronoun corrections; carry-forward confirmation; Epic 8 placement |
| `sprint-change-proposal-2026-05-29.md` | genjson UX rules, forbidden patterns, calibrated lines, drawer composition rule |
| `memory/project_bernard_character.md` | Condensed voice register + UX rules |
| `memory/feedback_intentional_jargon_polarization.md` | Jargon-as-routing + ownership/sovereignty |
| Story 9.2 session (2026-05-30) | Em-dash dialogue convention, Special Elite typewriter test, salvaged-typewriter imagery, 20%-bleed drawer rule, fork polarization |
