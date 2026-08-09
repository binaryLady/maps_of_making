# Library Proposal — Visual Documentation: IIIF Manifests + Four Corners Context

**Date:** 2026-08-09
**Status:** Draft — first worked example of a Library contribution (field + function pair)
**Depends on:** `community_library_of_tools_structured.md` (the Library vision), Epic 6 (Bernard read commands)
**Author context:** contributed via binaryLady/PR#1 exploration; connects MoM to existing IIIF and Four Corners protocol work

---

## Why this field

The Library's founding principle is *what gets used does not go stale.* Visual
documentation is the highest-leverage data a space can publish — it answers the
questions people actually ask ("what machines do you have? what gets built
there? is this place real and alive?") — but images shared on platforms rot,
lose attribution, and lock the space out of its own archive.

Two mature open protocols already solve this, the same way MoM solves the
directory problem — **self-hosted files at URLs the owner controls, read by
anyone**:

- **IIIF** (International Image Interoperability Framework): an institution
  hosts images plus a JSON-LD *manifest* at a stable URL; any compliant viewer
  can render, deep-zoom, sequence, and annotate them. The museum/archive world's
  version of "you publish, we make it legible."
- **Four Corners**: a presentation convention embedding authorship, backstory,
  related imagery, and licensing into the image's own corners — provenance that
  travels with the artifact instead of living in a platform's database.

MoM already speaks JSON-LD with schema.org terms. This proposal adds one field
and two bot functions.

## The field

Tier 2 (`mom:` namespace), optional, one URL:

```json
{
  "mom:iiifManifest": "https://yourspace.org/iiif/workshop/manifest.json"
}
```

The value MUST be a IIIF Presentation API 3.0 manifest (2.x accepted,
up-converted on read). The space hosts it wherever they host their space file —
same sovereignty rule, same heartbeat reachability semantics: a manifest that
404s is surfaced exactly like a stale endpoint (Axis A applies), never silently
dropped.

**Ontology addition** (`ontology/mom.ttl`):

```turtle
mom:iiifManifest a owl:DatatypeProperty ;
    rdfs:label "IIIF manifest URL" ;
    rdfs:comment "URL of a IIIF Presentation 3.0 manifest documenting the space —
                  machines, builds, community work. Owner-hosted, owner-controlled." ;
    rdfs:domain mom:Space ;
    rdfs:range xsd:anyURI .
```

## Four Corners as the context convention

For each canvas in the manifest, spaces are encouraged (not required) to fill
the four context slots as IIIF annotations with `motivation` values:

| Corner | Content | IIIF mechanism |
|---|---|---|
| Authorship | who made the image / the artifact shown | `requiredStatement` + annotation |
| Backstory | what this build is, why it exists | `describing` annotation |
| Related | links: project repo, OpenFlexure/OKH page, event | `linking` annotation |
| License | reuse terms (defaults to manifest `rights`) | `rights` |

A manifest with all four corners filled earns the subset badge (see scoring) —
same gamification pattern as the existing `mom:card` unlock ladder.

## The paired functions (Bernard)

Per the Library rule, a field ships with functions that make it worth
maintaining:

1. **`!mom show {slug}`** — power 0. Fetches the manifest, replies with the
   space's documented items: label, thumbnail link, and the four-corners
   authorship line per canvas. In rooms, degrades to a link list; the map's
   space card renders thumbnails inline (card zone: below SOURCE DATA).

2. **`!mom find documented {tag} {city}`** — power 0. Extends the existing
   `find` grammar with a `documented` predicate: only spaces whose
   `mom:iiifManifest` resolved on last heartbeat. "Show me spaces with
   documented open-hardware builds near Ghent" becomes answerable with
   *evidence*, not claims.

Implementation surface: `harness/commands.py` registry (+2 entries),
`query_commands.py` for the SPARQL (`?s mom:iiifManifest ?m`), pipeline
`write_payload_fields` extracts the URL like any other Tier-2 field. Manifest
fetching reuses the heartbeat's conditional-GET fetcher — ETag-cached, never
hot-looped.

## Worked example (Mother Sands, canary)

```json
{
  "@context": "http://iiif.io/api/presentation/3/context.json",
  "id": "https://mapsofmaking.org/canary/iiif/manifest.json",
  "type": "Manifest",
  "label": { "en": ["Mother Sands — salvage inventory"] },
  "rights": "http://creativecommons.org/licenses/by-sa/4.0/",
  "requiredStatement": {
    "label": { "en": ["Attribution"] },
    "value": { "en": ["Bernard, Mother Sands. Dredged, not bought."] }
  },
  "items": [
    {
      "id": ".../canvas/1", "type": "Canvas",
      "label": { "en": ["Salt-tolerant 3D printer"] },
      "metadata": [
        { "label": { "en": ["Backstory"] },
          "value": { "en": ["Rebuilt from a hull-crate donor. Prints at high tide only."] } },
        { "label": { "en": ["Related"] },
          "value": { "en": ["https://pass-the-salt.org"] } }
      ]
    }
  ]
}
```

The canary gets the field first (it gets everything first) — cheap to author,
exercises fetch/404/stale paths before any real space adopts it.

## Scoring / unlock

- `mom:iiifManifest` present + resolving → subset score +1, card gains a
  "Documented" zone.
- All four corners present on ≥1 canvas → "Provenance complete" badge.
  Wizard copy (Bernard, Tier 2 exit): *"Pictures with their stories attached.
  That's how it should be done."*

## What this is NOT

- MoM does not host images or manifests. Ever. Same rule as space files.
- No image proxying/caching beyond thumbnail URLs already published in the
  manifest (heartbeat stores the manifest JSON snapshot only — trust receipt
  parity).
- Not a gallery product. The map shows evidence; IIIF viewers (Mirador, UV)
  remain the deep-zoom surface — the card links out to `?manifest=` viewer URLs.

## Open questions

1. Manifest size guard — cap snapshot at N KB? (Recommend 256 KB, matching
   endpoint snapshot norms.)
2. Multiple manifests per space (machines vs. events vs. community work) —
   array now or single-URL-until-someone-asks? (Recommend single URL now;
   IIIF Collections already solve multiplicity inside one URL.)
3. Four Corners authoring UX — a wizard Tier for it, or defer to external IIIF
   tooling (e.g. Bodleian manifest editor) with a link from Bernard's copy?
4. Handshakes tie-in: annotation-based endorsements ("verified opinions" from
   the vision doc) could live as IIIF annotations from *other* spaces'
   identities — deferred to the handshake protocol design.
