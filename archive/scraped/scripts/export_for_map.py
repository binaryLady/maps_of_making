"""
Phase 6: Export member data for map display (GeoJSON).
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

import tomlkit
import geojson
from geopy.geocoders import Nominatim

sys.path.insert(0, str(Path(__file__).parent))
from utils import logger, setup_logging, DataQualityIssue

INPUT_FILE = "lifetech.brussels/members_enhanced.toml"
OUTPUT_FILE = "lifetech.brussels/members.geojson"
CACHE_FILE = "lifetech.brussels/geocoding_cache.json"


class MapDataExporter:
    """Export member data to GeoJSON with geocoding."""

    def __init__(self):
        self.members = []
        self.geocoder = Nominatim(user_agent="maps-of-making")
        self.geocoding_cache = self._load_cache()
        self.quality_issues = []

    def _load_cache(self) -> Dict:
        """Load geocoding cache."""
        if Path(CACHE_FILE).exists():
            return json.loads(Path(CACHE_FILE).read_text())
        return {}

    def _save_cache(self):
        """Save geocoding cache."""
        Path(CACHE_FILE).write_text(json.dumps(self.geocoding_cache, indent=2))

    def load_members(self, input_file: str = INPUT_FILE):
        """Load enhanced member data."""
        if not Path(input_file).exists():
            logger.error(f"Input file not found: {input_file}")
            return False

        with open(input_file) as f:
            doc = tomlkit.parse(f.read())

        members_table = doc.get("members", {})
        for key, member_data in members_table.items():
            if isinstance(member_data, dict):
                member_dict = dict(member_data)
                member_dict["_key"] = key
                self.members.append(member_dict)

        logger.info(f"Loaded {len(self.members)} members")
        return True

    def geocode_address(self, address: str) -> Optional[tuple]:
        """Geocode address (lat, lng)."""
        if not address:
            return None

        if address in self.geocoding_cache:
            return self.geocoding_cache[address]

        try:
            location = self.geocoder.geocode(address)
            if location:
                coords = (location.latitude, location.longitude)
                self.geocoding_cache[address] = coords
                return coords
        except Exception as e:
            logger.debug(f"Geocoding failed for {address}: {e}")

        return None

    def member_to_feature(self, member: Dict) -> Optional[Dict]:
        """Convert member to GeoJSON feature."""
        address = member.get("address_value")
        if not address:
            return None

        coords = self.geocode_address(address)
        if not coords:
            self.quality_issues.append(DataQualityIssue(
                member_id=member.get("_key", "unknown"),
                member_name=member.get("name", "Unknown"),
                severity="LOW",
                issue_type="geocoding_failed",
                description="Could not geocode address",
                related_field="address"
            ))
            return None

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [coords[1], coords[0]]  # [lng, lat]
            },
            "properties": {
                "id": member.get("_key"),
                "name": member.get("name", ""),
                "description": member.get("description_value", ""),
                "website": member.get("website_url", ""),
                "email": member.get("email_value", ""),
                "phone": member.get("phone_value", ""),
                "address": address,
                "website_status": member.get("website_status", ""),
            }
        }

        # Add data quality flags
        if member.get("website_status") in ["redirect", "http_404"]:
            feature["properties"]["warning"] = "Data quality issue detected"

        return feature

    def export_geojson(self, output_file: str = OUTPUT_FILE):
        """Export all members to GeoJSON."""
        features = []

        for member in self.members:
            feature = self.member_to_feature(member)
            if feature:
                features.append(feature)

        geojson_data = {
            "type": "FeatureCollection",
            "features": features
        }

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(geojson_data, f, indent=2)

        logger.info(f"Exported {len(features)} members to {output_file}")
        self._save_cache()
        return output_file


def main():
    """Main export pipeline."""
    setup_logging("INFO")
    logger.info("Starting map data export...")

    exporter = MapDataExporter()

    if not exporter.load_members():
        return 1

    exporter.export_geojson()

    logger.info("Export complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
