# MOM schema architecture — Claude Code handoff

**Project:** Maps of Making (MOM) — `maps_of_making` repo  
**Context:** Federated PoC Phase 2, post-Epic 3 schema design session  
**Purpose:** Brief Claude Code on the three-layer schema architecture and introduce a parallel community track (OMT health network) as the canonical second-community example. This supersedes any prior schema discussion in this session.

---

> **⚠️ CORRECTIONS (added 2026-05-16 by project maintainer — the source chat had an incomplete picture).** Read the architecture below for the *concepts*; the following facts are authoritative over what the body says:
>
> 1. **Namespace.** The canonical MOM namespace is **`https://nicolasdb.github.io/mapsofmaking_ontology/ns#`** (prefix `mom:`). Every `https://w3id.org/maps-of-making/...` IRI in this document is **illustrative only** — do not use it in code, queries, or `.ttl` files. The three-layer split is real; the `core:` / `fab:` / `omt:` / `edu:` separation will live *under* the canonical namespace, not under `w3id.org`.
> 2. **The ontology repo exists.** It is **`github.com/nicolasdb/mapsofmaking_ontology`**, published via GitHub Pages. It is not the speculative `core/ fab/ omt/ edu/` tree drawn in "The `mom-ontology` repo structure" section — that layout is a *future target*, not current state.
> 3. **Sync model.** `ontology/mom.ttl` in *this* repo is the working copy; the maintainer **manually syncs** it to the `mapsofmaking_ontology` repo when it changes. Any ontology edit lands in `ontology/mom.ttl` first.
> 4. **Operationalization is scheduled.** `core.ttl` + `crosswalk.csv` are **Story 3.5** (Epic 3 tail).

---

## What MOM actually is (one paragraph)

MOM is a **semantic bridge**: spaces and professionals publish a JSON endpoint they already control, MOM crawls it, transforms it to linked open data (MOM JSON-LD → Oxigraph triples), and makes it discoverable on a map and via SPARQL. MOM never owns the data. The endpoint owner decides what to publish. MOM's job is to ingest, surface, warn, and federate — not to gate.

---

## Critical correction: ingestion is permissive, not gating

**Previous assumption (wrong):** MOM rejects fields or endpoints that contain unexpected or non-compliant content.

**Correct behaviour:**
- MOM ingests everything it can parse.
- Fields it doesn't recognise go into the raw snapshot (Zone 3 on the space card) and are logged as schema enrichment signals (`mom:OntologyGap` triples).
- Fields that look like personal data (names, personal emails, personal phones) trigger a **coordinator notification with a CTA** — "We noticed your endpoint contains fields that may include personal data. You decide what to share. Here's what we saw: [field list]. Want to update your endpoint?" The coordinator acts; MOM does not delete or block.
- Hard schema invalids (missing `name`, missing `location.lat/lon`) produce a `"schema_invalid"` outcome in `heartbeat_log` and a notification, but the raw snapshot is still stored. Nothing is silently dropped.

**Why this matters for schema design:** The `mom:required` / `mom:card` / `mom:extended` field tiers (Story 2.7, Pydantic `SpaceAPISchema`) control **what unlocks on the card display**, not what gets ingested. Ingestion is always complete. Display is progressive.

---

## The three-layer schema architecture

### Why three layers

SpaceAPI v15 was designed for hackerspaces. It solves their problems well. MOM needs to serve fablabs, open workshops, health professionals, urban farms, schools, and more. Extending SpaceAPI inline would break the spec for hackerspaces and give MOM no governance boundary. The three-layer model solves this without forking SpaceAPI.

### Layer 1 — SpaceAPI v15 (upstream, not ours)

- Canonical schema: `https://schema.spaceapi.io/15.json`
- MOM accepts SpaceAPI v15 JSON as a valid endpoint format.
- MOM maps SpaceAPI fields to `core:` equivalents at ingestion time (the transformation layer, ADR-015).
- MOM does **not** modify or extend this spec. Any field not in v15 that a space wants to publish goes in a community extension namespace (Layer 3).
- Notable: `contact.keymasters` contains personal names and contact details. MOM's coordinator notification fires if this field is present. The coordinator decides whether to remove it.

Key v15 fields MOM maps:

| SpaceAPI v15 field | maps to | notes |
|---|---|---|
| `space` | `core:name` | `skos:exactMatch` |
| `url` | `core:website` | `skos:exactMatch` |
| `location.lat` + `location.lon` | `core:location` (as `schema:GeoCoordinates`) | `skos:exactMatch` |
| `location.address` | `core:address` | `skos:exactMatch` |
| `contact.email` | `core:contactEmail` | space-level only; personal email triggers CTA |
| `state.open` | `core:isOpen` | boolean; also lifecycle signal (resets freshness clock on change) |
| `logo` | `core:logo` | `skos:exactMatch` |
| `sensors.*` | stored in raw snapshot | not mapped to core; community namespaces may map specific sensors |

### Layer 2 — `core:` base schema (MOM-maintained)

Namespace: `https://w3id.org/maps-of-making/core/`  
File: `ontology/core.ttl`  
Governs: the minimum shared vocabulary every MOM community inherits.

**Rule:** If a concept exists in `core:`, no community extension namespace may redefine it. Extensions must alias via `skos:exactMatch` or `skos:closeMatch` if their field name differs.

`core:` fields:

```turtle
# Identity (inherited from SpaceAPI)
core:name          a owl:DatatypeProperty ; rdfs:range xsd:string .
core:website       a owl:DatatypeProperty ; rdfs:range xsd:anyURI .
core:logo          a owl:DatatypeProperty ; rdfs:range xsd:anyURI .
core:address       a owl:DatatypeProperty ; rdfs:range xsd:string .
core:location      a owl:ObjectProperty  ; rdfs:range schema:GeoCoordinates .
core:contactEmail  a owl:DatatypeProperty ; rdfs:range xsd:string .
core:isOpen        a owl:DatatypeProperty ; rdfs:range xsd:boolean .
core:description   a owl:DatatypeProperty ; rdfs:range xsd:string .

# MOM operational fields (not in SpaceAPI)
core:endpointUrl      a owl:DatatypeProperty ; rdfs:range xsd:anyURI .
core:freshnessStatus  a owl:ObjectProperty .   # mak:confirmed | mak:aging | mak:zombie | mak:dead
core:lastFetched      a owl:DatatypeProperty ; rdfs:range xsd:dateTime .
core:sourceLabel      a owl:DatatypeProperty ; rdfs:range xsd:string .   # "VOW network", "self-registered"
core:communities      a owl:ObjectProperty .   # links to community namespace IRIs this node participates in

# Cross-pollination bridge (critical for multi-community queries)
core:relationships    a owl:ObjectProperty .   # array of typed, tagged links to other endpoints
```

**`core:relationships` structure** (JSON-LD, in the space's endpoint):

```json
"core:relationships": [
  {
    "type": "partner",
    "target_url": "https://ferme-du-bonheur.be/api.json",
    "tags": ["maraîchage", "éducatif", "SDG-04"],
    "since": "2024-03"
  },
  {
    "type": "certified_by",
    "target_url": "https://omt-belgium.org/registry.json",
    "tags": ["OMT", "certification"]
  }
]
```

This field is how cross-community queries work. Without it, a query like "fablabs partnered with a maraîcher network" requires both parties to have used the same field name. With it, the link is explicit in the graph and SPARQL can traverse it.

### Layer 3 — Community extension namespaces

Each community (fablabs, maraîchers, health professionals, schools…) owns a namespace under the `mom-ontology` repo. Rules:

1. A namespace may add fields that don't exist in `core:`.
2. A namespace must never redefine a `core:` field — alias it instead.
3. A node's JSON-LD endpoint declares all namespaces it participates in via `@context` and `@type` arrays.
4. Fields with overlapping meaning across namespaces are resolved in the **crosswalk table** (`ontology/crosswalk.csv`).

A node participating in two communities:

```json
{
  "@context": [
    "https://w3id.org/maps-of-making/core/v1",
    "https://w3id.org/maps-of-making/fab/v1",
    "https://w3id.org/maps-of-making/edu/v1"
  ],
  "@type": ["core:Place", "fab:Fablab", "edu:LearningCentre"],
  "core:name": "OpenFab Brussels",
  "fab:sdgProfile": ["04", "09", "12", "17"],
  "edu:curriculumTags": ["STEAM", "repair_café"],
  "core:relationships": [
    { "type": "certified_by", "target_url": "...", "tags": ["fablabs.io"] }
  ]
}
```

---

## First community: `fab:` (fablabs / makerspaces)

This is the current MOM pilot. The `fab:` namespace extends SpaceAPI v15 beyond hackerspaces to cover fablabs, open workshops, and biolabs. It is the community being built in Epics 0–4.

Key additions over `core:`:

```turtle
fab:spaceType       # "fablab" | "open_workshop" | "biolab" | "hackerspace"
fab:sdgProfile      # array of SDG numbers ["04","09","12","17"]
fab:fablabsIoId     # fablabs.io profile ID for cross-reference
fab:equipment       # array of canonical equipment tags
fab:network         # network membership ("VOW", "RFF", "fablabs.io")
fab:residency       # boolean — hosts visiting makers
```

`fab:equipment` uses `skos:closeMatch` to `core:knowsAbout` (Schema.org). The `category_map.yaml` in the pipeline handles DE→EN tag normalisation.

---

## Second community: `omt:` (orofacial myofunctional therapy)

This is the **canonical second-community example** — a health professional network that faces the exact same structural problem as makerspaces, solved by the same three-layer architecture.

### The problem

Orofacial Myofunctional Therapy (OMT) addresses dysfunctions of mouth, tongue, and facial muscle patterns. It involves multiple specialist types: physicians, dentists, logopèdes (speech-language therapists), kinésithérapeutes (physiotherapists), and others. Only a **certified subset** of each profession is trained in OMT specifically.

The structural failures:
- Multiple siloed directories exist (dental associations, speech therapy boards, physiotherapy registers) — none cross-reference.
- No map exists. A patient in Liège cannot find a certified OMT dentist near them.
- A patient starting treatment with a certified OMT specialist (Specialist A) may unknowingly consult an OMT-unaware specialist (Specialist B) who contradicts the therapy protocol — breaking the treatment strategy, damaging patient trust, and causing measurable health harm.
- Health-tech companies building products for OMT specialists have no reliable registry to target.

### Why this is a MOM problem

Same root cause as makerspaces: **multiple stale directories, no freshness signal, no cross-referencing, no map.** The federation model is identical — each professional or practice publishes a JSON endpoint, MOM crawls it, surfaces it on a map, and enables cross-specialist discovery queries.

### The `omt:` namespace

```turtle
# Who they are
omt:specialistType   # "physician" | "dentist" | "logopede" | "kinesitherapeute" | "health_tech_company"
omt:omtCertified     # boolean — THE critical field. Uncertified specialists are still on the map but visually distinct.
omt:certificationBody     # IRI of the certifying organisation's endpoint
omt:certificationId       # link into the public certification ledger (see below)
omt:certificationDate     # xsd:date

# What they do
omt:acceptsPatients  # boolean
omt:ageGroups        # ["infant", "child", "adolescent", "adult"]
omt:languages        # BCP-47 language tags
omt:treatmentFocus   # ["tongue_thrust", "mouth_breathing", "jaw_dysfunction", "sleep_disordered_breathing"]
omt:sessionFormat    # ["in_person", "teleconsultation", "hybrid"]

# Cross-referencing
omt:affiliatedNetwork      # network or association IRI
omt:collaboratesWith       # array of other specialist endpoint URIs (feeds core:relationships)
```

### Query example this enables

"Find all OMT-certified logopèdes within 30km of patient in Namur who also collaborate with an OMT-certified dentist":

```sparql
SELECT ?logopede ?dentist WHERE {
  ?logopede a omt:OMTSpecialist ;
            omt:specialistType "logopede" ;
            omt:omtCertified true ;
            core:location ?loc .
  FILTER(geof:distance(?loc, "geo:50.46,4.86") < 30)
  
  ?logopede core:relationships ?rel .
  ?rel omt:collaboratesWith ?dentist .
  ?dentist omt:specialistType "dentist" ;
           omt:omtCertified true .
}
```

This query is impossible today — the data doesn't exist in a federated form. With MOM's architecture, it becomes standard SPARQL.

### Pin visual grammar for health communities

Unlike makerspaces, the certified/uncertified distinction is **patient safety critical**, not just administrative. The map must make it unambiguous:

- 🔵 Confirmed + OMT-certified: solid blue pin with a small ✓ badge
- ⚪ Confirmed + not OMT-certified (OMT-adjacent specialty): grey pin, no badge
- ⚠ Certified but certification lapsed/unverified: amber pin (feeds from ledger check)
- 🔴 Endpoint unreachable: broken state (same as makerspace)

Color alone is never sufficient (NFR-A4 — same accessibility rule applies).

---

## The education + certification track

This is a **planned but unscheduled** feature. It extends the architecture to answer: "Where can I get OMT-certified, and how is that certification recorded?"

### The need

An OMT-unaware kinésithérapeute wants to expand their practice. They need to:
1. Find accredited OMT training programmes near them or online.
2. Complete the formation.
3. Have that certification recorded in a way patients and other specialists can verify without a central authority.

This is a new node type that participates in **both** `omt:` and `edu:` namespaces:

```json
{
  "@type": ["core:Place", "edu:TrainingProvider", "omt:CertificationAuthority"],
  "core:name": "Institut de Myologie Fonctionnelle — Brussels",
  "edu:teaches": ["omt:OrofacialMyofunctionalTherapy"],
  "edu:certifies": ["omt:OMTCertification"],
  "edu:formationSchedule": "...",
  "edu:nextSession": "2026-09-15",
  "edu:format": ["in_person", "blended"],
  "omt:certificationBody": true
}
```

### The public certification ledger

Certification records must be:
- **Immutable** — a certification issued in 2024 cannot be quietly deleted or backdated.
- **Verifiable without a central authority** — any patient or colleague can check a certificate hash without trusting one registry.
- **Preservable after the issuing organisation closes** — the "death of a space" problem, applied to certifications.

This maps exactly to the IPFS/IPLD architecture already planned for immutable historical records (NFR-C3, AR-DATA1 snapshot graphs).

**Technical approach (planned, not yet scoped as a story):**

Each issued certification becomes a DAG-JSON node on IPFS:

```json
{
  "type": "omt:OMTCertification",
  "holder_endpoint": "https://dr-martin.be/api.json",
  "holder_name_hash": "<sha256 of canonical name — not the name itself>",
  "certifying_body": "https://iafe.org/registry.json",
  "issued_at": "2024-06-15T09:00:00Z",
  "valid_until": "2027-06-15",
  "programme_cid": "<IPFS CID of the training programme record>",
  "signature": "<certifying body's cryptographic signature>"
}
```

The CID of this node is the `omt:certificationId` stored in the specialist's endpoint. Any client can:
1. Resolve the CID from IPFS.
2. Verify the signature against the certifying body's published public key (also an IPFS node).
3. Check `valid_until` against today's date.

In Oxigraph terms, this lives in the named graph `<urn:mak:ledger/certifications>` with pointers to the IPFS CIDs. The graph is the index; IPFS is the immutable store.

**What's not designed yet:**
- Key management for certifying bodies
- Revocation model (CRLs vs short expiry + re-issue)
- Who pays for IPFS pinning and for how long
- Governance of which certifying bodies are trusted

These are Phase 3 / grant-funded design questions. The architecture accommodates them without requiring them now.

---

## The `mom-ontology` repo structure

This repo does not exist yet. It is the deliverable that makes the multi-community model operational.

```
mom-ontology/
  README.md              ← this document, essentially
  core/
    core.ttl             ← Layer 2 base schema
    context.jsonld       ← @context file for endpoint authors
    CHANGELOG.md
  fab/
    fab.ttl
    context.jsonld
    CHANGELOG.md
  omt/
    omt.ttl              ← placeholder, needs OMT community input
    context.jsonld
    CHANGELOG.md
  edu/
    edu.ttl
    context.jsonld
    CHANGELOG.md
  crosswalk/
    crosswalk.csv        ← overlap resolution table
    crosswalk.md         ← human-readable narrative of the table
  scripts/
    validate_crosswalk.py   ← checks that no extension redefines a core: field
    generate_context.py     ← generates combined @context from multiple namespaces
```

### crosswalk.csv format

```csv
concept,core_field,spaceapi_field,fab_field,omt_field,edu_field,mapping_type,notes
name,core:name,space,,,skos:exactMatch,
geo_coords,core:location,"location.lat+lon",,,skos:exactMatch,lat+lon combined into GeoCoordinates
equipment,core:knowsAbout,,fab:equipment,omt:treatmentFocus,edu:subjects,skos:closeMatch,different semantics but same pattern
contact_email,core:contactEmail,contact.email,,,skos:exactMatch,space-level only — personal email triggers CTA
```

**Rule enforced by `validate_crosswalk.py`:** if `core_field` is non-empty, the extension field column must be empty or contain only an alias declaration. No extension field may share an IRI with a `core:` field.

---

## What Claude Code needs to do with this

### Immediate (current sprint, Epic 3 / Story 3.0)

1. **Verify field names in `tasks/ingest.py` and `tasks/heartbeat.py`** against the SpaceAPI→`core:` mapping table in this document. Any field mapped to a name not in the table above is either a stale name from a prior session or a gap to be added to the crosswalk.

2. **Replace any "reject on field X" logic** with the correct flow: ingest everything, log unrecognised fields as `mom:OntologyGap` triples, queue a coordinator notification for personal-data-looking fields.

3. **Ensure `mom:OntologyGap` triples** (already defined in Story 1.4 and 6.3) are being written for fields that don't match any `core:` or `fab:` predicate. This is the enrichment signal.

### Near term (pre-Article 2 publication)

4. **Create `ontology/core.ttl`** with at minimum the fields listed in Layer 2 above. This file is referenced in Article 2 and must be dereferenceable at `https://w3id.org/maps-of-making/core/`.

5. **Create `ontology/crosswalk.csv`** with the SpaceAPI→`core:` rows plus the `fab:equipment` ↔ `core:knowsAbout` row. Rows for `omt:` and `edu:` are placeholders marked `status: draft`.

### Deferred (not yet a story)

6. `omt:` namespace design requires input from the OMT practitioner community — do not design in isolation. The field list in this document is a **conversation starter**, not a spec.

7. The IPFS/IPLD certification ledger is explicitly unscheduled. Architecture is noted here for continuity; no implementation work until a story is written.

---

## Key framing for any external audience

When explaining this to a grant reviewer, a network coordinator, or an OMT practitioner:

> "Every existing directory asks you to come to them, fill a profile, and trust them to keep it. MOM inverts that: you publish your own data at a URL you control, in a format your community agrees on, and MOM reads it. When you update your data, every map that reads from you updates too. No middlemen. And because MOM is just a reader, multiple maps can read from the same endpoints — the same OMT practitioner can appear on the MOM health map, a regional health authority's patient-facing site, and a research network's discovery tool, all from one JSON file they maintain."

This framing is community-agnostic and applies equally to makerspaces, OMT practitioners, urban farms, and schools.

---

*Document generated: 2026-05-16. Maintained in the Maps of Making project context. Update this document when field names are confirmed in code — it is the single source of truth for the schema architecture until `mom-ontology` repo exists.*
