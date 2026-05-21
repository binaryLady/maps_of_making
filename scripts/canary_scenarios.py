"""Mother Sands canary scenario library.

Each function returns (payload: dict, http_override: dict | None).
  - payload: the JSON to write to data/canary/served.json
  - http_override: {"mode": "ok|timeout|404|503"} or None (means ok)

Docstring contract for every scenario:
  INJECT  — what is injected into the payload / HTTP layer
  STATE   — expected (endpoint_health, lifecycle_state, openNow) triple
  EXPECT MARKER — expected effective_marker() output
  EXPECT CARD   — what the rendered drawer should show

Field-scoped diff (shared helper): import has_meaningful_change from transformer.
The function lives in infra/link_handler/transformer.py to keep one definition.
"""
import copy
import json
import os
from pathlib import Path

BASELINE_FILE = Path(__file__).parent.parent / "data" / "canary" / "baseline.json"


def _baseline() -> dict:
    return json.loads(BASELINE_FILE.read_text())


def _stamp_scenario(payload: dict, name: str) -> None:
    """Stamp scenario identity + apply-time into ext_mom so two runs produce
    different bytes. Without this, the heartbeat 304-path short-circuits and
    `detect_diff` never runs → `mom:updatedAt` never advances. The stamp lives
    under ext_mom (not ignored by detect_diff) and is the canary-side equivalent
    of a real operator content change.
    """
    from datetime import datetime, timezone
    payload.setdefault("ext_mom", {})
    payload["ext_mom"]["scenarioName"] = name
    payload["ext_mom"]["scenarioAppliedAt"] = datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# Axis A — Reachability
# ─────────────────────────────────────────────────────────────────────────────

def scenario_a_reachable() -> tuple[dict, dict | None]:
    """Axis A: healthy endpoint.

    INJECT  endpoint serves 200 OK with valid JSON (baseline)
    STATE   (healthy, confirmed, open)
    EXPECT MARKER  open
    EXPECT CARD    open pill; "fetched X ago" recency shown
    """
    return _baseline(), None


def scenario_a_timeout() -> tuple[dict, dict | None]:
    """Axis A: endpoint accepts connection but never replies.

    INJECT  MODE=timeout — server accepts TCP, reads timeout on client
    STATE   (unresponsive→broken depending on minutes elapsed, confirmed, unknown)
    EXPECT MARKER  broken (once minutes_since_last_good exceeds threshold)
    EXPECT CARD    "Endpoint issue" pill; fetch timestamp stale
    """
    return _baseline(), {"mode": "timeout"}


def scenario_a_dns_fail() -> tuple[dict, dict | None]:
    """Axis A: DNS resolution fails (endpoint URL points to unresolvable host).

    INJECT  endpoint URL changed to http://unresolvable.invalid — causes ConnectError
    STATE   (broken, confirmed, unknown)
    EXPECT MARKER  broken
    EXPECT CARD    "Endpoint issue" pill
    """
    payload = _baseline()
    # URL is used as identity only; the actual served URL is configured in heartbeat.
    # In the live poke loop the Makefile points the heartbeat at an unresolvable URL.
    return payload, None  # DNS failure is network-level; MODE env does not apply


def scenario_a_http_error() -> tuple[dict, dict | None]:
    """Axis A: endpoint returns 503 Service Unavailable.

    INJECT  MODE=503 — endpoint returns HTTP 503
    STATE   (unresponsive, confirmed, unknown)
    EXPECT MARKER  broken (after consecutive failures accumulate past threshold)
    EXPECT CARD    "Endpoint issue" pill
    """
    return _baseline(), {"mode": "503"}


# ─────────────────────────────────────────────────────────────────────────────
# Axis B — Lifecycle Freshness
# ─────────────────────────────────────────────────────────────────────────────

def scenario_b_seeded() -> tuple[dict, dict | None]:
    """Axis B: space has never had a confirmed content update.

    INJECT  simulatedAge=None → lifecycle clock not started → seeded state
    STATE   (healthy, seeded, open)
    EXPECT MARKER  seeded
    EXPECT CARD    seeded badge; no "updated X ago" shown
    """
    payload = _baseline()
    payload["ext_mom"]["simulatedAge"] = None
    return payload, None


def scenario_b_confirmed() -> tuple[dict, dict | None]:
    """Axis B: content updated recently (0 days).

    INJECT  simulatedAge=0 → classify_lifecycle(0) → confirmed
    STATE   (healthy, confirmed, open)
    EXPECT MARKER  open (confirmed + open_now=true → open wins)
    EXPECT CARD    open pill; "updated just now"
    """
    payload = _baseline()
    payload["ext_mom"]["simulatedAge"] = 0
    return payload, None


def scenario_b_aging() -> tuple[dict, dict | None]:
    """Axis B: content not updated for 30–90 days.

    INJECT  simulatedAge=45 → classify_lifecycle(45) → aging
    STATE   (healthy, aging, open)
    EXPECT MARKER  aging
    EXPECT CARD    "Going quiet" pill; "updated 45 days ago"
    """
    payload = _baseline()
    payload["ext_mom"]["simulatedAge"] = 45
    return payload, None


def scenario_b_zombie() -> tuple[dict, dict | None]:
    """Axis B: content not updated for 90–180 days.

    INJECT  simulatedAge=120 → classify_lifecycle(120) → zombie
    STATE   (healthy, zombie, open)
    EXPECT MARKER  zombie
    EXPECT CARD    "Unreachable" pill; "updated 120 days ago"
    """
    payload = _baseline()
    payload["ext_mom"]["simulatedAge"] = 120
    return payload, None


def scenario_b_closed() -> tuple[dict, dict | None]:
    """Axis B: operator-declared retirement (terminal, authoritative).

    INJECT  simulatedAge signals operator-declared closed state
            (in live system: is_closed=1 set in heartbeat_log.db)
    STATE   (healthy, closed, open)
    EXPECT MARKER  closed
    EXPECT CARD    "Permanently closed" — operator declared, not inferred
    """
    payload = _baseline()
    payload["ext_mom"]["simulatedAge"] = 999
    payload["ext_mom"]["operatorDeclaredClosed"] = True
    return payload, None


# ─────────────────────────────────────────────────────────────────────────────
# Axis C — Open / Close Boolean
# Note: false branch is "shut" (not "close") — one-letter guard so find-and-replace
# targeting Axis C cannot accidentally break Axis B lifecycle "closed" naming.
# ─────────────────────────────────────────────────────────────────────────────

def scenario_c_openclose_open() -> tuple[dict, dict | None]:
    """Axis C: space is explicitly open.

    INJECT  state.open = true
    STATE   (healthy, confirmed, True)
    EXPECT MARKER  open
    EXPECT CARD    open pill
    """
    payload = _baseline()
    payload["state"]["open"] = True
    payload["ext_mom"]["simulatedAge"] = 0
    return payload, None


def scenario_c_openclose_shut() -> tuple[dict, dict | None]:
    """Axis C: space is explicitly shut (closed boolean — not lifecycle closed).

    INJECT  state.open = false
    STATE   (healthy, confirmed, False)
    EXPECT MARKER  confirmed  (not open, lifecycle is confirmed)
    EXPECT CARD    no open pill; "Confirmed" status
    Note: "shut" spelling guards against find-and-replace collision with lifecycle "closed".
    """
    payload = _baseline()
    payload["state"]["open"] = False
    payload["ext_mom"]["simulatedAge"] = 0
    return payload, None


def scenario_c_no_open_field() -> tuple[dict, dict | None]:
    """Axis C: state.open field absent → unknown, not false.

    INJECT  state field omitted entirely
    STATE   (healthy, confirmed, None → unknown)
    EXPECT MARKER  confirmed
    EXPECT CARD    no open/closed pill; absence reads as "no live signal"
    """
    payload = _baseline()
    del payload["state"]
    payload["ext_mom"]["simulatedAge"] = 0
    return payload, None


# ─────────────────────────────────────────────────────────────────────────────
# Registry for Makefile / test parametrization
# ─────────────────────────────────────────────────────────────────────────────

SCENARIOS: dict[str, callable] = {
    "a-reachable": scenario_a_reachable,
    "a-timeout": scenario_a_timeout,
    "a-dns-fail": scenario_a_dns_fail,
    "a-http-error": scenario_a_http_error,
    "b-seeded": scenario_b_seeded,
    "b-confirmed": scenario_b_confirmed,
    "b-aging": scenario_b_aging,
    "b-zombie": scenario_b_zombie,
    "b-closed": scenario_b_closed,
    "c-openclose-open": scenario_c_openclose_open,
    "c-openclose-shut": scenario_c_openclose_shut,
    "c-no-open-field": scenario_c_no_open_field,
}

AXIS_A = ["a-reachable", "a-timeout", "a-dns-fail", "a-http-error"]
AXIS_B = ["b-seeded", "b-confirmed", "b-aging", "b-zombie", "b-closed"]
AXIS_C = ["c-openclose-open", "c-openclose-shut", "c-no-open-field"]


def apply_scenario(name: str, served_path: Path, db_path: str | None = None) -> None:
    """Write scenario payload to served_path via safe write protocol.

    Safe write: temp file → fsync → atomic rename → ETag invalidation in heartbeat_log.db.
    """
    import os
    import sqlite3
    import tempfile

    if name not in SCENARIOS:
        raise ValueError(f"Unknown canary scenario: {name!r}. Available: {list(SCENARIOS)}")

    fn = SCENARIOS[name]
    payload, http_override = fn()
    _stamp_scenario(payload, name)

    # Safe write: temp → fsync → atomic rename
    parent = served_path.parent
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", dir=parent, delete=False
    ) as tmp:
        json.dump(payload, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = tmp.name

    os.chmod(tmp_path, 0o644)   # NamedTemporaryFile defaults to 600; nginx needs world-read
    os.rename(tmp_path, served_path)

    # Invalidate ETag/Last-Modified so the next fetch is unconditional.
    # Story 3.10: ETag now lives in snapshot_store.snapshots (the new clean store),
    # not heartbeat_log. We clear both for safety in case the legacy column exists.
    snapshot_db = os.environ.get("SNAPSHOT_DB_PATH") or str(
        Path(__file__).parent.parent / "data" / "tasks" / "snapshot_store.db"
    )
    for target_db, table, key_col, key_match in [
        (snapshot_db, "snapshots", "uid", "mother-sands"),
        (db_path, "heartbeat_log", "space_id", "%mother-sands%"),
    ]:
        if not target_db or not Path(target_db).exists():
            continue
        try:
            con = sqlite3.connect(target_db)
            op = "=" if key_match and "%" not in key_match else "LIKE"
            con.execute(
                f"UPDATE {table} SET etag=NULL, last_modified=NULL WHERE {key_col} {op} ?",
                (key_match,),
            )
            con.commit()
            con.close()
        except sqlite3.OperationalError:
            # Column missing on legacy schema — fine, the other table covers it.
            pass
        except Exception as e:
            print(f"[canary] WARNING: could not invalidate ETag in {target_db}: {e}")

    if http_override:
        mode = http_override.get("mode", "ok")
        print(f"[canary] Scenario {name!r}: payload written. Restart endpoint with MODE={mode}")
    else:
        print(f"[canary] Scenario {name!r}: payload written")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 canary_scenarios.py <scenario-name>")
        print("Available:", list(SCENARIOS))
        sys.exit(1)

    name = sys.argv[1]
    served = Path(__file__).parent.parent / "web" / "canary" / "mother-sands.json"
    default_db = str(Path(__file__).parent.parent / "data" / "tasks" / "heartbeat_log.db")
    db = os.environ.get("HEARTBEAT_DB_PATH", default_db)

    # Story 3.10 B1: toggle ext_mom.thresholdMode in the served canary payload.
    # Self-describing demo mode — the canary endpoint itself tells the link-handler
    # to emit a per-feature thresholds_override. No env var, no container restart.
    if name == "threshold-mode":
        if len(sys.argv) < 3 or sys.argv[2] not in ("on", "off"):
            print("Usage: python3 canary_scenarios.py threshold-mode on|off")
            sys.exit(1)
        new_value = sys.argv[2] == "on"
        payload = json.loads(served.read_text()) if served.exists() else _baseline()
        payload.setdefault("ext_mom", {})
        payload["ext_mom"]["thresholdMode"] = new_value
        # Safe write — temp → fsync → atomic rename
        import tempfile as _tf
        with _tf.NamedTemporaryFile(mode="w", suffix=".json", dir=served.parent, delete=False) as tmp:
            json.dump(payload, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = tmp.name
        os.chmod(tmp_path, 0o644)
        os.rename(tmp_path, served)
        print(f"[canary] ext_mom.thresholdMode = {new_value}")
        sys.exit(0)

    apply_scenario(name, served, db_path=db if Path(db).exists() else None)
