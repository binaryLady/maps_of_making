"""Unit tests for normalize_vow.py pure functions."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from normalize_vow import parse_address, map_categories, build_entry, load_category_map, geocode_with_fallback


def test_parse_address_standard():
    addr_dict, city, postcode = parse_address("Jagdweg 1-3, 01159 Dresden")
    assert addr_dict["schema:streetAddress"] == "Jagdweg 1-3"
    assert addr_dict["schema:postalCode"] == "01159"
    assert addr_dict["schema:addressLocality"] == "Dresden"
    assert addr_dict["schema:addressCountry"] == "DE"
    assert addr_dict["@type"] == "schema:PostalAddress"
    assert city == "Dresden"
    assert postcode == "01159"


def test_parse_address_no_comma(caplog):
    import logging
    with caplog.at_level(logging.WARNING):
        addr_dict, city, postcode = parse_address("Kein Komma hier")
    assert addr_dict["schema:streetAddress"] == "Kein Komma hier"
    assert "separator" in caplog.text


def test_parse_address_no_postcode(caplog):
    import logging
    with caplog.at_level(logging.WARNING):
        addr_dict, city, postcode = parse_address("Hauptstraße 1, Berlin")
    assert addr_dict["schema:addressLocality"] == "Berlin"
    assert postcode == ""
    assert "postcode" in caplog.text


def test_map_categories_known():
    cat_map = {"Holz": "wood", "Elektronik": "electronics"}
    result = map_categories(["Holz", "Elektronik"], cat_map)
    assert result == ["wood", "electronics"]


def test_map_categories_unknown_verbatim(caplog):
    import logging
    with caplog.at_level(logging.WARNING):
        result = map_categories(["UnknownStuff"], {"Holz": "wood"})
    assert result == ["UnknownStuff"]
    assert "Unmapped category" in caplog.text


def test_map_categories_empty():
    assert map_categories([], {}) == []


def test_build_entry_structure():
    geo = MagicMock()
    geo.latitude = 51.05
    geo.longitude = 13.73
    raw = {
        "name": "Test Space",
        "address": "Teststr. 1, 01159 Dresden",
        "website": "https://example.com",
        "profileUrl": "https://offene-werkstaetten.org/werkstatt/test",
        "categories": ["Holz"],
    }
    addr_dict, _, _ = parse_address("Teststr. 1, 01159 Dresden")
    entry = build_entry(raw, geo, {"Holz": "wood"}, addr_dict, fidelity="precise")
    assert entry["@type"] == "mom:MakerSpace"
    assert entry["schema:name"] == "Test Space"
    assert entry["schema:geo"]["schema:latitude"] == 51.05
    assert entry["schema:geo"]["schema:longitude"] == 13.73
    assert entry["schema:geo"]["@type"] == "schema:GeoCoordinates"
    assert entry["schema:knowsAbout"] == ["wood"]
    assert entry["mom:source"] == "mak:scraped-vow"
    assert entry["mom:freshnessStatus"] == "mak:seeded"
    assert entry["schema:url"] == "https://example.com"
    assert entry["mom:profileUrl"] == "https://offene-werkstaetten.org/werkstatt/test"
    assert entry["mom:geolocationFidelity"] == "precise"


def test_build_entry_with_fidelity_note():
    geo = MagicMock()
    geo.latitude = 51.0
    geo.longitude = 10.0
    raw = {"name": "City Space", "address": ", Berlin", "website": None, "profileUrl": "", "categories": []}
    addr_dict, _, _ = parse_address(", Berlin")
    entry = build_entry(raw, geo, {}, addr_dict, fidelity="city-level", note="Address incomplete")
    assert entry["mom:geolocationFidelity"] == "city-level"
    assert entry["mom:geolocationNote"] == "Address incomplete"


def test_load_category_map_covers_all_18():
    cat_map = load_category_map()
    expected = {
        "3D-Druck", "Biologie/Chemie", "CNC-Fräse", "Druckverfahren", "Elektronik",
        "Fahrrad", "Fotolabor", "Holz", "Keramik/Töpfern", "Kunststoff",
        "Laserschneiden", "Lebensmittel", "Malerei", "Metall", "Programmieren",
        "Stein", "Textil", "digitale Medien",
    }
    assert set(cat_map.keys()) == expected


def test_geocode_with_fallback_precise():
    geo_mock = MagicMock()
    geo_mock.latitude = 51.05
    geo_mock.longitude = 13.73
    geocode_fn = MagicMock(return_value=geo_mock)

    result, fidelity, note = geocode_with_fallback(geocode_fn, "Jagdweg 1-3, 01159 Dresden", "Dresden")
    assert result == geo_mock
    assert fidelity == "precise"
    assert note == ""


def test_geocode_with_fallback_city_level():
    geo_mock = MagicMock()
    geo_mock.latitude = 51.0
    geo_mock.longitude = 10.0
    geocode_fn = MagicMock(side_effect=[None, geo_mock])  # Full address fails, city succeeds

    result, fidelity, note = geocode_with_fallback(geocode_fn, ", Berlin", "Berlin")
    assert result == geo_mock
    assert fidelity == "city-level"
    assert "incomplete" in note.lower()


def test_geocode_with_fallback_country_level():
    geo_mock = MagicMock()
    geo_mock.latitude = 51.1
    geo_mock.longitude = 10.5
    # Full address fails, city skipped (empty), country succeeds
    geocode_fn = MagicMock(side_effect=[None, geo_mock])

    result, fidelity, note = geocode_with_fallback(geocode_fn, ", ", "")
    assert result == geo_mock
    assert fidelity == "country-level"
    assert "incomplete" in note.lower()
