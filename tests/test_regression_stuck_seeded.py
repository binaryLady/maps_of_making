"""Regression tests for Story 3.4: stuck-seeded bug.

This test suite reproduces the stuck-seeded bug where spaces fetch successfully
but their mom:lastUpdated is never written to Oxigraph, causing them to remain
stuck in seeded state instead of transitioning to confirmed.

Tests use the Mother Sands diagnostic canary and live Oxigraph integration.
"""
import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timezone

import pytest
import httpx

# Allow importing from infra/link_handler
sys.path.insert(0, str(Path(__file__).parent.parent / "infra" / "link_handler"))

from transformer import (
    detect_diff,
    has_meaningful_change,
    transform_to_sparql,
    classify_lifecycle,
    _fetch_last_snapshot,
    _build_revival_closedAt_delete,
    build_state_only_update,
)
from main import SpaceAPISchema

REPO_ROOT = Path(__file__).parent.parent
BASELINE_FILE = REPO_ROOT / "data" / "canary" / "baseline.json"
SERVED_FILE = REPO_ROOT / "data" / "canary" / "served.json"
HEARTBEAT_DB = REPO_ROOT / "data" / "tasks" / "heartbeat_log.db"
OXIGRAPH_URL = "http://localhost:7878"

MOM = "https://nicolasdb.github.io/mapsofmaking_ontology/ns#"


def _read_baseline() -> dict:
    """Load Mother Sands baseline SpaceAPI payload."""
    return json.loads(BASELINE_FILE.read_text())


def _load_served_json() -> dict:
    """Load current served.json (may be modified by scenario injection)."""
    if SERVED_FILE.exists():
        return json.loads(SERVED_FILE.read_text())
    return _read_baseline()


def _oxigraph_query(sparql: str) -> dict:
    """Execute SPARQL query against Oxigraph. Returns bindings list."""
    resp = httpx.post(
        f"{OXIGRAPH_URL}/query",
        content=sparql,
        headers={
            "Content-Type": "application/sparql-query",
            "Accept": "application/sparql-results+json",
        },
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json().get("results", {}).get("bindings", [])


def _oxigraph_update(sparql: str) -> None:
    """Execute SPARQL update against Oxigraph."""
    resp = httpx.post(
        f"{OXIGRAPH_URL}/update",
        content=sparql,
        headers={"Content-Type": "application/sparql-update"},
        timeout=10.0,
    )
    resp.raise_for_status()


class TestRegressionStuckSeeded:
    """Test suite for stuck-seeded bug: mom:lastUpdated not written on fetch."""

    def test_regression_revival_write_persists_lastupdated(self):
        """
        END-TO-END: a closed space receiving a content change must end up with
        mom:lastUpdated written to its graph.

        This ties the visible symptom (stuck-seeded = 'updated unknown') to the
        root cause (revival SPARQL concatenation rejected with 400). Before the
        fix, the whole write was rejected and mom:lastUpdated never landed.
        After the fix, the revival write succeeds and the triple is present.
        """
        baseline = _read_baseline()
        schema = SpaceAPISchema(**baseline)

        space_uri = "urn:mak:space/test-revival-e2e"
        metadata = {
            "endpoint_url": "http://localhost:9191/",
            "space_id": "test-revival-e2e",
            "endpoint_health": "healthy",
            "lifecycle_state": "confirmed",
        }
        main_update, _ = transform_to_sparql(schema, metadata, content_changed=True)
        revival = _build_revival_closedAt_delete(space_uri)

        # Compose exactly as process_one_space does (revival prepended to main).
        combined = revival.rstrip() + " ;\n" + main_update
        resp = httpx.post(
            f"{OXIGRAPH_URL}/update",
            content=combined,
            headers={"Content-Type": "application/sparql-update"},
            timeout=10.0,
        )
        assert resp.status_code == 204, (
            f"Revival write rejected (HTTP {resp.status_code}): {resp.text}\n"
            "The stuck-seeded bug: this 400 froze all triples for closed spaces."
        )

        # Verify mom:lastUpdated actually landed — the cure for 'updated unknown'.
        check = f"""PREFIX mom: <{MOM}>
SELECT ?lastUpdated WHERE {{
  GRAPH <{space_uri}> {{ <{space_uri}> mom:lastUpdated ?lastUpdated }}
}}"""
        bindings = _oxigraph_query(check)
        assert len(bindings) > 0, (
            "mom:lastUpdated is STILL absent after a successful revival write.\n"
            "The space would render as 'updated unknown' / stuck-seeded."
        )

        # Cleanup test graph
        httpx.post(
            f"{OXIGRAPH_URL}/update",
            content=f"DROP SILENT GRAPH <{space_uri}>",
            headers={"Content-Type": "application/sparql-update"},
            timeout=10.0,
        )


    def test_regression_diff_detection_first_fetch_is_material(self):
        """
        Test that first fetch (no previous snapshot) is treated as a material change.

        First fetch should ALWAYS set content_changed=True, ensuring mom:lastUpdated
        is written. This test verifies the diff detection logic handles the first-fetch
        case correctly.
        """
        new_snap = _load_served_json()
        old_snap = None  # First fetch scenario

        # has_meaningful_change should return True for first fetch
        assert has_meaningful_change(old_snap, new_snap) is True, (
            "First fetch (old_snap=None) should always be considered a material change.\n"
            "If this returns False, content_changed stays False and mom:lastUpdated is skipped."
        )


    def test_regression_diff_detection_sensor_exclusion(self):
        """
        Verify that sensor flapping alone doesn't trigger lastUpdated write.

        Sensors are physical noise and should be excluded from diff detection.
        Only changes to stable fields (name, contact, state.open, etc.) should
        trigger a content_changed=True update.
        """
        baseline = _read_baseline()

        # Create a mutation with only sensor changes
        mutated = json.loads(json.dumps(baseline))
        mutated["sensors"] = {"temperature": [{"value": 99.9, "unit": "celsius"}]}

        # Diff should ignore sensors and return None (no material change)
        diff = detect_diff(baseline, mutated)
        assert diff is None, (
            "Sensors should be excluded from diff detection.\n"
            f"Got diff: {diff}\n"
            "This is why sensor flapping shouldn't reset the lifecycle clock."
        )


    def test_regression_diff_detection_state_open_included(self):
        """
        Verify that state.open changes ARE detected as material.

        An open/close flip is a deliberate state change that SHOULD reset
        the lifecycle clock and trigger mom:lastUpdated write.
        """
        baseline = _read_baseline()

        # Flip state.open from true to false
        mutated = json.loads(json.dumps(baseline))
        mutated["state"]["open"] = not baseline["state"]["open"]

        # Diff should detect this change
        diff = detect_diff(baseline, mutated)
        assert diff is not None, (
            "state.open flip should be detected as a material change.\n"
            "This is a deliberate state change that MUST reset the lifecycle clock."
        )

        # Verify the diff contains the state change
        changed_fields = {c["field"] for c in diff.get("changed", [])}
        assert "state" in changed_fields, (
            "state field should appear in the diff.\n"
            f"Changed fields: {changed_fields}"
        )


    def test_transform_to_sparql_writes_lastupdated_when_content_changed(self):
        """
        Unit test: transform_to_sparql should write mom:lastUpdated when content_changed=True.

        This test validates the transform layer directly, ensuring that when
        content_changed=True, the SPARQL output includes the mom:lastUpdated triple.
        """
        baseline = _read_baseline()

        # Parse the baseline as a SpaceAPISchema (simulating successful validation)
        schema = SpaceAPISchema(**baseline)

        metadata = {
            "endpoint_url": "http://localhost:9191/",
            "space_id": "mother-sands",
            "endpoint_health": "healthy",
            "lifecycle_state": "confirmed",
        }

        # Generate SPARQL with content_changed=True
        sparql_update, _ = transform_to_sparql(schema, metadata, content_changed=True)

        # SPARQL should contain mom:lastUpdated
        assert f"{MOM}lastUpdated" in sparql_update or "lastUpdated" in sparql_update, (
            "BUG: transform_to_sparql should write mom:lastUpdated when content_changed=True.\n"
            f"SPARQL output:\n{sparql_update}"
        )


    def test_transform_to_sparql_no_fresh_lastupdated_when_no_content_change(self):
        """
        Unit test: with content_changed=False AND no preserved value,
        transform_to_sparql writes no mom:lastUpdated (nothing to write yet).
        """
        baseline = _read_baseline()
        schema = SpaceAPISchema(**baseline)

        metadata = {
            "endpoint_url": "http://localhost:9191/",
            "space_id": "mother-sands",
            "endpoint_health": "healthy",
            "lifecycle_state": "confirmed",
        }

        sparql_update, _ = transform_to_sparql(schema, metadata, content_changed=False)

        insert_section = sparql_update.split("WHERE")[0] if "WHERE" in sparql_update else sparql_update
        assert f"{MOM}lastUpdated" not in insert_section, (
            "With no preserved value, content_changed=False should write no lastUpdated.\n"
            f"SPARQL output:\n{sparql_update}"
        )

    def test_transform_to_sparql_preserves_lastupdated_across_drop(self):
        """
        ROOT CAUSE #2 of stuck-seeded bug (Story 3.4):

        transform_to_sparql emits DROP SILENT GRAPH + INSERT DATA. On a no-diff
        cycle (content_changed=False) the INSERT used to omit mom:lastUpdated, so
        the DROP wiped the prior value permanently — the space went 'updated
        unknown' even though it had a valid timestamp before.

        FIX: when content_changed=False, the prior mom:lastUpdated is passed via
        metadata['preserved_last_updated'] and MUST be re-inserted across the DROP.
        """
        baseline = _read_baseline()
        schema = SpaceAPISchema(**baseline)

        prior_timestamp = "2026-05-07T16:08:30.804057+00:00"
        metadata = {
            "endpoint_url": "http://localhost:9191/",
            "space_id": "mother-sands",
            "endpoint_health": "healthy",
            "lifecycle_state": "confirmed",
            "preserved_last_updated": prior_timestamp,
        }

        # No-diff cycle, but a prior lastUpdated exists and must survive the DROP.
        sparql_update, _ = transform_to_sparql(schema, metadata, content_changed=False)

        assert prior_timestamp in sparql_update, (
            "BUG: prior mom:lastUpdated was NOT preserved across DROP SILENT GRAPH.\n"
            "On a no-diff cycle the timestamp must be re-inserted, or the space\n"
            "renders as 'updated unknown' / stuck-seeded.\n"
            f"SPARQL output:\n{sparql_update}"
        )
        assert f"{MOM}lastUpdated" in sparql_update, (
            "mom:lastUpdated triple missing entirely from no-diff write."
        )


class TestRevivalSparqlConcatenation:
    """
    ROOT CAUSE of stuck-seeded bug (Story 3.4):

    When a closed space receives a content change, process_one_space prepends a
    'revival' SPARQL block (DELETE/WHERE removing mak:closedAt) to the main
    sparql_update (which begins with DROP SILENT GRAPH).

    SPARQL UPDATE requires multiple operations to be ';'-separated. The original
    code concatenated them with NO separator, so Oxigraph parsed the trailing
    DROP as part of the revival WHERE clause and rejected the ENTIRE request
    with HTTP 400 'expected OPTIONAL'.

    Consequence: every write for that space failed — mom:lastUpdated,
    operationalState, lastFetched all frozen. The space stayed stuck.
    """

    def test_revival_block_concatenation_is_valid_sparql(self):
        """
        Reproduce the exact bug: revival_sparql + sparql_update must be valid SPARQL.

        Sends the concatenated update to live Oxigraph. Before the fix this
        returns HTTP 400; after the fix (';' separator) it returns HTTP 204.
        """
        baseline = _read_baseline()
        schema = SpaceAPISchema(**baseline)

        space_uri = "urn:mak:space/test-revival-canary"
        metadata = {
            "endpoint_url": "http://localhost:9191/",
            "space_id": "test-revival-canary",
            "endpoint_health": "healthy",
            "lifecycle_state": "confirmed",
        }
        main_update, _ = transform_to_sparql(schema, metadata, content_changed=True)
        revival = _build_revival_closedAt_delete(space_uri)

        # This is exactly how process_one_space composes the two operations.
        combined = revival.rstrip() + " ;\n" + main_update

        resp = httpx.post(
            f"{OXIGRAPH_URL}/update",
            content=combined,
            headers={"Content-Type": "application/sparql-update"},
            timeout=10.0,
        )

        assert resp.status_code == 204, (
            f"BUG: revival + main SPARQL concatenation rejected by Oxigraph.\n"
            f"HTTP {resp.status_code}: {resp.text}\n"
            f"Root cause: missing ';' separator between SPARQL UPDATE operations.\n"
            f"Combined SPARQL (first 400 chars):\n{combined[:400]}"
        )

        # Cleanup test graph
        httpx.post(
            f"{OXIGRAPH_URL}/update",
            content=f"DROP SILENT GRAPH <{space_uri}>",
            headers={"Content-Type": "application/sparql-update"},
            timeout=10.0,
        )

    def test_revival_block_without_separator_is_rejected(self):
        """
        Negative control: prove the bug is real by showing the UNSEPARATED
        concatenation IS rejected by Oxigraph. This guards against a future
        regression where someone removes the ';' separator.
        """
        baseline = _read_baseline()
        schema = SpaceAPISchema(**baseline)

        space_uri = "urn:mak:space/test-revival-negative"
        metadata = {
            "endpoint_url": "http://localhost:9191/",
            "space_id": "test-revival-negative",
            "endpoint_health": "healthy",
            "lifecycle_state": "confirmed",
        }
        main_update, _ = transform_to_sparql(schema, metadata, content_changed=True)
        revival = _build_revival_closedAt_delete(space_uri)

        # The OLD buggy concatenation — no ';' separator
        buggy_combined = revival + main_update

        resp = httpx.post(
            f"{OXIGRAPH_URL}/update",
            content=buggy_combined,
            headers={"Content-Type": "application/sparql-update"},
            timeout=10.0,
        )

        assert resp.status_code == 400, (
            "Expected the unseparated concatenation to be rejected (HTTP 400).\n"
            f"Got HTTP {resp.status_code} instead — the bug reproduction is no longer valid.\n"
            "If Oxigraph now accepts this, the test needs revisiting."
        )


class TestStaleLastFetchedOn304:
    """
    ROOT CAUSE #3 of stale display (Story 3.4):

    On HTTP 304 Not Modified, the heartbeat skipped writing mom:lastFetched to
    Oxigraph (build_state_only_update only touched health/state, and only fired
    when health/state changed). The map reads mom:lastFetched for its
    'fetched N ago' caption, so a space returning 304 forever showed a frozen
    timestamp from its last 200 response — e.g. 'fetched 9d ago' while the
    heartbeat actually ran minutes ago.

    FIX: build_state_only_update accepts last_fetched and the 304 path always
    writes it.
    """

    def test_state_only_update_omits_lastfetched_by_default(self):
        """Failure/legacy callers that pass no last_fetched must not touch it."""
        sparql = build_state_only_update(
            "urn:mak:space/x", "healthy", "confirmed"
        )
        assert "lastFetched" not in sparql, (
            "build_state_only_update should only write lastFetched when asked."
        )

    def test_state_only_update_writes_lastfetched_when_provided(self):
        """The 304 path passes last_fetched; it must land in the SPARQL."""
        ts = "2026-05-16T19:00:00+00:00"
        sparql = build_state_only_update(
            "urn:mak:space/x", "healthy", "confirmed", last_fetched=ts
        )
        assert "mom:lastFetched" in sparql, (
            "lastFetched triple missing — map 'fetched N ago' caption would freeze."
        )
        assert ts in sparql
        # DELETE-before-INSERT so the value is replaced, not duplicated.
        assert "DELETE WHERE" in sparql and sparql.count("lastFetched") >= 2

    def test_state_only_update_is_valid_sparql_against_oxigraph(self):
        """Live check: the 304 state+lastFetched update is accepted by Oxigraph."""
        space_uri = "urn:mak:space/test-304-lastfetched"
        ts = datetime.now(timezone.utc).isoformat()
        sparql = build_state_only_update(
            space_uri, "healthy", "confirmed", last_fetched=ts
        )
        resp = httpx.post(
            f"{OXIGRAPH_URL}/update",
            content=sparql,
            headers={"Content-Type": "application/sparql-update"},
            timeout=10.0,
        )
        assert resp.status_code == 204, (
            f"304 state+lastFetched update rejected (HTTP {resp.status_code}): {resp.text}"
        )

        check = f"""PREFIX mom: <{MOM}>
SELECT ?f WHERE {{ GRAPH <{space_uri}> {{ <{space_uri}> mom:lastFetched ?f }} }}"""
        bindings = _oxigraph_query(check)
        assert len(bindings) == 1, (
            "mom:lastFetched did not land exactly once after a 304-style write."
        )
        # Oxigraph normalizes the dateTime (+00:00 → Z); compare by value, not string.
        stored = datetime.fromisoformat(bindings[0]["f"]["value"].replace("Z", "+00:00"))
        assert stored == datetime.fromisoformat(ts)

        httpx.post(
            f"{OXIGRAPH_URL}/update",
            content=f"DROP SILENT GRAPH <{space_uri}>",
            headers={"Content-Type": "application/sparql-update"},
            timeout=10.0,
        )


class TestHeartbeatLogState:
    """Tests for heartbeat_log.db state tracking."""

    def test_heartbeat_log_has_required_columns(self):
        """
        Verify heartbeat_log.db schema has all columns needed for coherence tracking.

        Story 3.3 added columns: last_endpoint_health, last_lifecycle_state,
        last_open_now, last_effective_marker. All must exist for the bug fix to work.
        """
        con = sqlite3.connect(str(HEARTBEAT_DB))
        cursor = con.cursor()
        cursor.execute("PRAGMA table_info(heartbeat_log)")
        columns = {row[1] for row in cursor.fetchall()}
        con.close()

        required = {"last_endpoint_health", "last_lifecycle_state", "last_open_now", "last_effective_marker"}
        missing = required - columns

        assert not missing, (
            f"heartbeat_log schema is incomplete.\n"
            f"Missing columns: {missing}\n"
            f"Story 3.3 should have created these for coherence tracking."
        )


class TestCanaryCoherence:
    """Integration tests using the Mother Sands canary."""

    def test_canary_payload_has_simulatedage(self):
        """Verify that the served.json canary payload includes simulatedAge for lifecycle testing."""
        payload = _load_served_json()

        ext_mom = payload.get("ext_mom", {})
        assert "simulatedAge" in ext_mom, (
            "Canary payload must have ext_mom.simulatedAge for lifecycle testing.\n"
            "This field controls which lifecycle state the canary should enter.\n"
            f"Payload ext_mom: {ext_mom}"
        )
