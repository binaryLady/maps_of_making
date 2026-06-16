# Sprint Change Proposal — 2026-06-16

**Trigger:** `_bmad-output/planning-artifacts/mom_handoff_2026-06-16.md`
**Author:** nicolas (via Correct Course)
**Scope classification:** **Major** — epic restructure + cross-epic supersession + net-new capabilities requiring new PRD FRs + superseding architecture decision.
**Mode:** Batch

---

## Section 1 — Issue Summary

A planning session (2026-06-16) resolved the architecture for Epic 6 and produced a handoff
document that **supersedes the existing Epic 6 story list (6.1–6.6)** and **absorbs four Epic 9
stories** into the new Epic 6 write skillset.

The core decision: **one bot, one voice ("Bernard"), internal intent routing.** The previous plan
assumed two bots (a Matrix maintenance bot + a Discord/Telegram discovery bot) and Nanobot as the
agent framework. Both assumptions are reversed:

1. **One channel-agnostic bot.** Platform adapters (Matrix/Discord/Telegram/Mattermost) are
   transport only. An intent classifier routes each message to `write | query | nl_discovery |
   unknown`; the same Bernard voice responds.
2. **No new agent framework for 6.0–6.2.** The dormant `harness/` baseline is extended directly.
   Nanobot is **deferred**, re-evaluated at Story 6.4.
3. **New capability: coordinator write-back via deploy key.** Coordinators own their endpoint JSON;
   the bot edits it on their behalf over an SSH deploy key (JSON patch → git commit → heartbeat
   picks it up). The bot **never writes triples** to Oxigraph (read-only from the bot).
4. **New capability: isochrone travel-time discovery** (OpenRouteService + `shapely`
   point-in-polygon post-filter).

These capabilities have **no Functional Requirements in the current PRD** — the PRD's Epic 6 FRs
(FR37–FR42) describe a read-only NL bot only. The current architecture (ADR-008/013) names Nanobot
as the Epic 6 framework and assumes a two-bot model.

---

## Section 2 — Impact Analysis

| Area | Impact |
|---|---|
| **Epic 6 (epics.md)** | Full restructure. Stories 6.1–6.6 (old read-only NL bot) replaced by 6.0–6.6 (Bernard bot: infra/adapters/router → deploy key → write skillset → read/query+isochrone → NL→SPARQL → voice pass → channel adapters). |
| **Epic 9 (epics.md)** | Stories 9.6, 9.7, 9.9, 9.10 superseded (absorbed by Epic 6.2 write skillset). 9.8 done, 9.11 deferred-still-valid. Tier 1 (9.1–9.5, 9.8, 9.12) remains the first-user vertical slice. |
| **PRD** | New FRs for write skillset, permission model, deploy-key provisioning, template queries, isochrone. Revise FR37/FR42 (one bot, intent router, Matrix-first write). New NFR for deploy-key encryption + bot-read-only-Oxigraph. |
| **Architecture** | New superseding ADR (ADR-017): harness-as-baseline, intent router, deploy-key write path, read-only Oxigraph, ORS isochrone, new deps (`matrix-nio`, `shapely`). ADR-013 (Nanobot) marked deferred-to-6.4. Top banner + requirements-map + data-flow lines updated. |
| **sprint-status.yaml** | Epic 6 story keys replaced (6-0…6-6). Epic 9 keys 9-6/9-7/9-9/9-10 → `superseded`. |
| **Dependencies** | New: `matrix-nio`, `shapely`; external `OpenRouteService` (`ORS_API_KEY`). `httpx`/`cryptography` already present. |
| **Code anchors** | `harness/` (extend), `infra/link_handler/` (add deploy-key endpoint), `infra/docker-compose.yml` (add `mak-agent-bot`), `config.yaml` (`bot.*` block), new `infra/bot/git_ops.py`, `infra/bot/isochrone.py`. |

**Not changed:** Epic 6 remains parallel / non-demo-blocking. The pipeline stays the only Oxigraph
writer. No monetisation gating, no membership handshake, no per-coordinator OAuth (deploy-key only).

---

## Section 3 — Recommended Approach

**Direct Adjustment.** No rollback, no MVP reduction. The decisions are already made in the handoff;
this proposal ratifies and distributes them into the canonical planning artifacts so that
`create-story 6.0` reads a correct source of truth. Net story-count change: Epic 6 goes 6→7 stories
(adds 6.0), Epic 9 loses 4 active stories (→ superseded).

Effort: documentation pass (this proposal + 4 artifact edits). Risk: low — additive; superseded
items are explicitly marked, not deleted. Timeline: unblocks Epic 6 story creation immediately.

---

## Section 4 — Detailed Change Proposals

### 4.1 — sprint-status.yaml

**Epic 6 block** — replace lines under `# Epic 6`:

```yaml
# OLD
  epic-6: backlog
  6-1-nl-sparql-task-with-iop-ontology-context: backlog
  6-2-answer-formatting-source-links-sparql-transparency: backlog
  6-3-graceful-failure-clarification-ontology-gap-logging: backlog
  6-4-discord-ask-mom-command-wired-end-to-end: backlog
  6-5-telegram-adapter: backlog
  6-6-mattermost-custom-adapter: backlog

# NEW
  epic-6: in-progress
  6-0-bot-infrastructure-adapters-intent-router-bernard-config: ready-for-dev
  6-1-deploy-key-provisioning-ssh-git-access: backlog
  6-2-write-skillset-json-patch-git-commit-permission-model: backlog
  6-3-read-query-command-set-isochrone-tool: backlog
  6-4-nl-sparql-natural-language-iop-ontology: backlog
  6-5-graceful-failure-bernard-voice-pass: backlog
  6-6-additional-channel-adapters-discord-telegram-mattermost: backlog
```

**Epic 9 block** — change status on four keys:

```yaml
  9-6-...: superseded   # absorbed by Epic 6.2 (was ready-for-dev)
  9-7-...: superseded   # absorbed by Epic 6.2 (was backlog)
  9-9-...: superseded   # absorbed by Epic 6 (was backlog)
  9-10-...: superseded  # absorbed by Epic 6.2 (was backlog)
```

`last_updated` header bumped to 2026-06-16 with note. (9.11 stays `backlog` — deferred, still valid.)

### 4.2 — epics.md

1. **`editSummary` frontmatter** — append the 2026-06-16 Epic 6 restructure entry.
2. **Epic List entry (§388, "Epic 6")** — retitle to "Ask Bernard — One Bot, Two Skillsets" and
   rewrite the one-liner (channel-agnostic, intent router, write + discovery skillsets, deploy-key
   write path). Update FRs/ARs to the new set. Update `§420` parallel-track note.
3. **Epic 6 full section (§1674–1800)** — replace title, intro, and all six story bodies with the
   new 6.0–6.6 sequence from the handoff (verbatim ACs from handoff §97–298, including deploy-key
   model, permission table, isochrone tool, Bernard voice rules reference).
4. **Epic 9 stories 9.6, 9.7, 9.9, 9.10 (§2053–2110, §2142–2192)** — prepend a `> **SUPERSEDED
   2026-06-16** — absorbed by Epic 6.2 write skillset (see handoff). Not built as wizard tiers;
   coordinators update these fields conversationally via Bernard.` banner. Bodies retained for trail.
5. **Epic 9 Epic List one-liner (§409–410)** — note M2 9.6/9.7 + M3 9.9/9.10 superseded by Epic 6;
   Tier 1 (9.1–9.5, 9.8, 9.12) is the first-user slice.
6. **FR traceability table (§289–297)** — add new FR rows (see 4.3) mapped to Epic 6 stories.

### 4.3 — prd.md

**Revise** in §"Natural Language Bot (Phase 2)":
- **FR37** → "Ask Bernard" — a single channel-agnostic bot; an intent classifier routes each message
  to `write | query | nl_discovery | unknown`; one Bernard voice responds across all skillsets.
- **FR42** → Matrix-first for the **write** skillset (room-based power-level permissions);
  Discord/Telegram/Mattermost carry read/discovery commands only for the PoC.

**Add** new FRs (new subsection "Coordinator Write-Back via Bot (Phase 2)"):
- **FR45** Bot write path: coordinator commands patch the space's **own** endpoint JSON over an SSH
  deploy key (JSON patch → git commit → push). The bot **never** writes triples directly; the
  heartbeat re-ingests on its next cycle. No deploy key registered ⇒ graceful degraded path; read
  commands always work.
- **FR46** Permission model: Matrix power levels map to bot policy (100 = coordinator/any field +
  grant/revoke; 50 = trusted, coordinator-granted fields; 0 = read-only). Member-writable fields are
  a fixed whitelist (`state.open`, `contact.irc/matrix/twitter`); `space.name`, `location.*`, `url`
  are coordinator-only regardless of grant. Commit message `authorized_by: {matrix_user_id}` is the
  audit trail.
- **FR47** Deploy-key provisioning & sovereignty: MOM generates an ed25519 key pair per space,
  private key encrypted at rest (Fernet); coordinator adds the public key to their repo (GitLab /
  GitHub / Codeberg / Gitea); revocation removes MOM's access entirely.
- **FR48** Template query command set (no LLM in the query, only in formatting): `status`, `hours`,
  `find {tag} {city}`, `nearby {city} {radius}`, `network {name}`.
- **FR49** Isochrone travel-time discovery: resolve origin → OpenRouteService isochrone polygon →
  `shapely` point-in-polygon filter over confirmed spaces; degrade to bounding-box (`nearby`) on ORS
  timeout. Seeded-but-unregistered spaces in range surfaced as a follow-up offer.

**Add** NFRs:
- **NFR-S7** Bot has **read-only** Oxigraph access — no SPARQL UPDATE from the bot, ever. Deploy-key
  private keys encrypted at rest (Fernet, key from `BOT_KEY_SECRET`); scope is one repo, one file.

**Note (not rewritten):** PRD prose mentioning "Nanobot" as the Epic 6 framework (Exec Summary,
Innovation §3, Journey 5) is left intact as design-intent trail; a one-line pointer added at the
Innovation §3 / Journey 5 anchors noting the framework decision is now harness-baseline (Nanobot
deferred to Story 6.4) per ADR-017.

### 4.4 — architecture.md

1. **Top banner (§42)** — update the Epic 6 planned-direction line to point at ADR-017 (Bernard
   bot, harness baseline) and note ADR-008/013 (Nanobot) deferred to 6.4.
2. **New ADR-017: "Bernard Bot — One Voice, Two Skillsets, Deploy-Key Write Path"** appended in the
   Core Architectural Decisions area. Captures: channel-agnostic `Message`/`ChannelAdapter`
   protocol; intent classifier (Gemma 4 12B via OpenRouter; Sonnet only for nl_discovery query-gen);
   `harness/` as baseline (no Nanobot for 6.0–6.2); deploy-key model + `infra/bot/git_ops.py`;
   read-only Oxigraph; `infra/bot/isochrone.py` (ORS + shapely); new `mak-agent-bot` compose
   service; new deps `matrix-nio`, `shapely`.
3. **ADR-013 (§455)** — add banner: "**Deferred to Story 6.4** (handoff 2026-06-16). 6.0–6.2 extend
   `harness/` directly; re-evaluate Nanobot when NL→SPARQL lands. See ADR-017."
4. **Requirements map (§981) + data-flow (§1090–1092)** — update the "FR37–42 NL bot" row and the NL
   bot data-flow line to the Bernard router model.

---

## Section 5 — Implementation Handoff

**Scope: Major** → but the analytical replanning is already done in the handoff, so execution is a
documentation distribution pass, not a PM/Architect re-plan.

- **Artifacts to edit (this session):** `sprint-status.yaml`, `epics.md`, `prd.md`,
  `architecture.md` — per Section 4.
- **Then:** `bmad-create-story 6.0` (fresh context) reads the refreshed epics/architecture and
  scaffolds Story 6.0.
- **First dev gate (Story 6.0):** verify `harness/` runs cleanly (drift from Epic 1 spike), then
  `Message` dataclass + Matrix adapter; one room, one `!mom ping`, Bernard responds.

**Success criteria:** `create-story` produces a Story 6.0 file whose context matches the handoff
(adapters, intent router, Bernard config) with no references to the retired 6.1–6.6 NL-bot framing.
