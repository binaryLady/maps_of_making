"""Hermetic tests for the clean-slate canary loader (Story 3.4b, updated Story 3.11).

No HTTP, no Oxigraph — exercises the pure mapping functions in
scripts/load_canary.py. Pins the triple contract the map's materialization
query (urn:mak:canary UNION block) depends on.

Story 3.11 changes:
  - address, countryCode, timeZone now present in output (from extract_mom)
  - openNow / lastOpenChange removed (owned by heartbeat pipeline)
  - lastUpdated renamed to updatedAt (three-token model Axis B)
  - _lit() removed; escape_literal() used internally by extractor
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from load_canary import _classify_lifecycle, build_canary_sparql, GRAPH_URI, SPACE_URI


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _baseline_payload(simulated_age=None) -> dict:
    return {
        "api": "0.13",
        "space": "Mother Sands",
        "logo": "https://mapsofmaking.org/mother-sands-logo.png",
        "url": "https://mapsofmaking.org/canary/mother-sands.json",
        "location": {
            "lat": 51.65,
            "lon": 1.7,
            "address": "Maunsell Fort, North Sea",
            "country_code": "sol-3",
            "timezone": "UTC+0",
        },
        "contact": {"email": "bernard@mothersands.example.org"},
        "state": {"open": True, "lastchange": 1715000000, "message": "nominal"},
        "ext_mom": {"simulatedAge": simulated_age, "canary": True},
    }


# ── Lifecycle classifier ─────────────────────────────────────────────────────

@pytest.mark.parametrize("age,expected", [
    (None, "seeded"),
    (0, "confirmed"),
    (14, "confirmed"),
    (15, "aging"),
    (60, "aging"),
    (61, "zombie"),
    (180, "zombie"),
    (181, "dead"),
])
def test_classify_lifecycle(age, expected):
    assert _classify_lifecycle(age) == expected


# ── Triple contract ──────────────────────────────────────────────────────────

def test_required_triples_present():
    """Required (non-OPTIONAL) triples the materialization query depends on."""
    sparql = build_canary_sparql(_baseline_payload())
    assert f"<{SPACE_URI}> a <https://nicolasdb.github.io/mapsofmaking_ontology/ns#Space>" in sparql
    assert '"Mother Sands"' in sparql
    assert "51.65" in sparql
    assert "1.7" in sparql


def test_new_payload_fields_present():
    """Story 3.11: address, countryCode, timeZone now extracted."""
    sparql = build_canary_sparql(_baseline_payload(simulated_age=0))
    assert "Maunsell Fort, North Sea" in sparql
    assert "sol-3" in sparql
    assert "UTC+0" in sparql


def test_optional_card_triples_present():
    """Optional triples the card renders from."""
    sparql = build_canary_sparql(_baseline_payload(simulated_age=0))
    for pred in ["operationalState", "endpointHealth", "lastFetched", "updatedAt", "source"]:
        assert pred in sparql, f"missing mom:{pred}"
    assert "schema.org/url>" in sparql
    assert "schema.org/logo>" in sparql
    assert "contactJson>" in sparql


def test_freshness_axis_predicates_absent():
    """Heartbeat pipeline owns observedAt/openNow/lastOpenChange — not in loader."""
    sparql = build_canary_sparql(_baseline_payload(simulated_age=0))
    for pred in ["openNow", "lastOpenChange", "observedAt"]:
        assert pred not in sparql, f"freshness predicate leaked into canary loader: mom:{pred}"


def test_writes_only_canary_graph():
    """Isolation: loader DROPs and INSERTs ONLY urn:mak:canary."""
    sparql = build_canary_sparql(_baseline_payload())
    assert sparql.count("DROP") == 1
    assert f"DROP SILENT GRAPH <{GRAPH_URI}>" in sparql
    assert "urn:mak:space/" not in sparql
    assert "urn:mak:public_ledger" not in sparql


def test_seeded_omits_updated_at():
    """A seeded canary has no content-change history — no mom:updatedAt."""
    sparql = build_canary_sparql(_baseline_payload(simulated_age=None))
    assert "updatedAt" not in sparql
    assert 'operationalState> "seeded"' in sparql


def test_confirmed_includes_updated_at():
    sparql = build_canary_sparql(_baseline_payload(simulated_age=0))
    assert "updatedAt" in sparql
    assert 'operationalState> "confirmed"' in sparql


def test_missing_coordinates_raises():
    payload = _baseline_payload()
    del payload["location"]["lat"]
    with pytest.raises(ValueError, match="location"):
        build_canary_sparql(payload)


def test_contact_serialized_as_json():
    sparql = build_canary_sparql(_baseline_payload())
    assert "bernard@mothersands.example.org" in sparql
