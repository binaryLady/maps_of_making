#!/usr/bin/env python3
"""Validate a Space JSON-LD URL against both validators:
  1. mom (local /api/validate-url on localhost)
  2. SpaceAPI v14 (validator.spaceapi.io public API)

Usage:
  python scripts/validate_dual.py <public-url-of-jsonld>
  python scripts/validate_dual.py --file web/test-fixtures/openfab.jsonld

Exit codes:
  0 — both validators happy
  1 — mom failed
  2 — SpaceAPI failed
  3 — both failed
"""
import argparse
import json
import sys
import urllib.request
from urllib.error import URLError


MOM_VALIDATE = "http://localhost/api/validate-url"
SPACEAPI_VALIDATE = "https://validator.spaceapi.io/v2/?url="


def _post_json(url: str, body: dict, timeout: float = 15.0) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _get_json(url: str, timeout: float = 15.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def validate_mom(public_url: str) -> tuple[bool, dict]:
    try:
        result = _post_json(MOM_VALIDATE, {"url": public_url})
    except URLError as e:
        return False, {"error": f"mom validator unreachable: {e}"}
    ok = bool(result.get("json_ld_valid") and result.get("coords_found"))
    return ok, result


def validate_spaceapi(public_url: str) -> tuple[bool, dict]:
    try:
        result = _get_json(SPACEAPI_VALIDATE + public_url)
    except URLError as e:
        return False, {"error": f"SpaceAPI validator unreachable: {e}"}
    valid = bool(result.get("valid") is True or (result.get("v14") or {}).get("valid"))
    # Surface schemaErrors[] which the SpaceAPI validator returns but its UI buries.
    errs = result.get("schemaErrors") or (result.get("v14") or {}).get("schemaErrors")
    if errs:
        result["_schema_errors_summary"] = [
            f"{e.get('property', '?')}: {e.get('message', e)}" if isinstance(e, dict) else str(e)
            for e in errs
        ]
    return valid, result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("url", help="Public URL of the JSON-LD document")
    args = p.parse_args()

    print(f"→ Validating {args.url}")
    print("\n[1/2] mom validator (localhost)…")
    mom_ok, mom_res = validate_mom(args.url)
    print(json.dumps(mom_res, indent=2))
    print(f"  → {'PASS' if mom_ok else 'FAIL'} | tier: {mom_res.get('subset', 'n/a')}")

    print("\n[2/2] SpaceAPI v14 validator (validator.spaceapi.io)…")
    sa_ok, sa_res = validate_spaceapi(args.url)
    print(json.dumps(sa_res, indent=2))
    print(f"  → {'PASS' if sa_ok else 'FAIL'}")

    code = (0 if mom_ok else 1) | (0 if sa_ok else 2)
    print(f"\nExit code: {code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
