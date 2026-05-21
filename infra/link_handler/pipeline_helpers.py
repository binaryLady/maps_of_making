"""Shared pipeline helpers used by canary and regular-space heartbeat paths.

Extracted from transformer.py (Story 3.10 Step 1) so the unified pipeline
does not depend on the legacy transformer module.
"""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

_config: Optional[dict] = None


def get_config(config_path: Optional[str] = None) -> dict:
    """Load config.yaml once. Path overridable via CONFIG_PATH env var."""
    global _config
    if _config is not None:
        return _config
    path = config_path or os.getenv("CONFIG_PATH") or str(
        Path(__file__).parent / "config.yaml"
    )
    try:
        with open(path) as f:
            _config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning("config.yaml not found at %s, using defaults", path)
        _config = {}
    return _config


def detect_diff(old_snap: dict, new_snap: dict) -> dict | None:
    """Return field-level diff between two space snapshots.

    Ignores: mom:lastFetched, mom:snapshotDate, whitespace-only changes,
    and array order differences. Returns None if no material change.

    First-fetch case: if old_snap is None, returns a diff (not None) to signal
    that the initial fetch is always treated as a material change.
    """
    if old_snap is None:
        return {"added": list(new_snap.keys()) if isinstance(new_snap, dict) else [], "changed": [], "removed": []}

    if new_snap is None:
        return None

    _IGNORED = {"mom:lastFetched", "mom:snapshotDate", "lastFetched", "snapshotDate",
                "sensors", "extensions", "state"}

    def _normalize(obj):
        if isinstance(obj, dict):
            return {k: _normalize(v) for k, v in sorted(obj.items()) if k not in _IGNORED}
        if isinstance(obj, list):
            normalized = [_normalize(i) for i in obj]
            try:
                return sorted(normalized, key=lambda x: json.dumps(x, sort_keys=True))
            except TypeError:
                return normalized
        if isinstance(obj, str):
            return obj.strip()
        return obj

    old_n = _normalize(old_snap)
    new_n = _normalize(new_snap)
    all_keys = set(old_n) | set(new_n)
    changed = []
    added = []
    removed = []
    for key in sorted(all_keys):
        if key in old_n and key not in new_n:
            removed.append(key)
        elif key not in old_n and key in new_n:
            added.append(key)
        elif old_n.get(key) != new_n.get(key):
            changed.append({"field": key, "old": old_n[key], "new": new_n[key]})

    if not (changed or added or removed):
        return None

    return {"changed": changed, "added": added, "removed": removed}


def _extract_open_now(state) -> Optional[bool]:
    """Extract open/closed boolean from SpaceAPI state field.

    Handles v15 object {open: bool}, v0.13 string "open"/"closed", and returns
    None for missing, unknown, or malformed values (downstream defaults to false).
    """
    if state is None:
        return None
    if isinstance(state, dict):
        val = state.get("open")
        if isinstance(val, bool):
            return val
        return None
    if isinstance(state, str):
        s = state.strip().lower()
        if s == "open":
            return True
        if s == "closed":
            return False
        return None
    return None


def _extract_last_open_change(state) -> Optional[str]:
    """Extract lastchange epoch from v15 state object, return ISO datetime or None."""
    if not isinstance(state, dict):
        return None
    ts = state.get("lastchange")
    if isinstance(ts, (int, float)) and ts > 0:
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except (OSError, OverflowError, ValueError):
            logger.warning("WARNING_INVALID_LASTCHANGE: cannot convert %s to datetime", ts)
    return None
