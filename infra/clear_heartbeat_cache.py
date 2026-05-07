#!/usr/bin/env python3
"""Clear stale HTTP caching headers from heartbeat_log.db for one or more spaces.

Usage:
    python3 clear_heartbeat_cache.py <space_id> [space_id2 ...]
    python3 clear_heartbeat_cache.py --all

This forces the next heartbeat cycle to fetch without If-None-Match / If-Modified-Since
headers, guaranteeing a 200 response and content refresh.
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = "/app/tasks/heartbeat_log.db"


def clear_cache(db_path: str, space_ids: list[str]) -> None:
    """Clear etag and last_modified for specified spaces."""
    con = sqlite3.connect(db_path)
    for space_id in space_ids:
        con.execute(
            "UPDATE heartbeat_log SET etag = NULL, last_modified = NULL WHERE space_id = ?",
            (space_id,)
        )
        rows = con.total_changes
        print(f"Cleared cache for {space_id}")
    con.commit()
    con.close()
    print(f"✓ Cache cleared for {len(space_ids)} space(s)")


def clear_all(db_path: str) -> None:
    """Clear etag and last_modified for ALL spaces."""
    con = sqlite3.connect(db_path)
    con.execute("UPDATE heartbeat_log SET etag = NULL, last_modified = NULL")
    count = con.total_changes
    con.commit()
    con.close()
    print(f"✓ Cache cleared for ALL {count} space(s)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 clear_heartbeat_cache.py <space_id> [space_id2 ...] or --all")
        sys.exit(1)

    if sys.argv[1] == "--all":
        clear_all(DB_PATH)
    else:
        clear_cache(DB_PATH, sys.argv[1:])
