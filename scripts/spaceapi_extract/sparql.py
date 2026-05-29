"""SPARQL triple-emission helpers for the spaceapi_extract library.

escape_literal  — consolidates _lit() (load_canary.py) and sparql_str() (seed_spaceapi.py)
triples_for     — type-aware triple builder; callers own the SPARQL envelope and mutation semantics
"""
from __future__ import annotations

from typing import Any

_NS = {
    "schema": "https://schema.org/",
    "mom": "https://nicolasdb.github.io/mapsofmaking_ontology/ns#",
}

XSD_DT = "http://www.w3.org/2001/XMLSchema#dateTime"
XSD_BOOL = "http://www.w3.org/2001/XMLSchema#boolean"

# CURIEs whose values are URL strings and must be emitted as SPARQL IRIs
_IRI_PREDS = {"schema:url", "schema:logo", "mom:endpointUrl", "mom:profileUrl"}

# CURIEs whose values are lists of URIs (multi-value, IRI-emitted, one triple each)
_IRI_LIST_PREDS = {"mom:memberOf"}

# CURIEs whose string values are ISO-8601 datetime and must carry ^^xsd:dateTime
_DT_PREDS = {"mom:lastOpenChange", "mom:updatedAt", "mom:observedAt", "mom:lastFetched"}


def _expand(curie: str) -> str:
    """Expand a CURIE to a full URI, or return as-is if already a full URI/URN."""
    if "://" in curie or curie.startswith("urn:"):
        return curie
    prefix, local = curie.split(":", 1)
    return _NS[prefix] + local


def escape_literal(val: str) -> str:
    """Escape and quote a string as a SPARQL double-quoted literal.

    Reference implementation: load_canary._lit() — handles \\, ", \\n, \\r, \\t.
    """
    escaped = (
        str(val)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def triples_for(subject_uri: str, fields: dict[str, Any]) -> list[str]:
    """Emit type-aware SPARQL triple strings from a predicate→value dict.

    Keys are CURIEs (schema:name, mom:address, …) or full URIs.
    None values are silently skipped.
    Handles:
      - schema:geo         → blank node with schema:latitude / schema:longitude
      - schema:knowsAbout  → one triple per list element (multi-value)
      - bool values        → ^^xsd:boolean literal
      - _DT_PREDS          → ^^xsd:dateTime literal
      - _IRI_PREDS         → <IRI> (not a quoted literal)
      - everything else    → plain quoted literal via escape_literal
    """
    out: list[str] = []
    for curie, val in fields.items():
        if val is None:
            continue
        pred_uri = _expand(curie)

        if curie == "schema:geo":
            if isinstance(val, dict):
                lat = val.get("lat")
                lon = val.get("lon")
                if lat is not None and lon is not None:
                    lat_uri = _expand("schema:latitude")
                    lon_uri = _expand("schema:longitude")
                    out.append(
                        f"<{subject_uri}> <{pred_uri}> "
                        f"[ <{lat_uri}> {float(lat)} ; <{lon_uri}> {float(lon)} ] ."
                    )
            continue

        if curie == "mom:sdgs":
            items = val if isinstance(val, list) else [val]
            for item in items:
                out.append(f"<{subject_uri}> <{pred_uri}> {int(item)} .")
            continue

        if curie == "schema:knowsAbout":
            items = val if isinstance(val, list) else [val]
            for item in items:
                if item:
                    out.append(
                        f"<{subject_uri}> <{pred_uri}> {escape_literal(str(item))} ."
                    )
            continue

        if curie in _IRI_LIST_PREDS:
            items = val if isinstance(val, list) else [val]
            for item in items:
                if item:
                    out.append(f"<{subject_uri}> <{pred_uri}> <{item}> .")
            continue

        if isinstance(val, bool):
            out.append(
                f'<{subject_uri}> <{pred_uri}> "{str(val).lower()}"^^<{XSD_BOOL}> .'
            )
            continue

        if curie in _DT_PREDS:
            out.append(
                f'<{subject_uri}> <{pred_uri}> "{val}"^^<{XSD_DT}> .'
            )
            continue

        if curie in _IRI_PREDS:
            out.append(f"<{subject_uri}> <{pred_uri}> <{val}> .")
            continue

        out.append(f"<{subject_uri}> <{pred_uri}> {escape_literal(str(val))} .")

    return out
