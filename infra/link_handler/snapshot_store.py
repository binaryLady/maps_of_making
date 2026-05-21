"""Clean snapshot store for Epic 3.5 — one snapshot per successful fetch.

The snapshot is the unit: {uid, observed_at, payload, etag, last_modified}.
observed_at is minted once at fetch and must be byte-identical at all downstream
stages. This store is the single source of truth for that token.

Does NOT touch heartbeat_log.db. Legacy path is completely separate.
"""
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


SNAPSHOT_DB_DEFAULT = "/app/tasks/snapshot_store.db"


def _get_db_path() -> str:
    return os.getenv("SNAPSHOT_DB_PATH") or SNAPSHOT_DB_DEFAULT


def init_snapshot_db(db_path: Optional[str] = None) -> None:
    path = db_path or _get_db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            uid TEXT PRIMARY KEY,
            observed_at TEXT NOT NULL,
            payload TEXT NOT NULL,
            etag TEXT,
            last_modified TEXT,
            fetch_status TEXT NOT NULL DEFAULT 'ok',
            fetch_error TEXT
        )
    """)
    cols = {r[1] for r in con.execute("PRAGMA table_info(snapshots)").fetchall()}
    if "fetch_status" not in cols:
        con.execute("ALTER TABLE snapshots ADD COLUMN fetch_status TEXT NOT NULL DEFAULT 'ok'")
    if "fetch_error" not in cols:
        con.execute("ALTER TABLE snapshots ADD COLUMN fetch_error TEXT")
    con.commit()
    con.close()


def write_snapshot(
    uid: str,
    observed_at: str,
    payload: dict,
    etag: Optional[str] = None,
    last_modified: Optional[str] = None,
    fetch_status: str = "ok",
    db_path: Optional[str] = None,
) -> None:
    """Write a snapshot row. observed_at must already be minted — never re-stamp here."""
    path = db_path or _get_db_path()
    init_snapshot_db(path)
    payload_json = json.dumps(payload, separators=(",", ":"))
    con = sqlite3.connect(path)
    con.execute("""
        INSERT INTO snapshots (uid, observed_at, payload, etag, last_modified, fetch_status, fetch_error)
        VALUES (?, ?, ?, ?, ?, ?, NULL)
        ON CONFLICT(uid) DO UPDATE SET
            observed_at=excluded.observed_at,
            payload=excluded.payload,
            etag=excluded.etag,
            last_modified=excluded.last_modified,
            fetch_status=excluded.fetch_status,
            fetch_error=NULL
    """, (uid, observed_at, payload_json, etag, last_modified, fetch_status))
    con.commit()
    con.close()


def read_snapshot(uid: str, db_path: Optional[str] = None) -> Optional[dict]:
    """Read snapshot row for uid. Returns dict or None."""
    path = db_path or _get_db_path()
    init_snapshot_db(path)
    con = sqlite3.connect(path)
    row = con.execute(
        "SELECT uid, observed_at, payload, etag, last_modified, fetch_status, fetch_error FROM snapshots WHERE uid=?",
        (uid,)
    ).fetchone()
    con.close()
    if row is None:
        return None
    return {
        "uid": row[0],
        "observed_at": row[1],
        "payload": json.loads(row[2]),
        "etag": row[3],
        "last_modified": row[4],
        "fetch_status": row[5],
        "fetch_error": row[6],
    }


def mint_observed_at() -> str:
    """Mint a UTC ISO-8601 instant. Call exactly once per successful fetch.

    Uses Z suffix (not +00:00) so the value is byte-identical when round-tripped
    through Oxigraph (which normalizes xsd:dateTime to Z format).
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def advance_observed_at(uid: str, observed_at: str, db_path: Optional[str] = None) -> None:
    """Update observed_at and mark fetch_status='not_modified'. Called on 304 responses."""
    path = db_path or _get_db_path()
    con = sqlite3.connect(path)
    con.execute(
        "UPDATE snapshots SET observed_at=?, fetch_status='not_modified' WHERE uid=?",
        (observed_at, uid)
    )
    con.commit()
    con.close()


def mark_unreachable(uid: str, db_path: Optional[str] = None, reason: Optional[str] = None) -> None:
    """Mark fetch_status='unreachable'. Does NOT touch observed_at.

    `reason` is a short human-readable string (e.g. "HTTP 503", "Invalid JSON at line 19",
    "DNS resolution failed") surfaced to coordinators as a CTA hint on the broken card.
    """
    path = db_path or _get_db_path()
    con = sqlite3.connect(path)
    con.execute(
        "UPDATE snapshots SET fetch_status='unreachable', fetch_error=? WHERE uid=?",
        (reason, uid),
    )
    con.commit()
    con.close()


def read_last_ok_observed_at(uid: str, db_path: Optional[str] = None) -> Optional[str]:
    """Read observed_at if row exists and endpoint was reachable (ok or not_modified), else None."""
    path = db_path or _get_db_path()
    con = sqlite3.connect(path)
    row = con.execute(
        "SELECT observed_at FROM snapshots WHERE uid=? AND fetch_status != 'unreachable'",
        (uid,)
    ).fetchone()
    con.close()
    return row[0] if row else None
