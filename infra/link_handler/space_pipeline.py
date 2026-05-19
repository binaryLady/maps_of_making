"""Clean space pipeline for Epic 3.5 — Story 3.7 fetch seam migration.

Handles registered-space heartbeat fetches with three-outcome rules:
  - HTTP 200 → fetch_status=ok, observed_at fresh mint, full payload
  - HTTP 304 → fetch_status=not_modified, observed_at advances to now, payload from prior
  - Error/unreachable → fetch_status=unreachable, observed_at frozen, prior snapshot untouched

Outcome rules ensure the snapshot store is single source of truth for fetch timing.
"""
import logging
from typing import Optional

import httpx

from snapshot_store import (
    mint_observed_at,
    write_snapshot,
    read_snapshot,
    advance_observed_at,
    mark_unreachable,
)

logger = logging.getLogger(__name__)


async def fetch_space_snapshot(
    uid: str,
    endpoint_url: str,
    db_path: Optional[str] = None,
) -> dict:
    """Fetch a registered space, enforce three-outcome rules, persist snapshot.

    Args:
        uid: space slug (e.g. "openfab")
        endpoint_url: SpaceAPI endpoint URL
        db_path: optional snapshot store path

    Returns:
        dict with keys:
            - fetch_status: "ok" | "not_modified" | "unreachable"
            - snapshot: full snapshot dict (or None if unreachable)
            - response: httpx.Response object (or None on connection error)
    """
    try:
        prior_snap = read_snapshot(uid, db_path=db_path)
        headers = {}
        if prior_snap:
            if prior_snap.get("etag"):
                headers["if-none-match"] = prior_snap["etag"]
            if prior_snap.get("last_modified"):
                headers["if-modified-since"] = prior_snap["last_modified"]

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(endpoint_url, headers=headers)

    except (
        httpx.ConnectError,
        httpx.TimeoutException,
        httpx.RequestError,
    ) as exc:
        logger.warning("fetch_space_snapshot %s: connection error: %s", uid, exc)
        mark_unreachable(uid, db_path=db_path)
        return {"fetch_status": "unreachable", "snapshot": None, "response": None}

    if resp.status_code == 200:
        try:
            payload = resp.json()
        except Exception as e:
            logger.warning("fetch_space_snapshot %s: JSON decode error: %s", uid, e)
            mark_unreachable(uid, db_path=db_path)
            return {"fetch_status": "unreachable", "snapshot": None, "response": resp}

        observed_at = mint_observed_at()
        etag = resp.headers.get("etag")
        last_modified = resp.headers.get("last-modified")

        write_snapshot(
            uid=uid,
            observed_at=observed_at,
            payload=payload,
            etag=etag,
            last_modified=last_modified,
            fetch_status="ok",
            db_path=db_path,
        )
        logger.info(
            "fetch_space_snapshot %s: HTTP 200 → snapshot minted: observed_at=%s",
            uid,
            observed_at,
        )
        snap = read_snapshot(uid, db_path=db_path)
        return {"fetch_status": "ok", "snapshot": snap, "response": resp}

    elif resp.status_code == 304:
        prior_snap = read_snapshot(uid, db_path=db_path)
        if prior_snap is None:
            logger.warning(
                "fetch_space_snapshot %s: HTTP 304 but no prior snapshot → treat as 200 with empty payload",
                uid,
            )
            observed_at = mint_observed_at()
            write_snapshot(
                uid=uid,
                observed_at=observed_at,
                payload={},
                fetch_status="ok",
                db_path=db_path,
            )
            snap = read_snapshot(uid, db_path=db_path)
            return {"fetch_status": "ok", "snapshot": snap, "response": resp}

        observed_at = mint_observed_at()
        advance_observed_at(uid, observed_at, db_path=db_path)
        snap = read_snapshot(uid, db_path=db_path)
        logger.info(
            "fetch_space_snapshot %s: HTTP 304 → observed_at advanced: %s", uid, observed_at
        )
        return {"fetch_status": "not_modified", "snapshot": snap, "response": resp}

    else:
        logger.warning("fetch_space_snapshot %s: HTTP %s → unreachable", uid, resp.status_code)
        mark_unreachable(uid, db_path=db_path)
        return {"fetch_status": "unreachable", "snapshot": None, "response": resp}
