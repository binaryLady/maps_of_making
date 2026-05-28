# Feature Requests & User Needs — WhatsApp Chat (Nicolas × Jason)

Extracted from conversation spanning 2024-03 → 2026-05-27. Attributions noted where a specific person is named. Items marked **[NEW]** are not yet covered by the current epics/stories.

---

## 1. Map & Data Display

| # | Request / Need | Who | Date | Status vs Epics |
|---|---|---|---|---|
| 1 | Show **seeded labs in filters** so networks can use the map immediately; highlight those with an active JSON endpoint | Jason | 22/05/26 | Partially in Epic 5 (FR5) — but "highlight early adopters" framing is new **[NEW nuance]** |
| 2 | **World map view** — remove Europe-only restriction for a broader pitch | Jason | 23/05/26 | Epic 1 Story 1.2 sets `maxBounds` to Europe; widening is an explicit departure **[NEW]** |
| 3 | **Cluster toggle** in Tweaks — option to show organic/unclustered view vs grouped pins at zoom out | Nicolas | 05/05/26 | Mentioned as Epic 5 deferred — not yet a story |
| 4 | **Health map legend** must be present when the health overlay is active | Jason | 27/04/26 | Mentioned in UX-DR2 but no dedicated AC |
| 5 | Show **dead space "postmortem"**: why it closed, revival contacts, global pattern analysis | Jason | 27/04/26 | Immutable historical record is in NFR-C3/IPFS; postmortem content field is **[NEW]** |
| 6 | **Simplified default UI** — only show active filters, hide inactive ones; home screen = search bar only ("Google-style") | Jason | 21/04/26 | UX-DR4/5.5 addresses drawer pruning, but explicit "active filters only" logic is **[NEW]** |

---

## 2. Space Registration & Onboarding

| # | Request / Need | Who | Date | Status vs Epics |
|---|---|---|---|---|
| 7 | **One-click email registration** — send an email to register a space with a default JSON listing auto-generated | Jason | 23/05/26 | Current flow is web drawer (Epic 2). Email-based path is explicitly backlogged **[NEW path]** |
| 8 | **Simple email + JSON hosting process** — lower the barrier to creating and self-hosting the JSON file | Jason | 24/05/26 | Workshop content + JSON generator are backlogged in Epic 2 notes; still **[NEW deliverable]** |
| 9 | **QR code displayed in-lab** — makes it easy for the lab's own members to update/claim their space file | Jason | 25/05/26 | Not in any epic **[NEW]** |
| 10 | Replace the "Claim your space" dropdown with **space ID auto-detected in the request** (no manual selection) | Jason | 27/04/26 | Story 2.1 AC notes the system recognises existing spaces — but UX fix not explicitly confirmed |
| 11 | **Waiting list / interest form** for spaces not yet registering, to capture early adopters for later outreach | Jason | 27/04/26 | Not in any epic **[NEW]** |
| 12 | **Add SpaceAPI-listed hackerspaces** as seeds — they already use a compatible format | Jason | 26/04/26 | AR-SEED1 covers VOW; SpaceAPI bulk ingest is not scoped **[NEW scope]** |
| 13 | **Add fablabs.io** dataset | Jason | 23/05/26 | Not in seed pipeline (AR-SEED1 only covers VOW + RFF mockup) **[NEW source]** |
| 14 | **Admin contacts field** in JSON — facilitates handover and internal governance of the space file | Jason | 27/04/26 | NFR-D1 explicitly bans personal data; needs framing as "role contact, not person" **[NEW field, needs GDPR design]** |

---

## 3. Schema & Data Model

| # | Request / Need | Who | Date | Status vs Epics |
|---|---|---|---|---|
| 15 | Add **fablab type fields**: revenue model, main activities, target audience | Jason | 19/05/26 | Not in current MOM schema **[NEW fields]** |
| 16 | Add **SDG profile field** to the JSON schema (after seeing WG Fablabs & SDGs mailer) | Jason | 07/05/26 | Not in current schema **[NEW field]** |
| 17 | Implement **Open Know-Where (OKW) standard** to potentially replace existing IoP/fablabs.io maps | Jason | 22/05/26 | IoP ontology is in scope; OKW alignment is a distinct standard **[NEW alignment]** |
| 18 | Support **"meta/unlinked" field** for freeform data that doesn't map to any known predicate yet | Jason | 08/05/26 | MOM ontology roadmap mentions enrichment signals; explicit passthrough field is **[NEW]** |
| 19 | Schema must support a node being **simultaneously a fablab, a school, and an urban farm** — composable types | Nicolas | 08/05/26 | The 3-layer federated architecture (core + modules) is the design intent; not yet a story |
| 20 | Support **Markdown/HTML pull for a space's "page"** — display a remotely hosted rich profile page within MOM | Jason | 12/05/26 | Not in any epic **[NEW]** |

---

## 4. Search & Bot

| # | Request / Need | Who | Date | Status vs Epics |
|---|---|---|---|---|
| 21 | **NLP search inside chat apps** (Discord, Telegram, Matrix) — not just a web UI | Jason | 24/05/26 | Epic 6 covers this — confirmed priority |
| 22 | **Platform-agnostic bot engine** — build the core separately from platform-specific clients | Jason | 27/05/26 | AR-AGT5 / ChannelAdapter protocol is exactly this — confirmed in architecture |
| 23 | **Multi-query / visit history** — manually select visited spaces → generate a profile query → store in personal JSON | Nicolas | 05/05/26 | Not in any epic **[NEW — individual maker layer, Article 3 territory]** |
| 24 | **Matrix integration** for bot testing + pulling discussion content into AI context | Jason | 12/05/26 | Epic 6 notes Matrix as post-pilot; not current scope |
| 25 | Search by capability + audience type (e.g. "medialabs with AR/VR for youth 12-18") | Vulca group analysis | 17/04/26 | FR37-40 cover NL bot; audience-type as a schema field is **[NEW]** |

---

## 5. Sharing & Social

| # | Request / Need | Who | Date | Status vs Epics |
|---|---|---|---|---|
| 26 | **Copy-link popup** — small notification when a space URL is copied | Jason | 05/05/26 | Not explicitly in any story **[NEW UX micro-detail]** |
| 27 | **URL hash/anchor** on space name and link for direct deep-linking | Jason | 05/05/26 | FR8 covers shareable URL state; space-name anchor is a refinement **[NEW]** |
| 28 | **Auto social media post** each time a space gets verified (🔵) — zero-effort growth loop | Jason | 27/04/26 | Not in any epic **[NEW]** |
| 29 | **Intro popup + video + doc link** on first map load — present the concept to new visitors | Jason | 27/04/26 | Not in any epic **[NEW onboarding]** |
| 30 | **GitBook integration** — attach documentation to the project hub | Jason | 13/04/26 | Article series exists; GitBook-specific integration is **[NEW]** |

---

## 6. Infrastructure & Operations

| # | Request / Need | Who | Date | Status vs Epics |
|---|---|---|---|---|
| 31 | **CRM / feature request tracker** — register user requests, notify them when shipped | Jason | 26/05/26 | Not in any epic **[NEW — meta tooling]** |
| 32 | **Tile hosting reliability** — map was stuck on roadmap; public Protomaps dependency is a fragility | Jason (observed) | 26/05/26 | NFR-I1 addresses self-hosting PMTiles; not yet actioned |
| 33 | **VPS RAM** was overloaded (4 GB, multiple containers) — infrastructure sizing issue | Nicolas | 27/05/26 | Ops concern, not a feature — but signals need to prune non-essential containers |
| 34 | **Self-hosted Discord** (Spacebar) as alternative to Discord dependency | Nicolas | 27/05/26 | Not in any epic **[NEW — infra option]** |

---

## 7. Business Model & Ecosystem

| # | Request / Need | Who | Date | Status vs Epics |
|---|---|---|---|---|
| 35 | **Data leverage interfaces** for projects, suppliers, and funders — not just space discovery | Jason | 12/05/26 | Not in current scope **[NEW — marketplace layer]** |
| 36 | **Open hardware advertising** — mini ads for open source machines only, as a revenue stream | Jason | 09/04/26 | Not in any epic **[NEW — monetization]** |
| 37 | Positioning MOM as a **service to networks** — custom schema creation, workshops, and data apps as a paid offering | Jason | 24/05/26 | Implicit in project vision; not in epics **[NEW — business model]** |
| 38 | MOM as infrastructure after **fablabs.io/Fab Foundation transition** — fill the vacuum | Alberto (via Jason) | 12/05/26 | Not in epics but validates strategic positioning |

---

## 8. User Needs from Field Research

These emerged from real conversations with users / potential adopters — not feature requests per se, but needs the product must address.

| # | Need / Friction | Source | Date |
|---|---|---|---|
| F1 | "Who in the lab is responsible for the data?" — unclear data ownership role inside spaces | Mario, Superlab lab manager (via Jason) | 10/05/26 |
| F2 | "Who's going to take care of it?" — adoption blocker; no perceived owner for the JSON file | Field feedback, Germany tour (Jason) | 12/05/26 |
| F3 | Spaces **don't want to expose open hours** outside scheduled events — security + social friction | Jeffrey + Mario (via Jason) | 10/05/26 |
| F4 | **Nobody wants to list their machines** — risk of theft, attracts uncommitted visitors | German fablab community (via Jason) | 12/05/26 |
| F5 | A lab manager wants **their own profile page** — not available on fablabs.io, blocked by university IT | (unnamed, via Jason) | 12/05/26 |
| F6 | "I'm going to Bath, does anyone know a lab?" → needs a **queryable nomad-maker map** | Vulca WhatsApp (analysed by Nicolas) | 17/04/26 |
| F7 | "Looking for medialabs with AR/VR for youth 12-18" → needs **capability + audience filtering** | Vulca WhatsApp | 17/04/26 |
| F8 | Erasmus+ consortium partner search via WhatsApp noise → needs **structured matchmaking** | Vulca WhatsApp | 17/04/26 |
| F9 | "My FabLab is closed now" (Barcelona) → **live closure signal** absent from all current maps | Vulca WhatsApp | 17/04/26 |
| F10 | "I don't know if the university fab lab is still open" → **stale data is the core trust problem** | Vulca WhatsApp | 17/04/26 |
| F11 | Crafting Futures (UAntwerpen/KU Leuven) building their own Flanders makerspace map → **interoperability / JSON URL adoption pitch** | Jonas Nicolaï (via contact form) | 20/04/26 |
| F12 | Local government (communes) as an addressable audience for the map — civic infrastructure frame | Jason | 09/04/26 |
| F13 | Jonathan (Cambridge, Vulca Coffee) wants to **create a local lab ecosystem map** using MOM | Jonathan (via Jason) | 27/03/26 |

---

## Priority Signal (Jason, 26/05/26)

Explicit priority list from Jason's last ranked to-do:

1. Site web FabTafels
2. Présentation MoM
3. **Enregistrement makerspaces + hosting par défaut** ← maps to items 7, 8 above
4. **Handshake réseau** ← network onboarding/partnership
5. **Search basic fonctionnel** ← maps to Epic 5/6
6. **Bot basic** ← maps to Epic 6
