import pytest
from main import SpaceAPISchema, SpaceAPIGeo, classify_subset


def test_spaceapi_geo_parsing():
    """Test SpaceAPIGeo model parsing."""
    # With schema: prefixes
    data = {
        "schema:geo": {
            "schema:latitude": 50.5,
            "schema:longitude": 4.5
        }
    }
    schema = SpaceAPISchema.model_validate(data)
    assert schema.resolved_lat == 50.5
    assert schema.resolved_lon == 4.5

    # With plain keys
    data = {
        "schema:geo": {
            "latitude": 50.5,
            "longitude": 4.5
        }
    }
    schema = SpaceAPISchema.model_validate(data)
    assert schema.resolved_lat == 50.5
    assert schema.resolved_lon == 4.5


def test_spaceapi_name_parsing():
    """Test name resolution with aliases."""
    # schema:name takes priority
    data = {
        "schema:name": "FabLab Brussels",
        "name": "Old Name"
    }
    schema = SpaceAPISchema.model_validate(data)
    assert schema.resolved_name == "FabLab Brussels"

    # Plain name fallback
    data = {"name": "FabLab Brussels"}
    schema = SpaceAPISchema.model_validate(data)
    assert schema.resolved_name == "FabLab Brussels"


def test_classify_subset_none():
    """Test subset classification when validation fails."""
    schema = SpaceAPISchema()
    result = classify_subset(schema)
    assert result["subset"] == "none"
    assert result["subset_score"] == 0
    assert result["unlock_message"] is None


def test_classify_subset_required():
    """Test mom:required subset (name + coords only)."""
    data = {
        "schema:name": "FabLab",
        "schema:geo": {
            "schema:latitude": 50.5,
            "schema:longitude": 4.5
        }
    }
    schema = SpaceAPISchema.model_validate(data)
    result = classify_subset(schema)
    assert result["subset"] == "mom:required"
    assert result["subset_score"] == 1
    assert "schema:url" in result["missing_card_fields"]
    assert "schema:openingHours" in result["missing_card_fields"]
    assert result["next_subset"] == "mom:card"


def test_classify_subset_card():
    """Test mom:card subset (required + url + hours)."""
    data = {
        "schema:name": "FabLab",
        "schema:geo": {
            "schema:latitude": 50.5,
            "schema:longitude": 4.5
        },
        "schema:url": "https://fablab.be",
        "schema:openingHours": "Mo-Fr 10:00-18:00"
    }
    schema = SpaceAPISchema.model_validate(data)
    result = classify_subset(schema)
    assert result["subset"] == "mom:card"
    assert result["subset_score"] == 2
    assert "api_compatibility" in result["missing_card_fields"]
    assert "logo" in result["missing_card_fields"]
    assert "contact" in result["missing_card_fields"]
    assert result["next_subset"] == "spaceapi:compatible"


def test_classify_subset_spaceapi():
    """Test spaceapi:compatible subset (full set)."""
    data = {
        "schema:name": "FabLab",
        "schema:geo": {
            "schema:latitude": 50.5,
            "schema:longitude": 4.5
        },
        "schema:url": "https://fablab.be",
        "schema:openingHours": "Mo-Fr 10:00-18:00",
        "api_compatibility": ["v14"],
        "logo": "https://example.com/logo.png",
        "contact": {"phone": "123-456"}
    }
    schema = SpaceAPISchema.model_validate(data)
    result = classify_subset(schema)
    assert result["subset"] == "spaceapi:compatible"
    assert result["subset_score"] == 3
    assert result["missing_card_fields"] == []
    assert result["next_subset"] is None


def test_classify_subset_partial_card():
    """Test when one card field is missing."""
    data = {
        "schema:name": "FabLab",
        "schema:geo": {
            "schema:latitude": 50.5,
            "schema:longitude": 4.5
        },
        "schema:url": "https://fablab.be"
        # missing: schema:openingHours
    }
    schema = SpaceAPISchema.model_validate(data)
    result = classify_subset(schema)
    assert result["subset"] == "mom:required"
    assert result["subset_score"] == 1
    assert "schema:openingHours" in result["missing_card_fields"]


def test_spaceapi_extra_fields():
    """Test that extra fields are allowed but ignored."""
    data = {
        "schema:name": "FabLab",
        "schema:geo": {
            "schema:latitude": 50.5,
            "schema:longitude": 4.5
        },
        "custom_field": "custom_value",
        "another_extra": 123
    }
    schema = SpaceAPISchema.model_validate(data)
    assert schema.resolved_name == "FabLab"
    # Extra fields are allowed but not accessible via model properties


def test_spaceapi_flat_key_required():
    """SpaceAPI v14 flat shape (space + location.lat/lon) reaches mom:required."""
    data = {
        "space": "OpenFab",
        "location": {"lat": 50.833, "lon": 4.378, "address": "158 Rue Gray, 1050 Ixelles"}
    }
    schema = SpaceAPISchema.model_validate(data)
    assert schema.resolved_name == "OpenFab"
    assert schema.resolved_lat == 50.833
    assert schema.resolved_lon == 4.378
    result = classify_subset(schema)
    assert result["subset"] == "mom:required"
    assert result["subset_score"] == 1


def test_spaceapi_flat_key_card():
    """SpaceAPI v14 flat shape with url + opening_hours reaches mom:card."""
    data = {
        "space": "OpenFab",
        "url": "https://openfab.be",
        "location": {"lat": 50.833, "lon": 4.378},
        "opening_hours": "Tu-Sa 10:00-22:00",
    }
    schema = SpaceAPISchema.model_validate(data)
    assert schema.resolved_url == "https://openfab.be"
    assert schema.resolved_opening_hours == "Tu-Sa 10:00-22:00"
    result = classify_subset(schema)
    assert result["subset"] == "mom:card"
    assert result["subset_score"] == 2
