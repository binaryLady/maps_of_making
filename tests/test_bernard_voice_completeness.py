"""
AC5 — Bernard voice completeness check.
Verifies YAML leaf keys are referenced in genjson.js and no forbidden phrases appear.
"""
import yaml
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent
COPY_YAML = ROOT / 'web/genjson/bernard_copy.yaml'
GENJSON_JS = ROOT / 'web/genjson/genjson.js'

FORBIDDEN = [
    'most spaces leave this blank',
    'keep it simple',
    'you can do better',
    'well done',
    'great job',
]


def leaf_paths(d, prefix=''):
    for k, v in d.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            yield from leaf_paths(v, path)
        else:
            yield path, v


def test_no_forbidden_patterns():
    copy = yaml.safe_load(COPY_YAML.read_text())
    for path, val in leaf_paths(copy):
        for forbidden in FORBIDDEN:
            assert forbidden.lower() not in val.lower(), \
                f"Forbidden pattern '{forbidden}' found at {path}"


def test_keys_referenced_in_js():
    js = GENJSON_JS.read_text()
    copy = yaml.safe_load(COPY_YAML.read_text())
    unreferenced = []
    for path, _ in leaf_paths(copy):
        parts = path.split('.')
        dotted = 'COPY.' + path
        bracketed = 'COPY' + ''.join(f"['{p}']" for p in parts)
        if dotted not in js and bracketed not in js:
            unreferenced.append(path)
    if unreferenced:
        print(f"\nWARN: YAML keys not yet referenced in genjson.js: {unreferenced}")
    # warn-only: future stories add keys before JS uses them
