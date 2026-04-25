"""Normalize VOW workshop scrape to MOM-compliant JSON-LD and geocode via Nominatim."""

import json
import logging
import re
import sys
from pathlib import Path

import yaml
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent
INPUT_FILE = REPO_ROOT / "web" / "data" / "vow_workshops.json"
OUTPUT_FILE = REPO_ROOT / "web" / "data" / "moms_seed.json"
FAILURES_FILE = REPO_ROOT / "web" / "data" / "moms_seed_geocode_failures.json"
CATEGORY_MAP_FILE = Path(__file__).parent / "category_map.yaml"

USER_AGENT = "maps-of-making-seed-pipeline/1.0 (nicolas.de.barquin@gmail.com)"


def load_category_map() -> dict:
    with open(CATEGORY_MAP_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_address(raw: str) -> tuple[dict, str, str]:
    """Parse 'Street, POSTCODE City' into components. Returns (address_dict, city, postcode)."""
    parts = raw.split(",", 1)
    street = parts[0].strip() if parts else raw.strip()
    postcode = ""
    city = ""

    if len(parts) == 2:
        rest = parts[1].strip()
        m = re.search(r"(\d{5})\s*(.*)", rest)
        if m:
            postcode = m.group(1)
            city = m.group(2).strip()
        else:
            log.warning("Address parse: no postcode in %r", raw)
            city = rest if rest else ""
    else:
        log.warning("Address parse: no comma separator in %r", raw)

    address_dict = {
        "@type": "schema:PostalAddress",
        "schema:streetAddress": street,
        "schema:postalCode": postcode,
        "schema:addressLocality": city,
        "schema:addressCountry": "DE",
    }
    return address_dict, city, postcode


def map_categories(raw_cats: list, category_map: dict) -> list:
    result = []
    for cat in raw_cats:
        if cat in category_map:
            result.append(category_map[cat])
        else:
            log.warning("Unmapped category %r — including verbatim", cat)
            result.append(cat)
    return result


def geocode_with_fallback(geocode_fn, address_raw: str, city: str) -> tuple:
    """Try geocoding with fallback strategy. Returns (geo_result, fidelity, note)."""
    # Try 1: Full address
    try:
        query = f"{address_raw}, Germany"
        geo = geocode_fn(query)
        if geo:
            return geo, "exact", ""
    except Exception:
        pass

    # Try 2: City only (if available and different from full address)
    if city and city.strip():
        try:
            query = f"{city}, Germany"
            geo = geocode_fn(query)
            if geo:
                note = "Address incomplete — showing city-level location"
                return geo, "city", note
        except Exception:
            pass

    # Try 3: Country fallback (Germany center)
    try:
        query = "Germany"
        geo = geocode_fn(query)
        if geo:
            note = "Address incomplete — showing country-level location"
            return geo, "country", note
    except Exception:
        pass

    return None, "", ""


def build_entry(raw: dict, geo_result, category_map: dict, address_dict: dict, fidelity: str = "exact", note: str = "") -> dict:
    tags = map_categories(raw.get("categories", []), category_map)

    entry = {
        "@type": "mom:Space",
        "schema:name": raw.get("name", ""),
        "schema:address": address_dict,
        "schema:geo": {
            "@type": "schema:GeoCoordinates",
            "schema:latitude": geo_result.latitude,
            "schema:longitude": geo_result.longitude,
        },
        "schema:url": raw.get("website", ""),
        "mom:profileUrl": raw.get("profileUrl", ""),
        "schema:knowsAbout": tags,
        "mom:source": "scraped-vow",
        "mom:operationalState": "seeded",
        "mom:geolocationFidelity": fidelity,
    }
    if note:
        entry["mom:geolocationNote"] = note
    return entry


def main() -> int:
    category_map = load_category_map()

    with open(INPUT_FILE, encoding="utf-8") as f:
        workshops = json.load(f)

    total = len(workshops)
    log.info("Geocoding %d entries at 1 req/s — estimated %d minutes", total, total // 60)

    geolocator = Nominatim(user_agent=USER_AGENT)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    results = []
    failures = []

    for i, raw in enumerate(workshops, start=1):
        if i % 50 == 0:
            log.info("Processed %d/%d", i, total)

        name = raw.get("name", f"entry-{i}")
        address_raw = raw.get("address", "")
        address_dict, city, _ = parse_address(address_raw)

        try:
            geo, fidelity, note = geocode_with_fallback(geocode, address_raw, city)
        except Exception as exc:
            log.error("Geocode error for %r: %s", name, exc)
            failures.append(raw)
            continue

        if geo is None:
            log.warning("Geocode failed (all fallbacks exhausted) for %r", name)
            failures.append(raw)
            continue

        try:
            entry = build_entry(raw, geo, category_map, address_dict, fidelity=fidelity, note=note)
            results.append(entry)
        except Exception as exc:
            log.error("Build entry error for %r: %s", name, exc)
            failures.append(raw)

    # Count fidelity levels
    exact = sum(1 for r in results if r.get("mom:geolocationFidelity") == "exact")
    city_count = sum(1 for r in results if r.get("mom:geolocationFidelity") == "city")
    country = sum(1 for r in results if r.get("mom:geolocationFidelity") == "country")
    log.info(
        "Done: %d total | %d exact, %d city, %d country | %d failures",
        len(results), exact, city_count, country, len(failures),
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(FAILURES_FILE, "w", encoding="utf-8") as f:
        json.dump(failures, f, ensure_ascii=False, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
