"""Offline unit test for _to_iso_datetime — the backfill timestamp normalizer.

Regression guard for the "updated unknown" bug: the one-time mom:updatedAt backfill
stamps from the snapshot's HTTP Last-Modified header, which is RFC 7231 date format
("Thu, 11 Jun 2026 00:08:43 GMT") — NOT a valid xsd:dateTime. If written verbatim it
poisons the graph and the browser renders "updated unknown". This proves the helper
converts HTTP-date → ISO while leaving ISO strings untouched.

No live seams — pure function. Run: pytest tests/test_updated_at_iso_normalization.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "infra" / "link_handler"))

from pipeline import _to_iso_datetime  # noqa: E402


@pytest.mark.parametrize("raw,expected", [
    # HTTP Last-Modified header (the bug source) → ISO
    ("Thu, 11 Jun 2026 00:08:43 GMT", "2026-06-11T00:08:43+00:00"),
    ("Sun, 29 Jul 2013 18:03:00 GMT", "2013-07-29T18:03:00+00:00"),
    # Already-ISO values pass through untouched (observed_at path)
    ("2026-06-11T06:46:29.434165+00:00", "2026-06-11T06:46:29.434165+00:00"),
    ("2019-11-28T13:53:25Z", "2019-11-28T13:53:25Z"),
    ("2026-06-11", "2026-06-11"),  # date-only ISO
])
def test_normalizes_to_iso(raw, expected):
    assert _to_iso_datetime(raw) == expected


@pytest.mark.parametrize("bad", [None, "", "   ", "not a date"])
def test_unparseable_returns_none(bad):
    # Never raise, never emit a malformed literal — fail soft to None.
    assert _to_iso_datetime(bad) is None


def test_http_date_is_not_mistaken_for_iso():
    """The 'Thu'/'GMT' tokens contain a 'T' — guard must NOT treat them as ISO."""
    out = _to_iso_datetime("Thu, 11 Jun 2026 00:08:43 GMT")
    assert out is not None and "GMT" not in out and out.startswith("2026-06-11T")
