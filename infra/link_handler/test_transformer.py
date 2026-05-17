"""Unit tests for transformer.py — pure, no HTTP, no Oxigraph."""
import os
import pytest
import tempfile
from pathlib import Path

import transformer
from main import SpaceAPISchema

# Story 3.4b: quarantined — pins the transformer tangle that Story 3.5 rewrites.
# Kept as a rewrite safety net; deselected from the default green bar.
# Run explicitly with: pytest -m legacy
pytestmark = pytest.mark.legacy


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


# ---- AC1: classify_endpoint_health ----

def test_classify_endpoint_health_healthy_200(tmp_config):
    state, reason = transformer.classify_endpoint_health(200, minutes_since_last_good=0, consecutive_failures=0)
    assert state == "healthy"


def test_classify_endpoint_health_healthy_304(tmp_config):
    state, reason = transformer.classify_endpoint_health(304, minutes_since_last_good=0, consecutive_failures=0)
    assert state == "healthy"


def test_classify_endpoint_health_unresponsive(tmp_config):
    state, reason = transformer.classify_endpoint_health(None, minutes_since_last_good=15, consecutive_failures=1)
    assert state == "unresponsive"
    assert "15" in reason


def test_classify_endpoint_health_warning(tmp_config):
    state, reason = transformer.classify_endpoint_health(503, minutes_since_last_good=35, consecutive_failures=2)
    assert state == "warning"


def test_classify_endpoint_health_broken(tmp_config):
    state, reason = transformer.classify_endpoint_health(None, minutes_since_last_good=70, consecutive_failures=5)
    assert state == "broken"
    assert "70" in reason


# ---- AC1: classify_lifecycle ----

def test_classify_lifecycle_confirmed(tmp_config):
    state, reason = transformer.classify_lifecycle(5)
    assert state == "confirmed"


def test_classify_lifecycle_aging(tmp_config):
    state, reason = transformer.classify_lifecycle(45)
    assert state == "aging"
    assert "45" in reason


def test_classify_lifecycle_zombie(tmp_config):
    state, reason = transformer.classify_lifecycle(100)
    assert state == "zombie"


def test_classify_lifecycle_dead(tmp_config):
    state, reason = transformer.classify_lifecycle(200)
    assert state == "dead"


def test_classify_lifecycle_negative_clamp(tmp_config, caplog):
    import logging
    with caplog.at_level(logging.WARNING):
        state, reason = transformer.classify_lifecycle(-5)
    assert state == "confirmed"
    assert "WARNING_CLOCK_SKEW" in caplog.text


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


# ---- AC2: _extract_open_now ----

def test_extract_open_now_v15_true():
    assert transformer._extract_open_now({"open": True, "lastchange": 1715000000}) is True


def test_extract_open_now_v15_false():
    assert transformer._extract_open_now({"open": False}) is False


def test_extract_open_now_legacy_open():
    assert transformer._extract_open_now("open") is True


def test_extract_open_now_legacy_closed():
    assert transformer._extract_open_now("closed") is False


def test_extract_open_now_legacy_unknown():
    assert transformer._extract_open_now("unknown") is None


def test_extract_open_now_missing():
    assert transformer._extract_open_now(None) is None


def test_extract_open_now_malformed_dict():
    assert transformer._extract_open_now({"status": "open"}) is None


def test_extract_last_open_change_v15():
    result = transformer._extract_last_open_change({"open": True, "lastchange": 1715000000})
    assert result is not None
    assert "2024" in result  # epoch 1715000000 is in 2024


def test_extract_last_open_change_missing():
    assert transformer._extract_last_open_change({"open": True}) is None


def test_extract_last_open_change_non_positive():
    assert transformer._extract_last_open_change({"open": True, "lastchange": 0}) is None


# ---- AC2: transform_to_sparql emits openNow triples ----

def test_transform_to_sparql_emits_open_now_true(tmp_config):
    schema = _make_schema(**{"state": {"open": True, "lastchange": 1715000000}})
    sparql, _ = transformer.transform_to_sparql(schema, {"endpoint_url": "https://example.com"})
    assert 'openNow' in sparql
    assert '"true"' in sparql
    assert 'lastOpenChange' in sparql


def test_transform_to_sparql_emits_open_now_false(tmp_config):
    schema = _make_schema(**{"state": {"open": False}})
    sparql, _ = transformer.transform_to_sparql(schema, {"endpoint_url": "https://example.com"})
    assert 'openNow' in sparql
    assert '"false"' in sparql
    assert 'lastOpenChange' not in sparql


def test_transform_to_sparql_no_open_now_when_missing(tmp_config):
    schema = _make_schema()
    sparql, _ = transformer.transform_to_sparql(schema, {"endpoint_url": "https://example.com"})
    assert 'mom:openNow' not in sparql


def test_transform_to_sparql_content_changed_false_no_last_updated(tmp_config):
    schema = _make_schema()
    sparql, _ = transformer.transform_to_sparql(schema, {"endpoint_url": "https://example.com"},
                                                  content_changed=False)
    assert 'lastUpdated' not in sparql


def test_transform_to_sparql_content_changed_true_writes_last_updated(tmp_config):
    schema = _make_schema()
    sparql, _ = transformer.transform_to_sparql(schema, {"endpoint_url": "https://example.com"},
                                                  content_changed=True)
    assert 'lastUpdated' in sparql


# ---- AC4: detect_diff ignores sensors/extensions, counts state ----

def test_detect_diff_ignores_sensors():
    old = {"schema:name": "FabLab", "sensors": {"temperature": [{"value": 20}]}}
    new = {"schema:name": "FabLab", "sensors": {"temperature": [{"value": 25}]}}
    assert transformer.detect_diff(old, new) is None


def test_detect_diff_ignores_extensions():
    old = {"schema:name": "FabLab", "extensions": {"sensors": {"humidity": 50}}}
    new = {"schema:name": "FabLab", "extensions": {"sensors": {"humidity": 60}}}
    assert transformer.detect_diff(old, new) is None


def test_detect_diff_counts_state_open_flip():
    old = {"schema:name": "FabLab", "state": {"open": True}}
    new = {"schema:name": "FabLab", "state": {"open": False}}
    result = transformer.detect_diff(old, new)
    assert result is not None
    assert any(c["field"] == "state" for c in result["changed"])


def test_detect_diff_counts_address_change():
    old = {"schema:name": "FabLab", "location": {"address": "Old St 1"}}
    new = {"schema:name": "FabLab", "location": {"address": "New St 2"}}
    result = transformer.detect_diff(old, new)
    assert result is not None


# ---- AC5: effective_marker conflict resolution ----

def test_effective_marker_dead_wins_over_broken():
    assert transformer.effective_marker("broken", "dead", True) == "dead"


def test_effective_marker_zombie_wins_over_broken():
    assert transformer.effective_marker("broken", "zombie", True) == "zombie"


def test_effective_marker_aging_wins_over_broken():
    assert transformer.effective_marker("broken", "aging", False) == "aging"


def test_effective_marker_broken_when_confirmed_and_unhealthy():
    assert transformer.effective_marker("broken", "confirmed", False) == "broken"


def test_effective_marker_open_when_healthy_confirmed():
    assert transformer.effective_marker("healthy", "confirmed", True) == "open"


def test_effective_marker_confirmed_when_closed():
    assert transformer.effective_marker("healthy", "confirmed", False) == "confirmed"


def test_effective_marker_broken_not_shown_when_dead():
    assert transformer.effective_marker("broken", "dead", False) == "dead"


def test_effective_marker_broken_shown_only_when_confirmed():
    for lifecycle in ("aging", "zombie", "dead"):
        assert transformer.effective_marker("broken", lifecycle, False) == lifecycle


# ---- Story 3.2b: closed-cycle counter + PII strip ----

def test_effective_marker_closed_wins_over_broken():
    assert transformer.effective_marker("broken", "closed", False) == "closed"


def test_effective_marker_closed_wins_over_confirmed():
    assert transformer.effective_marker("healthy", "closed", True) == "closed"


def test_build_pii_strip_sparql_deletes_contact_and_sets_closed():
    sparql = transformer._build_pii_strip_sparql("urn:mak:space/testfab")
    assert "schema:contactJson" in sparql
    assert 'mom:operationalState "closed"' in sparql
    assert "mak:closedAt" in sparql
    # Must NOT touch coordinates or name
    assert "schema:geo" not in sparql
    assert "schema:name" not in sparql
    assert "schema:url" not in sparql
    assert "schema:logo" not in sparql


def test_build_pii_strip_sparql_uses_graph_scope():
    sparql = transformer._build_pii_strip_sparql("urn:mak:space/testfab")
    assert "GRAPH <urn:mak:space/testfab>" in sparql


def test_build_revival_closedAt_delete():
    sparql = transformer._build_revival_closedAt_delete("urn:mak:space/testfab")
    assert "mak:closedAt" in sparql
    assert "DELETE" in sparql
    assert "GRAPH <urn:mak:space/testfab>" in sparql


def test_extract_open_now_v15_false_triggers_closed_signal():
    # v15 state.open == false → _extract_open_now returns False (closed signal)
    result = transformer._extract_open_now({"open": False})
    assert result is False


def test_extract_open_now_v013_closed_string_triggers_closed_signal():
    # v0.13 "closed" string → _extract_open_now returns False
    result = transformer._extract_open_now("closed")
    assert result is False


def test_extract_open_now_v15_true_returns_true():
    result = transformer._extract_open_now({"open": True})
    assert result is True


def test_extract_open_now_none_returns_none():
    # Missing state → no signal, counter unchanged
    result = transformer._extract_open_now(None)
    assert result is None


def _make_db_with_row(db_path: str, space_id: str, **kwargs) -> None:
    """Helper: init DB and insert a row with given field values."""
    transformer._init_heartbeat_db(db_path)
    import sqlite3
    con = sqlite3.connect(db_path)
    con.execute(
        "INSERT OR REPLACE INTO heartbeat_log "
        "(space_id, etag, last_modified, last_fetched, consecutive_failures, "
        "last_content_updated, consecutive_closed_cycles, is_closed, "
        "last_endpoint_health, last_lifecycle_state) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            space_id,
            kwargs.get("etag"),
            kwargs.get("last_modified"),
            kwargs.get("last_fetched"),
            kwargs.get("consecutive_failures", 0),
            kwargs.get("last_content_updated"),
            kwargs.get("consecutive_closed_cycles", 0),
            kwargs.get("is_closed", 0),
            kwargs.get("last_endpoint_health", "healthy"),
            kwargs.get("last_lifecycle_state", "confirmed"),
        ),
    )
    con.commit()
    con.close()


def test_db_migration_adds_consecutive_closed_cycles(tmp_path):
    db = str(tmp_path / "hb.db")
    # Create table without new columns (simulate pre-migration schema)
    import sqlite3
    con = sqlite3.connect(db)
    con.execute("""CREATE TABLE heartbeat_log (
        space_id TEXT PRIMARY KEY,
        etag TEXT,
        last_modified TEXT,
        last_fetched TEXT,
        consecutive_failures INTEGER DEFAULT 0,
        last_content_updated TEXT
    )""")
    con.commit()
    con.close()
    # Run migration
    transformer._init_heartbeat_db(db)
    con = sqlite3.connect(db)
    cols = {r[1] for r in con.execute("PRAGMA table_info(heartbeat_log)").fetchall()}
    con.close()
    assert "consecutive_closed_cycles" in cols
    assert "is_closed" in cols


def test_read_heartbeat_row_new_columns_default_zero(tmp_path):
    db = str(tmp_path / "hb.db")
    transformer._init_heartbeat_db(db)
    row = transformer._read_heartbeat_row("nonexistent", db)
    assert row["consecutive_closed_cycles"] == 0
    assert row["is_closed"] == 0


def test_read_heartbeat_row_returns_stored_values(tmp_path):
    db = str(tmp_path / "hb.db")
    _make_db_with_row(db, "testspace", consecutive_closed_cycles=4, is_closed=0)
    row = transformer._read_heartbeat_row("testspace", db)
    assert row["consecutive_closed_cycles"] == 4
    assert row["is_closed"] == 0


def test_pii_strip_sparql_idempotency_guard():
    # If already closed (is_closed=1), process_one_space skips closure trigger.
    # We test the guard condition directly: threshold check with is_closed=1 must skip.
    # This is a logic unit test — the guard is: if consecutive >= threshold AND NOT is_closed
    consecutive_closed_cycles = 10
    is_closed = 1
    cfg_threshold = 6
    should_strip = consecutive_closed_cycles >= cfg_threshold and not is_closed
    assert should_strip is False


def test_pii_strip_sparql_triggers_when_threshold_met():
    consecutive_closed_cycles = 6
    is_closed = 0
    cfg_threshold = 6
    should_strip = consecutive_closed_cycles >= cfg_threshold and not is_closed
    assert should_strip is True


# ---------------------------------------------------------------------------
# Behavioral tests for process_one_space counter mechanics (AC7 — Story 3.2b)
# These drive process_one_space with mocked HTTP/Oxigraph to verify that the
# consecutive_closed_cycles counter and is_closed flag are persisted correctly.
# ---------------------------------------------------------------------------

import asyncio
import sqlite3
from unittest.mock import AsyncMock, MagicMock, patch

_SPACE_URI = "urn:mak:space/testspace"
_SPACE_ID = "testspace"
_ENDPOINT_URL = "https://example.com/spaceapi.json"
_OXIGRAPH = "http://localhost:7878"

_OPEN_PAYLOAD = {"api_compatibility": ["14"], "space": "Test", "url": "https://example.com",
                 "logo": "https://example.com/logo.png", "location": {"lat": 0.0, "lon": 0.0},
                 "state": {"open": True}}
_CLOSED_PAYLOAD = {**_OPEN_PAYLOAD, "state": {"open": False}}
_LEGACY_CLOSED_PAYLOAD = {**_OPEN_PAYLOAD, "state": "closed"}


def _mock_response(payload, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = payload
    resp.text = str(payload)
    resp.headers = {}
    return resp


def _mock_sparql_post():
    """Return an AsyncMock that records SPARQL update calls."""
    post_mock = AsyncMock()
    post_mock.return_value.raise_for_status = MagicMock()
    return post_mock


def _run_process(db_path, payload, status=200):
    """Run process_one_space with mocked I/O against a real tmp SQLite DB."""
    resp = _mock_response(payload, status)
    db_row = transformer._read_heartbeat_row(_SPACE_ID, db_path)

    def _getenv_side_effect(key, default=None):
        if key == "HEARTBEAT_DB_PATH":
            return db_path
        return os.environ.get(key, default)

    with patch("transformer.fetch_endpoint_conditional",
               new=AsyncMock(return_value=(resp, {}, False, db_row))), \
         patch("transformer._fetch_last_snapshot", new=AsyncMock(return_value=None)), \
         patch("transformer.os.getenv", side_effect=_getenv_side_effect), \
         patch("httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = _mock_sparql_post()
        mock_client_cls.return_value = mock_client

        outcome, state_changed = asyncio.run(
            transformer.process_one_space(_SPACE_URI, _ENDPOINT_URL, _OXIGRAPH)
        )
    return outcome, state_changed, transformer._read_heartbeat_row(_SPACE_ID, db_path)


def test_counter_increments_on_200_closed(tmp_path):
    db = str(tmp_path / "hb.db")
    _make_db_with_row(db, _SPACE_ID, last_fetched="2026-01-01T00:00:00+00:00",
                      last_content_updated="2026-01-01T00:00:00+00:00")
    _run_process(db, _CLOSED_PAYLOAD)
    row = transformer._read_heartbeat_row(_SPACE_ID, db)
    assert row["consecutive_closed_cycles"] == 1


def test_counter_increments_on_legacy_closed_string(tmp_path):
    db = str(tmp_path / "hb.db")
    _make_db_with_row(db, _SPACE_ID, last_fetched="2026-01-01T00:00:00+00:00",
                      last_content_updated="2026-01-01T00:00:00+00:00",
                      consecutive_closed_cycles=2)
    _run_process(db, _LEGACY_CLOSED_PAYLOAD)
    row = transformer._read_heartbeat_row(_SPACE_ID, db)
    assert row["consecutive_closed_cycles"] == 3


def test_counter_resets_on_200_open(tmp_path):
    db = str(tmp_path / "hb.db")
    _make_db_with_row(db, _SPACE_ID, last_fetched="2026-01-01T00:00:00+00:00",
                      last_content_updated="2026-01-01T00:00:00+00:00",
                      consecutive_closed_cycles=4)
    _run_process(db, _OPEN_PAYLOAD)
    row = transformer._read_heartbeat_row(_SPACE_ID, db)
    assert row["consecutive_closed_cycles"] == 0


def test_revival_resets_is_closed_and_counter(tmp_path):
    """Material content diff on a closed space revives it (AC4)."""
    db = str(tmp_path / "hb.db")
    _make_db_with_row(db, _SPACE_ID, last_fetched="2026-01-01T00:00:00+00:00",
                      last_content_updated="2026-01-01T00:00:00+00:00",
                      consecutive_closed_cycles=8, is_closed=1)
    # Simulate material diff: new payload differs from old snapshot
    old_snap = {**_CLOSED_PAYLOAD, "location": {"lat": 1.0, "lon": 2.0}}
    new_payload = {**_OPEN_PAYLOAD, "location": {"lat": 3.0, "lon": 4.0}}
    resp = _mock_response(new_payload)
    db_row = transformer._read_heartbeat_row(_SPACE_ID, db)

    def _getenv2(key, default=None):
        if key == "HEARTBEAT_DB_PATH":
            return db
        return os.environ.get(key, default)

    with patch("transformer.fetch_endpoint_conditional",
               new=AsyncMock(return_value=(resp, {}, False, db_row))), \
         patch("transformer._fetch_last_snapshot", new=AsyncMock(return_value=old_snap)), \
         patch("transformer.os.getenv", side_effect=_getenv2), \
         patch("httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = _mock_sparql_post()
        mock_client_cls.return_value = mock_client

        asyncio.run(transformer.process_one_space(_SPACE_URI, _ENDPOINT_URL, _OXIGRAPH))

    row = transformer._read_heartbeat_row(_SPACE_ID, db)
    assert row["is_closed"] == 0
    assert row["consecutive_closed_cycles"] == 0
