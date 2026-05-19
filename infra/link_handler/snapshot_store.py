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
            last_modified TEXT
        )
    """)
    con.commit()
    con.close()


def write_snapshot(
    uid: str,
    observed_at: str,
    payload: dict,
    etag: Optional[str] = None,
    last_modified: Optional[str] = None,
    db_path: Optional[str] = None,
) -> None:
    """Write a snapshot row. observed_at must already be minted — never re-stamp here."""
    path = db_path or _get_db_path()
    init_snapshot_db(path)
    payload_json = json.dumps(payload, separators=(",", ":"))
    con = sqlite3.connect(path)
    con.execute("""
        INSERT INTO snapshots (uid, observed_at, payload, etag, last_modified)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(uid) DO UPDATE SET
            observed_at=excluded.observed_at,
            payload=excluded.payload,
            etag=excluded.etag,
            last_modified=excluded.last_modified
    """, (uid, observed_at, payload_json, etag, last_modified))
    con.commit()
    con.close()


def read_snapshot(uid: str, db_path: Optional[str] = None) -> Optional[dict]:
    """Read snapshot row for uid. Returns dict or None."""
    path = db_path or _get_db_path()
    init_snapshot_db(path)
    con = sqlite3.connect(path)
    row = con.execute(
        "SELECT uid, observed_at, payload, etag, last_modified FROM snapshots WHERE uid=?",
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
    }


def mint_observed_at() -> str:
    """Mint a UTC ISO-8601 instant. Call exactly once per successful fetch.

    Uses Z suffix (not +00:00) so the value is byte-identical when round-tripped
    through Oxigraph (which normalizes xsd:dateTime to Z format).
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
