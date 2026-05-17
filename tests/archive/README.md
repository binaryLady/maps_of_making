# Archived tests

Tests for code retired by the Story 3.4b clean-slate pivot. Kept in git for
history; **excluded from pytest collection** (see `pytest.ini` → `norecursedirs`).

| File | Tests | Why archived |
|---|---|---|
| `test_seed_import.py` | 25 | Tests `scripts/seed_import.py`, deprecated by Story 3.4b. Bulk VOW/RFF seed import is no longer part of the supported pipeline. |

Do not add new tests here. If bulk import is revived (EU-spaces reintroduction),
restore the relevant file to its original location and remove its `legacy` status.
