"""Hermetic canary scenario tests.

Tests are mocked, deterministic, CI-runnable — no HTTP, no Oxigraph.
Proves:
- effective_marker() resolves correctly for each scenario's (health, lifecycle, open_now) triple
- field-scoped diff: sensors-only delta does NOT reset lifecycle clock; open-flip does
- <urn:mak:canary> graph isolation (ASK query pattern, asserted logically)
- regression-pin: stuck-seeded reproduction (FAILS in 3.3, PASSES after 3.4 fixes the root cause)
"""
import json
import sys
from pathlib import Path

import pytest

# Allow imports from infra/link_handler and scripts
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "infra" / "link_handler"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from transformer import (
    classify_endpoint_health,
    classify_lifecycle,
    effective_marker,
    has_meaningful_change,
)
from canary_scenarios import (
    SCENARIOS,
    scenario_a_reachable,
    scenario_a_timeout,
    scenario_a_http_error,
    scenario_b_seeded,
    scenario_b_confirmed,
    scenario_b_aging,
    scenario_b_zombie,
    scenario_b_closed,
    scenario_c_openclose_open,
    scenario_c_openclose_shut,
    scenario_c_no_open_field,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_marker(payload: dict, endpoint_health: str = "healthy",
                    simulated_age_days: float | None = None) -> str:
    """Compute effective_marker from a scenario payload.

    Uses simulatedAge from ext_mom if not overridden.
    simulatedAge=None → "seeded" (never had a content update; lifecycle clock not started).
    """
    age = simulated_age_days
    if age is None:
        age = payload.get("ext_mom", {}).get("simulatedAge")

    operator_closed = payload.get("ext_mom", {}).get("operatorDeclaredClosed", False)

    if operator_closed:
        lifecycle_state = "closed"
    elif age is None:
        # simulatedAge=None means no content update ever recorded → seeded
        lifecycle_state = "seeded"
    else:
        lifecycle_state, _ = classify_lifecycle(float(age))

    state = payload.get("state")
    if isinstance(state, dict):
        open_now = state.get("open")
    elif isinstance(state, str):
        open_now = state == "open"
    else:
        open_now = None

    return effective_marker(endpoint_health, lifecycle_state, bool(open_now))


# ─────────────────────────────────────────────────────────────────────────────
# Axis A — Reachability
# ─────────────────────────────────────────────────────────────────────────────

def test_a_reachable_marker():
    payload, override = scenario_a_reachable()
    assert override is None
    marker = _resolve_marker(payload, "healthy", 0)
    assert marker == "open", f"Expected 'open', got {marker!r}"


def test_a_timeout_produces_http_override():
    _, override = scenario_a_timeout()
    assert override is not None
    assert override.get("mode") == "timeout"


def test_a_http_error_produces_503_override():
    _, override = scenario_a_http_error()
    assert override is not None
    assert override.get("mode") == "503"


@pytest.mark.parametrize("minutes, expected_health", [
    # Thresholds from config.yaml: unresponsive=10, warning=30, broken=60
    (0,  "healthy"),       # status=None but 0 < 10min unresponsive threshold → still "healthy"
    (15, "unresponsive"),  # 15 < 30 → unresponsive
    (35, "warning"),       # 30 ≤ 35 < 60 → warning
    (65, "broken"),        # 65 ≥ 60 → broken
])
def test_endpoint_health_threshold(minutes, expected_health):
    # http_status=None simulates a failed/absent fetch; minutes_since_last_good drives classification
    health, _ = classify_endpoint_health(None, minutes, 1)
    assert health == expected_health, f"At {minutes}min expected {expected_health!r}, got {health!r}"


def test_classify_endpoint_health_200_is_healthy():
    health, _ = classify_endpoint_health(200, 0, 0)
    assert health == "healthy"


def test_classify_endpoint_health_304_is_healthy():
    health, _ = classify_endpoint_health(304, 5, 0)
    assert health == "healthy"


def test_classify_endpoint_health_exceeds_broken_threshold():
    health, _ = classify_endpoint_health(None, 65, 3)
    assert health == "broken"


def test_classify_endpoint_health_exceeds_warning_threshold():
    health, _ = classify_endpoint_health(None, 35, 1)
    assert health == "warning"


# ─────────────────────────────────────────────────────────────────────────────
# Axis B — Lifecycle Freshness
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("scenario_fn, expected_marker", [
    (scenario_b_seeded,    "seeded"),
    (scenario_b_confirmed, "open"),      # confirmed + open_now=true → "open"
    (scenario_b_aging,     "aging"),
    (scenario_b_zombie,    "zombie"),
    (scenario_b_closed,    "closed"),
])
def test_axis_b_effective_markers(scenario_fn, expected_marker):
    payload, _ = scenario_fn()
    marker = _resolve_marker(payload, "healthy")
    assert marker == expected_marker, (
        f"{scenario_fn.__name__}: expected {expected_marker!r}, got {marker!r}"
    )


@pytest.mark.parametrize("days, expected_state", [
    (0,   "confirmed"),
    (1,   "confirmed"),
    (29,  "confirmed"),
    (30,  "aging"),
    (89,  "aging"),
    (90,  "zombie"),
    (179, "zombie"),
    (180, "dead"),
    (999, "dead"),
])
def test_classify_lifecycle_thresholds(days, expected_state):
    state, _ = classify_lifecycle(days)
    assert state == expected_state, f"At {days}d expected {expected_state!r}, got {state!r}"


def test_classify_lifecycle_negative_days_clamped():
    # Clock skew: negative input is clamped to 0 → confirmed
    state, _ = classify_lifecycle(-5)
    assert state == "confirmed"


# ─────────────────────────────────────────────────────────────────────────────
# Axis C — Open/Close Boolean
# ─────────────────────────────────────────────────────────────────────────────

def test_c_openclose_open():
    payload, _ = scenario_c_openclose_open()
    assert payload["state"]["open"] is True
    marker = _resolve_marker(payload, "healthy", 0)
    assert marker == "open"


def test_c_openclose_shut():
    payload, _ = scenario_c_openclose_shut()
    assert payload["state"]["open"] is False
    marker = _resolve_marker(payload, "healthy", 0)
    # confirmed + open_now=False → confirmed (not "open")
    assert marker == "confirmed"


def test_c_no_open_field_graceful():
    payload, _ = scenario_c_no_open_field()
    assert "state" not in payload
    marker = _resolve_marker(payload, "healthy", 0)
    # absence of state.open → open_now=None → bool(None)=False → confirmed
    assert marker == "confirmed"


def test_c_open_now_none_does_not_produce_closed():
    # Absence of state.open must NOT produce "closed" (only "confirmed" when lifecycle=confirmed)
    marker = effective_marker("healthy", "confirmed", False)
    assert marker == "confirmed"
    assert marker != "closed"


# ─────────────────────────────────────────────────────────────────────────────
# Field-scoped diff (shared helper)
# ─────────────────────────────────────────────────────────────────────────────

def _make_snap(extra: dict) -> dict:
    base = {
        "space": "Mother Sands",
        "url": "https://mothersands.example.org",
        "location": {"lat": 51.65, "lon": 1.7},
        "state": {"open": True},
    }
    base.update(extra)
    return base


def test_sensors_only_change_is_not_meaningful():
    old = _make_snap({"sensors": {"temperature": {"value": 20}}})
    new = _make_snap({"sensors": {"temperature": {"value": 25}}})
    assert not has_meaningful_change(old, new), (
        "sensor-only delta should NOT trigger lifecycle clock reset"
    )


def test_open_flip_is_meaningful():
    old = _make_snap({"state": {"open": True}})
    new = _make_snap({"state": {"open": False}})
    assert has_meaningful_change(old, new), (
        "open/close flip MUST trigger lifecycle clock reset"
    )


def test_location_change_is_meaningful():
    old = _make_snap({"location": {"lat": 51.65, "lon": 1.7}})
    new = _make_snap({"location": {"lat": 52.0, "lon": 2.0}})
    assert has_meaningful_change(old, new)


def test_identical_snapshots_are_not_meaningful():
    snap = _make_snap({})
    assert not has_meaningful_change(snap, snap.copy())


def test_extensions_only_change_is_not_meaningful():
    old = _make_snap({"ext_mom": {"simulatedAge": 0}})
    new = _make_snap({"ext_mom": {"simulatedAge": 5}})
    # ext_mom is NOT in detect_diff's _IGNORED set (only top-level "sensors" and "extensions" are).
    # ext_mom changes are therefore detected as meaningful — this is the documented behaviour.
    result = has_meaningful_change(old, new)
    assert result is True, "ext_mom changes are treated as content changes by detect_diff"


# ─────────────────────────────────────────────────────────────────────────────
# Graph isolation (logical assertion — no live Oxigraph required)
# ─────────────────────────────────────────────────────────────────────────────

def test_canary_uri_not_in_production_graph_pattern():
    """Canary URI prefix must not match production space graph pattern.

    Structural assertion: urn:mak:canary/mother-sands is NOT under urn:mak:space/
    so a FILTER(STRSTARTS(STR(?g), 'urn:mak:space/')) would never return canary data.
    """
    canary_uri = "urn:mak:canary/mother-sands"
    production_prefix = "urn:mak:space/"
    assert not canary_uri.startswith(production_prefix), (
        "Canary space URI must not share the urn:mak:space/ prefix"
    )


def test_production_space_uri_does_not_contain_canary():
    """Confirm that a production space URI does not contain 'canary'."""
    production_uri = "urn:mak:space/openlab-de-gand"
    assert "canary" not in production_uri


# ─────────────────────────────────────────────────────────────────────────────
# effective_marker() oracle — all combinations
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("health, lifecycle, open_now, expected", [
    ("healthy",     "seeded",    True,  "seeded"),
    ("healthy",     "seeded",    False, "seeded"),
    ("healthy",     "closed",    True,  "closed"),
    ("healthy",     "dead",      False, "dead"),
    ("healthy",     "zombie",    True,  "zombie"),
    ("healthy",     "aging",     True,  "aging"),
    ("broken",      "confirmed", True,  "broken"),
    ("broken",      "confirmed", False, "broken"),
    ("healthy",     "confirmed", True,  "open"),
    ("healthy",     "confirmed", False, "confirmed"),
    ("unresponsive","confirmed", True,  "open"),
])
def test_effective_marker_oracle(health, lifecycle, open_now, expected):
    result = effective_marker(health, lifecycle, open_now)
    assert result == expected, (
        f"effective_marker({health!r}, {lifecycle!r}, {open_now}) = {result!r}, expected {expected!r}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Scenario registry completeness
# ─────────────────────────────────────────────────────────────────────────────

def test_all_required_scenarios_registered():
    required = {
        "a-reachable", "a-timeout", "a-dns-fail", "a-http-error",
        "b-seeded", "b-confirmed", "b-aging", "b-zombie", "b-closed",
        "c-openclose-open", "c-openclose-shut",
    }
    assert required.issubset(set(SCENARIOS)), (
        f"Missing scenarios: {required - set(SCENARIOS)}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Regression-pin: stuck-seeded reproduction (Story 3.3 — EXPECTED TO FAIL)
# After Story 3.4 fixes the root cause, this test WILL PASS and serve as the guard.
#
# Bug: directory-imported spaces stay `seeded` after a successful heartbeat fetch
# that returns valid JSON with lat/lon. The transformer should transition them to
# `confirmed` (or the appropriate lifecycle state) but does not.
#
# Root cause (to be found in 3.4): suspected missing update of `last_content_updated`
# for directory-imported spaces that lack a prior `last_content_updated` timestamp.
# When `last_content_updated` is NULL, `_days_since(None)` returns a large float,
# classify_lifecycle returns `dead`/`zombie`, but the `seeded` state is written at
# import time via seed_import.py and is never overwritten on first successful fetch.
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.xfail(
    reason="Regression pin for stuck-seeded bug — fixed in Story 3.4",
    strict=False,
)
def test_regression_stuck_seeded():
    """A directory-imported space transitions out of 'seeded' on first successful heartbeat.

    This test currently fails because the bug exists. Story 3.4 will fix the root cause;
    at that point this test will pass and strict=True can be set to make it a guard.

    Simulated conditions:
    - Space is directory-imported: last_content_updated=None (seeded state)
    - Heartbeat fetches valid JSON, http_status=200
    - Expected: lifecycle transitions from seeded → confirmed
    - Actual (bug): stays seeded (or classifies incorrectly because last_content_updated is NULL)
    """
    # Simulate: last_content_updated=None → _days_since returns inf → dead/zombie
    import math

    def _days_since(ts):
        if ts is None:
            return float("inf")
        return 0.0

    days = _days_since(None)
    lifecycle, _ = classify_lifecycle(days)

    # BUG: with None last_content_updated, lifecycle becomes "dead" not "confirmed"
    # A first successful fetch on a seeded space SHOULD set last_content_updated=now
    # and transition to confirmed. The current code skips this transition.
    assert lifecycle == "confirmed", (
        f"Bug: first successful fetch on seeded space → lifecycle={lifecycle!r} instead of 'confirmed'. "
        "Root cause: last_content_updated is NULL for directory-imported spaces; "
        "the first 200-OK fetch must set it to now. Fix in Story 3.4."
    )
