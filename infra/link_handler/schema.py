"""SpaceAPISchema and its nested models — extracted from main.py so that
infra/bot/git_ops.py (running in the separate mak-agent-bot container) can
validate patches against the same model without a second source of truth.
See Story 6.1 Dev Notes "Schema validation reuse needs a shared import path"."""
from typing import Any, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class SpaceAPIGeo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    latitude: Optional[float] = Field(None, alias="schema:latitude")
    longitude: Optional[float] = Field(None, alias="schema:longitude")


class SpaceAPILocation(BaseModel):
    """SpaceAPI v14 flat `location` object: { lat, lon, address }."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    lat: Optional[float] = None
    lon: Optional[float] = None
    address: Optional[str] = None


class SpaceAPISchema(BaseModel):
    """Accepts both mom JSON-LD (`schema:name`, `schema:geo.schema:latitude`)
    and SpaceAPI v14 flat shape (`space`, `location.lat/lon`). One document,
    two validators — see web/test-fixtures/SKILL.md."""
    model_config = ConfigDict(populate_by_name=True, extra="allow", validate_default=True)

    name: Optional[str] = Field(None, alias="schema:name")
    plain_name: Optional[str] = Field(None, alias="name")
    space: Optional[str] = None  # SpaceAPI v14 flat key for name
    geo: Optional[SpaceAPIGeo] = Field(None, alias="schema:geo")
    location: Optional[SpaceAPILocation] = None  # SpaceAPI v14 flat key for coords
    url: Optional[str] = Field(None, alias="schema:url")
    plain_url: Optional[str] = Field(None, alias="url")  # SpaceAPI v14 flat key
    opening_hours: Optional[str] = Field(None, alias="schema:openingHours")
    plain_opening_hours: Optional[str] = Field(None, alias="opening_hours")  # SpaceAPI v14 flat key
    description: Optional[str] = Field(None, alias="schema:description")
    logo: Optional[str] = None
    api_compatibility: Optional[Union[List[str], str]] = None
    contact: Optional[dict] = None
    # Full SpaceAPI v14 tier
    state: Optional[Any] = None  # SpaceAPI v14 `state` may be a string ("open"/"closed"/"unknown") or an object {open: bool, lastchange: int, message: str, ...}. Accept either; classify_subset only checks truthiness.
    networks: Optional[List[str]] = None
    tags: Optional[List[str]] = Field(None, alias="schema:knowsAbout")
    plain_tags: Optional[List[str]] = Field(None, alias="knowsAbout")
    specialties: Optional[List[str]] = None  # mom alias for knowsAbout — same triple, more intuitive key
    # MOM geolocation enrichment
    geolocation_fidelity: Optional[str] = Field(None, alias="mom:geolocationFidelity")
    geolocation_note: Optional[str] = Field(None, alias="mom:geolocationNote")
    # Extended address fields (AC1 extended tier)
    address_locality: Optional[str] = Field(None, alias="schema:addressLocality")
    postal_code: Optional[str] = Field(None, alias="schema:postalCode")
    street_address: Optional[str] = Field(None, alias="schema:streetAddress")
    address_country: Optional[str] = Field(None, alias="schema:addressCountry")

    @property
    def resolved_name(self) -> Optional[str]:
        return self.name or self.plain_name or self.space

    @property
    def resolved_url(self) -> Optional[str]:
        return self.url or self.plain_url

    @property
    def resolved_opening_hours(self) -> Optional[str]:
        return self.opening_hours or self.plain_opening_hours

    @property
    def resolved_lat(self) -> Optional[float]:
        if self.geo and self.geo.latitude is not None:
            return self.geo.latitude
        if self.location and self.location.lat is not None:
            return self.location.lat
        return None

    @property
    def resolved_lon(self) -> Optional[float]:
        if self.geo and self.geo.longitude is not None:
            return self.geo.longitude
        if self.location and self.location.lon is not None:
            return self.location.lon
        return None

    @property
    def resolved_tags(self) -> List[str]:
        raw = self.tags or self.plain_tags or self.specialties or []
        if isinstance(raw, str):
            return [raw]
        return list(raw)

    @property
    def resolved_geolocation_fidelity(self) -> Optional[str]:
        return self.geolocation_fidelity
