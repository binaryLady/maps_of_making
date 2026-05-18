#!/usr/bin/env python3
"""Validate ontology/crosswalk.csv against the no-redefinition rule (Story 3.5, AC4).

Rule: no extension namespace may REDEFINE a core:/mom: field — it may only ALIAS
it. Concretely: any row that fills both `core_field` and at least one extension
field (`fab_field` / `omt_field` / `edu_field`) MUST declare a `skos:` mapping
type (`skos:exactMatch` or `skos:closeMatch`). A non-skos or empty mapping_type
on such a row means the extension is claiming to be the core field — rejected.

Runnable standalone:

    python scripts/validate_crosswalk.py

Exit 0 + one-line summary on success; non-zero + clear message on failure.
"""

import csv
import sys
from pathlib import Path

CROSSWALK = Path(__file__).resolve().parent.parent / "ontology" / "crosswalk.csv"

REQUIRED_COLUMNS = {"concept", "core_field", "spaceapi_field", "fab_field",
                    "omt_field", "edu_field", "mapping_type", "notes"}
EXTENSION_FIELDS = ("fab_field", "omt_field", "edu_field")
ALIAS_TYPES = {"skos:exactMatch", "skos:closeMatch"}


def validate(path: Path) -> list[str]:
    """Return a list of human-readable error strings (empty = valid)."""
    errors: list[str] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return ["crosswalk.csv appears to be empty — no header row found"]
        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            return [f"crosswalk.csv is missing expected column(s): {sorted(missing)}"]
        for lineno, row in enumerate(reader, start=2):  # header is line 1
            concept = (row.get("concept") or "").strip()
            core_field = (row.get("core_field") or "").strip()
            mapping_type = (row.get("mapping_type") or "").strip()
            ext_cols = {
                col
                for col in EXTENSION_FIELDS
                if (row.get(col) or "").strip()
            }
            if core_field and ext_cols and mapping_type not in ALIAS_TYPES:
                errors.append(
                    f"line {lineno} [{concept}]: core_field '{core_field}' is "
                    f"also claimed by extension column(s) {sorted(ext_cols)} "
                    f"but mapping_type is '{mapping_type or '(empty)'}' — must be "
                    f"an explicit alias (skos:exactMatch / skos:closeMatch). "
                    f"Extensions may alias a core field, never redefine it."
                )
    return errors


def main() -> int:
    if not CROSSWALK.exists():
        print(f"ERROR: crosswalk not found at {CROSSWALK}", file=sys.stderr)
        return 1

    with CROSSWALK.open(newline="", encoding="utf-8") as f:
        row_count = sum(1 for _ in csv.DictReader(f))

    errors = validate(CROSSWALK)
    if errors:
        print(f"FAIL: {len(errors)} no-redefinition violation(s) in {CROSSWALK.name}:",
              file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"OK: crosswalk valid — {row_count} rows checked, no-redefinition rule holds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
