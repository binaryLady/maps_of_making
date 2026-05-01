"""Unit tests for transformer.py — pure, no HTTP, no Oxigraph."""
import os
import pytest
import tempfile
from pathlib import Path

import transformer
from main import SpaceAPISchema


@pytest.fixture(autouse=True)
def reset_caches():
    """Reset module-level caches between tests."""
    transformer._config = None
    transformer._activity_map = None
    yield
    transformer._config = None
    transformer._activity_map = None


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    """Provide a config pointing to tmp_path for gap_log and heartbeat_db."""
    gap_log = str(tmp_path / "gap_log.txt")
    db_path = str(tmp_path / "heartbeat.db")
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(f"""
operational_state:
  aging_days_threshold: 30
  zombie_days_threshold: 90
  zombie_failures_threshold: 5
  dead_failures_threshold: 10
bandwidth:
  heartbeat_log_path: "{db_path}"
  gap_log_path: "{gap_log}"
activity_map_path: "OVERRIDE_BELOW"
""")
    monkeypatch.setenv("CONFIG_PATH", str(cfg_file))
    return {"gap_log": gap_log, "db_path": db_path, "config_path": str(cfg_file)}


@pytest.fixture
def activity_map_file(tmp_path):
    """Write a small activity_map.yaml for testing."""
    content = """
"holz": "https://nicolasdb.github.io/mapsofmaking_ontology/ns#Woodworking"
"elektronik": "https://nicolasdb.github.io/mapsofmaking_ontology/ns#Electronics"
"3d-druck": "https://nicolasdb.github.io/mapsofmaking_ontology/ns#ThreeDPrinting"
"woodworking": "https://nicolasdb.github.io/mapsofmaking_ontology/ns#Woodworking"
"electronics": "https://nicolasdb.github.io/mapsofmaking_ontology/ns#Electronics"
"3d-printing": "https://nicolasdb.github.io/mapsofmaking_ontology/ns#ThreeDPrinting"
"""
    p = tmp_path / "activity_map.yaml"
    p.write_text(content)
    return str(p)


# ---- AC2: resolve_activities ----

def test_resolve_activities_known_german_tag(activity_map_file, tmp_config):
    result = transformer.resolve_activities(["Holz"], activity_map_path=activity_map_file)
    assert "https://nicolasdb.github.io/mapsofmaking_ontology/ns#Woodworking" in result


def test_resolve_activities_known_english_tag(activity_map_file, tmp_config):
    result = transformer.resolve_activities(["electronics"], activity_map_path=activity_map_file)
    assert "https://nicolasdb.github.io/mapsofmaking_ontology/ns#Electronics" in result


def test_resolve_activities_case_insensitive(activity_map_file, tmp_config):
    result = transformer.resolve_activities(["ELEKTRONIK"], activity_map_path=activity_map_file)
    assert "https://nicolasdb.github.io/mapsofmaking_ontology/ns#Electronics" in result


def test_resolve_activities_unknown_tag_falls_back(activity_map_file, tmp_config):
    result = transformer.resolve_activities(["xyz-unknown-activity"], activity_map_path=activity_map_file)
    assert "xyz-unknown-activity" in result


def test_resolve_activities_deduplication(activity_map_file, tmp_config):
    # "Holz" and "holz" map to same IRI — should appear only once
    result = transformer.resolve_activities(["Holz", "holz"], activity_map_path=activity_map_file)
    wood_iri = "https://nicolasdb.github.io/mapsofmaking_ontology/ns#Woodworking"
    assert result.count(wood_iri) == 1


def test_resolve_activities_logs_unmapped(activity_map_file, tmp_config):
    gap_log = tmp_config["gap_log"]
    transformer.resolve_activities(["xyz-unknown-activity"], activity_map_path=activity_map_file)
    assert Path(gap_log).exists()
    content = Path(gap_log).read_text()
    assert "xyz-unknown-activity" in content
    assert "UNMAPPED_TAG" in content


def test_resolve_activities_multiple_tags(activity_map_file, tmp_config):
    result = transformer.resolve_activities(["Holz", "Elektronik", "3D-Druck"], activity_map_path=activity_map_file)
    assert "https://nicolasdb.github.io/mapsofmaking_ontology/ns#Woodworking" in result
    assert "https://nicolasdb.github.io/mapsofmaking_ontology/ns#Electronics" in result
    assert "https://nicolasdb.github.io/mapsofmaking_ontology/ns#ThreeDPrinting" in result


# ---- AC3: classify_operational_state ----

def test_classify_confirmed(tmp_config):
    state, reason = transformer.classify_operational_state(200, age_days=5, consecutive_failures=0, prior_state="seeded")
    assert state == "confirmed"
    assert reason


def test_classify_aging(tmp_config):
    state, reason = transformer.classify_operational_state(200, age_days=45, consecutive_failures=0, prior_state="confirmed")
    assert state == "aging"
    assert "45" in reason


def test_classify_zombie_by_age(tmp_config):
    state, reason = transformer.classify_operational_state(200, age_days=95, consecutive_failures=0, prior_state="confirmed")
    assert state == "zombie"


def test_classify_zombie_by_failures(tmp_config):
    state, reason = transformer.classify_operational_state(200, age_days=10, consecutive_failures=6, prior_state="confirmed")
    assert state == "zombie"


def test_classify_dead_on_404(tmp_config):
    state, reason = transformer.classify_operational_state(404, age_days=0, consecutive_failures=0, prior_state="confirmed")
    assert state == "dead"
    assert "404" in reason


def test_classify_dead_on_410(tmp_config):
    state, reason = transformer.classify_operational_state(410, age_days=0, consecutive_failures=0, prior_state="confirmed")
    assert state == "dead"


def test_classify_error_no_http(tmp_config):
    state, reason = transformer.classify_operational_state(None, age_days=0, consecutive_failures=0, prior_state=None)
    assert state == "error"


def test_classify_error_5xx(tmp_config):
    state, reason = transformer.classify_operational_state(503, age_days=0, consecutive_failures=0, prior_state="confirmed")
    assert state == "error"
    assert "503" in reason


# ---- AC4: categorize_error (via errors.py) ----

from errors import categorize_error, ErrorType
import httpx as _httpx


def test_categorize_error_timeout():
    error_type, msg = categorize_error(_httpx.TimeoutException("timed out"), None, "")
    assert error_type == ErrorType.TIMEOUT


def test_categorize_error_connection():
    error_type, msg = categorize_error(_httpx.ConnectError("refused"), None, "")
    assert error_type == ErrorType.CONNECTION_REFUSED


def test_categorize_error_http_404():
    error_type, msg = categorize_error(None, 404, "Not Found")
    assert error_type == ErrorType.HTTP_4XX
    assert "404" in msg


def test_categorize_error_http_500():
    error_type, msg = categorize_error(None, 500, "Internal Server Error")
    assert error_type == ErrorType.HTTP_5XX
    assert "500" in msg


def test_categorize_error_redirect():
    error_type, msg = categorize_error(None, 301, "")
    assert error_type == ErrorType.HTTP_3XX


def test_categorize_error_unknown():
    error_type, msg = categorize_error(None, None, None)
    assert error_type == ErrorType.UNKNOWN


# ---- AC7: detect_diff ----

def test_detect_diff_no_change():
    snap = {"schema:name": "FabLab", "schema:openingHours": "Mo-Fr 10-18"}
    result = transformer.detect_diff(snap, snap.copy())
    assert result is None


def test_detect_diff_field_changed():
    old = {"schema:openingHours": "Mo-Fr 10-18"}
    new = {"schema:openingHours": "Mo-Fr 09-18"}
    result = transformer.detect_diff(old, new)
    assert result is not None
    assert any(c["field"] == "schema:openingHours" for c in result["changed"])


def test_detect_diff_field_added():
    old = {"schema:name": "FabLab"}
    new = {"schema:name": "FabLab", "schema:description": "A new description"}
    result = transformer.detect_diff(old, new)
    assert "schema:description" in result["added"]


def test_detect_diff_field_removed():
    old = {"schema:name": "FabLab", "schema:description": "Old desc"}
    new = {"schema:name": "FabLab"}
    result = transformer.detect_diff(old, new)
    assert "schema:description" in result["removed"]


def test_detect_diff_ignores_lastFetched():
    old = {"schema:name": "FabLab", "mom:lastFetched": "2026-01-01T00:00:00Z"}
    new = {"schema:name": "FabLab", "mom:lastFetched": "2026-05-01T00:00:00Z"}
    result = transformer.detect_diff(old, new)
    assert result is None


def test_detect_diff_ignores_array_order():
    old = {"tags": ["electronics", "woodworking"]}
    new = {"tags": ["woodworking", "electronics"]}
    result = transformer.detect_diff(old, new)
    assert result is None


def test_detect_diff_whitespace_ignored():
    old = {"schema:name": "FabLab  "}
    new = {"schema:name": "FabLab"}
    result = transformer.detect_diff(old, new)
    assert result is None


# ---- AC5: transform_to_sparql ----

def _make_schema(**kwargs):
    base = {
        "schema:name": "TestFab",
        "schema:geo": {"schema:latitude": 52.5, "schema:longitude": 13.4},
    }
    base.update(kwargs)
    return SpaceAPISchema.model_validate(base)


def test_transform_to_sparql_basic(tmp_config, activity_map_file):
    schema = _make_schema()
    sparql, snapshot_uri = transformer.transform_to_sparql(schema, {"endpoint_url": "https://example.com/api"})
    assert "TestFab" in sparql
    assert "52.5" in sparql
    assert "13.4" in sparql
    assert "urn:mak:space/testfab" in sparql
    assert snapshot_uri.startswith("urn:mak:space/testfab/")


def test_transform_to_sparql_with_known_tags(tmp_config, activity_map_file):
    schema = _make_schema(**{"schema:knowsAbout": ["woodworking", "xyz-unknown"]})
    os.environ["ACTIVITY_MAP_PATH"] = activity_map_file
    try:
        sparql, _ = transformer.transform_to_sparql(schema, {"endpoint_url": "https://example.com"})
    finally:
        del os.environ["ACTIVITY_MAP_PATH"]
    assert "Woodworking" in sparql  # IRI present
    assert "xyz-unknown" in sparql  # raw fallback present


def test_transform_to_sparql_idempotent(tmp_config, activity_map_file):
    """Calling transform_to_sparql twice with same input produces same SPARQL (modulo timestamp)."""
    schema = _make_schema()
    sparql1, snap1 = transformer.transform_to_sparql(schema, {"endpoint_url": "https://example.com", "space_id": "testfab"})
    sparql2, snap2 = transformer.transform_to_sparql(schema, {"endpoint_url": "https://example.com", "space_id": "testfab"})
    # Snapshot URI date should match (same day)
    assert snap1 == snap2
    # Both use DROP SILENT — idempotent pattern
    assert "DROP SILENT GRAPH" in sparql1
    assert "DROP SILENT GRAPH" in sparql2


def test_transform_to_sparql_missing_name_raises(tmp_config):
    schema = SpaceAPISchema.model_validate({
        "schema:geo": {"schema:latitude": 52.5, "schema:longitude": 13.4}
    })
    with pytest.raises(ValueError, match="resolved_name"):
        transformer.transform_to_sparql(schema, {})


def test_transform_to_sparql_missing_coords_raises(tmp_config):
    schema = SpaceAPISchema.model_validate({"schema:name": "TestFab"})
    with pytest.raises(ValueError, match="coordinates"):
        transformer.transform_to_sparql(schema, {})


def test_transform_to_sparql_skips_unsafe_url(tmp_config, caplog):
    schema = _make_schema(**{"schema:url": "ftp://unsafe.example.com"})
    sparql, _ = transformer.transform_to_sparql(schema, {"endpoint_url": "https://example.com"})
    assert "ftp://" not in sparql


def test_transform_to_sparql_optional_fields(tmp_config):
    schema = _make_schema(**{
        "schema:url": "https://fablab.be",
        "schema:openingHours": "Mo-Fr 10-18",
        "schema:description": "A great space",
        "logo": "https://fablab.be/logo.png",
        "api_compatibility": ["14"],
        "networks": ["Hackerspaces.org"],
    })
    sparql, _ = transformer.transform_to_sparql(schema, {"endpoint_url": "https://fablab.be/api"})
    assert "fablab.be" in sparql
    assert "Mo-Fr 10-18" in sparql
    assert "A great space" in sparql
    assert "logo.png" in sparql
    assert '"14"' in sparql
    assert "Hackerspaces.org" in sparql


def test_transform_to_sparql_geolocation_fidelity(tmp_config):
    schema = _make_schema(**{"mom:geolocationFidelity": "exact", "mom:geolocationNote": "GPS verified"})
    sparql, _ = transformer.transform_to_sparql(schema, {})
    assert "exact" in sparql
    assert "GPS verified" in sparql
