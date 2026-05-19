"""Regression tests for Story 3.4: stuck-seeded bug; updated Story 3.8.

This test suite reproduces the stuck-seeded bug where spaces fetch successfully
but their freshness token is never written to Oxigraph, causing them to remain
stuck in seeded state instead of transitioning to confirmed.

Story 3.8: mom:lastUpdated replaced by mom:observedAt (snapshot-minted token).
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
    """Test suite for stuck-seeded bug: freshness token not written on fetch."""

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

        # Verify mom:observedAt landed — Story 3.8 replaces mom:lastUpdated with
        # the snapshot-minted observed_at token as the freshness proof.
        T = "2026-05-19T10:00:00Z"
        check = f"""PREFIX mom: <{MOM}>
SELECT ?observedAt WHERE {{
  GRAPH <{space_uri}> {{ <{space_uri}> mom:observedAt ?observedAt }}
}}"""
        # Re-run the write with an observed_at to confirm the triple lands.
        main_update2, _ = transform_to_sparql(schema, metadata, content_changed=True,
                                              observed_at=T)
        combined2 = revival.rstrip() + " ;\n" + main_update2
        httpx.post(
            f"{OXIGRAPH_URL}/update",
            content=combined2,
            headers={"Content-Type": "application/sparql-update"},
            timeout=10.0,
        )
        bindings = _oxigraph_query(check)
        assert len(bindings) > 0, (
            "mom:observedAt is absent after a successful revival write.\n"
            "The space would have no freshness token — equivalent to old stuck-seeded bug."
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


    def test_transform_to_sparql_writes_observedat_when_provided(self):
        """
        Unit test: transform_to_sparql writes mom:observedAt when observed_at is supplied.

        Story 3.8: observed_at replaces mom:lastUpdated as the freshness token.
        The token is minted once at fetch time and carried byte-identical into Oxigraph.
        """
        baseline = _read_baseline()
        schema = SpaceAPISchema(**baseline)

        T = "2026-05-19T10:00:00Z"
        metadata = {
            "endpoint_url": "http://localhost:9191/",
            "space_id": "mother-sands",
            "endpoint_health": "healthy",
            "lifecycle_state": "confirmed",
        }

        sparql_update, _ = transform_to_sparql(schema, metadata, content_changed=True,
                                               observed_at=T)

        assert f"{MOM}observedAt" in sparql_update or "observedAt" in sparql_update, (
            "BUG: transform_to_sparql should write mom:observedAt when observed_at is provided.\n"
            f"SPARQL output:\n{sparql_update}"
        )
        assert T in sparql_update, (
            "observed_at value must appear byte-identical in the SPARQL output."
        )


    def test_transform_to_sparql_no_observedat_when_not_provided(self):
        """
        Unit test: transform_to_sparql writes no mom:observedAt when observed_at is absent.

        Story 3.8: the freshness token is optional — callers that don't yet have
        a snapshot (e.g. legacy fallback paths) produce a graph without observedAt.
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

        assert f"{MOM}observedAt" not in sparql_update and "observedAt" not in sparql_update, (
            "Without observed_at, transform_to_sparql should write no mom:observedAt.\n"
            f"SPARQL output:\n{sparql_update}"
        )

    def test_transform_to_sparql_carries_observedat_across_drop(self):
        """
        Story 3.8 analog of the ROOT CAUSE #2 fix:

        transform_to_sparql emits DROP SILENT GRAPH + INSERT DATA. The freshness
        token (observed_at) must be carried into the INSERT — otherwise the DROP
        wipes it permanently. Story 3.8 fixes this structurally: the caller always
        passes observed_at (from snapshot store) so it is always re-inserted.
        """
        baseline = _read_baseline()
        schema = SpaceAPISchema(**baseline)

        T = "2026-05-19T10:00:00Z"
        metadata = {
            "endpoint_url": "http://localhost:9191/",
            "space_id": "mother-sands",
            "endpoint_health": "healthy",
            "lifecycle_state": "confirmed",
        }

        sparql_update, _ = transform_to_sparql(schema, metadata, content_changed=False,
                                               observed_at=T)

        assert T in sparql_update, (
            "BUG: observed_at was NOT carried across DROP SILENT GRAPH.\n"
            "The freshness token must be re-inserted on every write.\n"
            f"SPARQL output:\n{sparql_update}"
        )
        assert f"{MOM}observedAt" in sparql_update, (
            "mom:observedAt triple missing entirely from no-diff write."
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


class TestStaleObservedAtOn304:
    """
    Story 3.8 replacement for TestStaleLastFetchedOn304:

    On HTTP 304 Not Modified, build_state_only_update now propagates the
    snapshot store's observed_at value to Oxigraph (instead of re-stamping
    mom:lastFetched with datetime.now()). The advanced token keeps Oxigraph
    in sync with the snapshot store across all three HTTP outcomes.
    """

    def test_state_only_update_omits_observedat_by_default(self):
        """Error path callers pass no observed_at — observedAt must not be touched."""
        sparql = build_state_only_update(
            "urn:mak:space/x", "healthy", "confirmed"
        )
        assert "observedAt" not in sparql, (
            "build_state_only_update should only write observedAt when provided."
        )

    def test_state_only_update_writes_observedat_when_provided(self):
        """The 304 path passes observed_at; it must land byte-identical in the SPARQL."""
        T = "2026-05-19T10:00:00Z"
        sparql = build_state_only_update(
            "urn:mak:space/x", "healthy", "confirmed", observed_at=T
        )
        assert "mom:observedAt" in sparql, (
            "observedAt triple missing — freshness token would not reach Oxigraph."
        )
        assert T in sparql, "observed_at must appear byte-identical."
        # DELETE-before-INSERT so the value is replaced, not duplicated.
        assert "DELETE WHERE" in sparql and sparql.count("observedAt") >= 2

    def test_state_only_update_is_valid_sparql_against_oxigraph(self):
        """Live check: the 304 state+observedAt update is accepted by Oxigraph."""
        space_uri = "urn:mak:space/test-304-observedat"
        T = "2026-05-19T10:00:00Z"
        sparql = build_state_only_update(
            space_uri, "healthy", "confirmed", observed_at=T
        )
        resp = httpx.post(
            f"{OXIGRAPH_URL}/update",
            content=sparql,
            headers={"Content-Type": "application/sparql-update"},
            timeout=10.0,
        )
        assert resp.status_code == 204, (
            f"304 state+observedAt update rejected (HTTP {resp.status_code}): {resp.text}"
        )

        check = f"""PREFIX mom: <{MOM}>
SELECT ?t WHERE {{ GRAPH <{space_uri}> {{ <{space_uri}> mom:observedAt ?t }} }}"""
        bindings = _oxigraph_query(check)
        assert len(bindings) == 1, (
            "mom:observedAt did not land exactly once after a 304-style write."
        )
        # observedAt is stored as xsd:string (byte-identical, no Oxigraph normalization).
        assert bindings[0]["t"]["value"] == T, (
            f"Stored value {bindings[0]['t']['value']!r} != minted {T!r}"
        )

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
        Verify heartbeat_log.db schema has the columns needed for coherence tracking.

        Story 3.3 original columns: last_endpoint_health, last_lifecycle_state,
        last_open_now, last_effective_marker.

        Story 3.7 dropped last_endpoint_health and last_lifecycle_state (timing data
        moved to snapshot_store). Remaining columns: last_open_now, last_effective_marker.
        """
        con = sqlite3.connect(str(HEARTBEAT_DB))
        cursor = con.cursor()
        cursor.execute("PRAGMA table_info(heartbeat_log)")
        columns = {row[1] for row in cursor.fetchall()}
        con.close()

        # Story 3.7 schema: timing columns removed, open/marker columns kept.
        required = {"last_open_now", "last_effective_marker"}
        missing = required - columns

        assert not missing, (
            f"heartbeat_log schema is incomplete.\n"
            f"Missing columns: {missing}\n"
            f"Story 3.7 schema: last_open_now and last_effective_marker must remain."
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
