"""Gating test for Story 3.7 — three-outcome fetch seam with temporal assertions.

Tests that fetch_space_snapshot enforces the observed_at rules:
  - HTTP 200 → fetch_status=ok, observed_at fresh mint, full payload
  - HTTP 304 → fetch_status=not_modified, observed_at advances, payload from prior
  - HTTP error → fetch_status=unreachable, observed_at frozen, prior snapshot untouched
"""
import time

import pytest
from pytest_httpserver import HTTPServer

from space_pipeline import fetch_space_snapshot
from snapshot_store import init_snapshot_db, read_snapshot


@pytest.fixture
def snapshot_db(tmp_path):
    db = str(tmp_path / "snap.db")
    init_snapshot_db(db)
    return db


@pytest.mark.asyncio
async def test_heartbeat_two_cycle_temporal(httpserver: HTTPServer, snapshot_db):
    uid = "test-space"
    payload = {"space": "Test", "api": "0.13"}

    # Cycle 1: 200 → fresh snapshot with new observed_at
    httpserver.expect_ordered_request("/space.json").respond_with_json(
        payload, status=200, headers={"ETag": '"abc"'}
    )
    r1 = await fetch_space_snapshot(uid, httpserver.url_for("/space.json"), db_path=snapshot_db)
    assert r1["fetch_status"] == "ok"
    snap1 = read_snapshot(uid, db_path=snapshot_db)
    assert snap1 is not None
    assert snap1["payload"] == payload
    T1 = snap1["observed_at"]

    time.sleep(0.01)  # ensure T2 > T1

    # Cycle 2: 304 → payload unchanged, observed_at advances
    httpserver.expect_ordered_request("/space.json").respond_with_data("", status=304)
    r2 = await fetch_space_snapshot(uid, httpserver.url_for("/space.json"), db_path=snapshot_db)
    assert r2["fetch_status"] == "not_modified"
    snap2 = read_snapshot(uid, db_path=snapshot_db)
    assert snap2 is not None
    T2 = snap2["observed_at"]
    assert T2 > T1, f"observed_at must advance on 304: {T1} not < {T2}"
    assert snap2["payload"] == payload, "payload must be preserved on 304"

    time.sleep(0.01)

    # Cycle 3: 503 → fetch_status=unreachable, observed_at frozen at T2
    httpserver.expect_ordered_request("/space.json").respond_with_data("", status=503)
    r3 = await fetch_space_snapshot(uid, httpserver.url_for("/space.json"), db_path=snapshot_db)
    assert r3["fetch_status"] == "unreachable"
    snap3 = read_snapshot(uid, db_path=snapshot_db)
    assert snap3 is not None
    assert snap3["observed_at"] == T2, f"observed_at must freeze on error: {snap3['observed_at']} != {T2}"
    assert snap3["payload"] == payload, "payload must be preserved on error"
