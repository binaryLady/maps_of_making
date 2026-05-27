"""Extract SpaceAPI v15 core fields to schema.org keys."""
from __future__ import annotations

import json
from typing import Any


def extract_core(payload: dict) -> dict[str, Any]:
    """Extract SpaceAPI v15 core fields from a payload dict.

    Returns a CURIE-keyed dict suitable for triples_for().
    Handles both SpaceAPI v14 flat keys (space, url, location.lat) and
    JSON-LD schema.org keys (schema:name, schema:geo, schema:url).

    Pure function — no HTTP, no SPARQL, no Oxigraph.
    """
    fields: dict[str, Any] = {}

    name = payload.get("space") or payload.get("name") or payload.get("schema:name")
    if name and isinstance(name, str):
        fields["schema:name"] = name

    loc = payload.get("location") or {}
    lat = loc.get("lat")
    lon = loc.get("lon")
    if lat is not None and lon is not None:
        try:
            fields["schema:geo"] = {"lat": float(lat), "lon": float(lon)}
        except (TypeError, ValueError):
            pass

    url = payload.get("url") or payload.get("schema:url")
    if url and isinstance(url, str):
        fields["schema:url"] = url

    logo = payload.get("logo") or payload.get("schema:logo")
    if logo and isinstance(logo, str):
        fields["schema:logo"] = logo

    contact = payload.get("contact")
    if isinstance(contact, dict):
        fields["schema:contactJson"] = json.dumps(contact, separators=(",", ":"))

    desc = payload.get("description") or payload.get("schema:description")
    if desc and isinstance(desc, str):
        fields["schema:description"] = desc

    hours = payload.get("opening_hours") or payload.get("schema:openingHours")
    if hours and isinstance(hours, str):
        fields["schema:openingHours"] = hours

    raw_tags = (
        payload.get("schema:knowsAbout")
        or payload.get("knowsAbout")
        or payload.get("specialties")
    )
    if not raw_tags:
        ext = payload.get("ext") or {}
        if isinstance(ext, dict):
            raw_tags = ext.get("tags")
    if isinstance(raw_tags, str):
        raw_tags = [raw_tags]
    if isinstance(raw_tags, list):
        tags = [str(t) for t in raw_tags if t]
        if tags:
            fields["schema:knowsAbout"] = tags

    # Top-level `memberOf` (preferred) or ext_mom.memberOf (canary convention).
    # Coordinators self-declare network affiliation via slugs ("spaceapi", "vow", ...).
    # Future deferred work: handshake verification against the declared network's
    # directory before honouring (e.g. spaceapi → cross-check directory.spaceapi.io).
    raw_member = payload.get("memberOf")
    if raw_member is None:
        ext_mom = payload.get("ext_mom") or {}
        if isinstance(ext_mom, dict):
            raw_member = ext_mom.get("memberOf")
    if isinstance(raw_member, str):
        raw_member = [raw_member]
    if isinstance(raw_member, list):
        slugs = [str(s).strip() for s in raw_member if isinstance(s, str) and s.strip()]
        if slugs:
            # Expand bare slugs to urn:mak:network/<slug>; pass through full URIs.
            fields["mom:memberOf"] = [
                s if (":" in s or s.startswith("urn:")) else f"urn:mak:network/{s}"
                for s in slugs
            ]

    return fields
