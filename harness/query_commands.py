"""SPARQL query dispatch for all read commands (Story 6.3).
Called by commands.try_handle for literal !mom verbs, and by router.route
for the 'query' intent from free-text messages.
"""
import re
import os
import structlog

import bernard
import sparql_client
from bot import git_ops
from bot.git_ops import NoEndpointError

log = structlog.get_logger()

LINK_HANDLER_URL = os.environ.get("LINK_HANDLER_URL", "http://mak-link-handler:8000")

PREFIX = """\
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
"""


def _sanitize(value: str) -> str:
    """Strip SPARQL injection characters from user-supplied strings."""
    return re.sub(r'[{}<>"\\' + r"\n\r\x00-\x1f]", "", value)


async def geocode_city(city: str) -> tuple[float, float] | None:
    """Returns (lat, lon) or None on failure. Uses link_handler Nominatim proxy."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{LINK_HANDLER_URL}/api/geocode",
                json={"address": "", "city": city},
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            return float(data["lat"]), float(data["lon"])
    except Exception as e:
        log.warning("query_commands.geocode_failed", city=city, error=str(e))
        return None


async def space_status(space_id: str) -> str:
    """Return lifecycle report string for a space (public-safe fields only)."""
    query = PREFIX + f"""
SELECT ?name ?openNow ?lastOpenChange ?updatedAt ?subset ?nextUnlock WHERE {{
  GRAPH <urn:mak:space/{space_id}> {{
    ?s a mom:Space ;
       schema:name ?name .
    OPTIONAL {{ ?s mom:openNow ?openNow }}
    OPTIONAL {{ ?s mom:lastOpenChange ?lastOpenChange }}
    OPTIONAL {{ ?s mom:updatedAt ?updatedAt }}
    OPTIONAL {{ ?s mom:subset ?subset }}
    OPTIONAL {{ ?s mom:nextUnlock ?nextUnlock }}
  }}
}}
"""
    try:
        bindings, _ = await sparql_client.run_select(query)
    except Exception as e:
        log.warning("query_commands.status_failed", error=str(e))
        return bernard.query_failed_ack()

    if not bindings:
        return bernard.status_no_link_ack()

    b = bindings[0]
    name = b.get("name", {}).get("value", space_id)
    open_now = b.get("openNow", {}).get("value")
    last_change = b.get("lastOpenChange", {}).get("value", "unknown")
    updated_at = b.get("updatedAt", {}).get("value", "unknown")
    subset = b.get("subset", {}).get("value", "")
    next_unlock = b.get("nextUnlock", {}).get("value", "")

    if open_now == "true":
        state_line = "open"
    elif open_now == "false":
        state_line = "closed"
    else:
        state_line = "state unknown"

    subset_label = subset.split("#")[-1] if subset else ""
    unlock_line = f"Next unlock: {next_unlock}" if next_unlock else ""

    return bernard.status_lifecycle_ack(
        name=name,
        state_line=state_line,
        updated_at=updated_at,
        subset=subset_label,
        unlock_line=unlock_line,
    )


async def hours(space_id: str) -> str:
    """Return opening hours for a linked space."""
    query = PREFIX + f"""
SELECT ?name ?openingHours WHERE {{
  GRAPH <urn:mak:space/{space_id}> {{
    ?s a mom:Space ; schema:name ?name .
    OPTIONAL {{ ?s schema:openingHours ?openingHours }}
  }}
}}
"""
    try:
        bindings, _ = await sparql_client.run_select(query)
    except Exception as e:
        log.warning("query_commands.hours_failed", error=str(e))
        return bernard.query_failed_ack()

    if not bindings:
        return bernard.status_no_link_ack()

    b = bindings[0]
    name = b.get("name", {}).get("value", space_id)
    opening_hours = b.get("openingHours", {}).get("value")
    if opening_hours:
        return bernard.hours_found_ack(name=name, hours=opening_hours)
    return bernard.hours_missing_ack(name=name)


async def find(tag: str, city: str) -> str:
    """Search confirmed spaces by tag and city."""
    tag_s = _sanitize(tag)
    city_s = _sanitize(city)
    query = PREFIX + f"""
SELECT ?name ?city ?website WHERE {{
  GRAPH ?g {{
    ?s a mom:Space ;
       schema:name ?name ;
       schema:knowsAbout ?specialty ;
       mom:endpointUrl ?e .
    OPTIONAL {{ ?s schema:addressLocality ?city }}
    OPTIONAL {{ ?s schema:url ?website }}
    FILTER(STRSTARTS(STR(?g), "urn:mak:space/"))
    FILTER(CONTAINS(LCASE(STR(?specialty)), LCASE("{tag_s}")))
    FILTER(CONTAINS(LCASE(STR(?city)), LCASE("{city_s}")))
  }}
}} LIMIT 10
"""
    try:
        bindings, _ = await sparql_client.run_select(query)
    except Exception as e:
        log.warning("query_commands.find_failed", error=str(e))
        return bernard.query_failed_ack()

    seeded_count = await _count_seeded_in_find(tag_s, city_s)

    if not bindings:
        seeded_note = bernard.seeded_note_ack(seeded_count) if seeded_count > 0 else ""
        return bernard.find_empty_ack(tag=tag, city=city, seeded_note=seeded_note)

    items = _format_space_list(bindings)
    result = bernard.find_results_ack(count=len(bindings), tag=tag, city=city, list_text=items)
    if len(bindings) >= 10:
        result += "\n" + bernard.result_cap_note_ack(n=10)
    if seeded_count > 0:
        result += "\n" + bernard.seeded_note_ack(seeded_count)
    return result


async def _count_seeded_in_find(tag_s: str, city_s: str) -> int:
    """Count seeded (unregistered) spaces matching find criteria."""
    query = PREFIX + f"""
SELECT (COUNT(?s) AS ?count) WHERE {{
  GRAPH ?g {{
    ?s a mom:Space ;
       schema:name ?name ;
       schema:knowsAbout ?specialty .
    OPTIONAL {{ ?s schema:addressLocality ?city }}
    FILTER(STRSTARTS(STR(?g), "urn:mak:space/"))
    FILTER(CONTAINS(LCASE(STR(?specialty)), LCASE("{tag_s}")))
    FILTER(CONTAINS(LCASE(STR(?city)), LCASE("{city_s}")))
    FILTER NOT EXISTS {{ ?s mom:endpointUrl ?e }}
  }}
}}
"""
    try:
        bindings, _ = await sparql_client.run_select(query)
        return int(bindings[0].get("count", {}).get("value", 0)) if bindings else 0
    except Exception:
        return 0


async def nearby(city: str, radius_km: float) -> str:
    """Find spaces within a bounding box around a city."""
    coords = await geocode_city(city)
    if coords is None:
        return f"I couldn't locate '{city}' — check the spelling and try again."

    lat, lon = coords
    delta = radius_km / 111.0
    min_lat, max_lat = lat - delta, lat + delta
    min_lon, max_lon = lon - delta, lon + delta

    query = PREFIX + f"""
SELECT ?name ?lat ?lon ?website WHERE {{
  GRAPH ?g {{
    ?s a mom:Space ;
       schema:name ?name ;
       schema:geo [schema:latitude ?lat ; schema:longitude ?lon] ;
       mom:endpointUrl ?e .
    OPTIONAL {{ ?s schema:url ?website }}
    FILTER(STRSTARTS(STR(?g), "urn:mak:space/"))
    FILTER(?lat >= {min_lat} && ?lat <= {max_lat})
    FILTER(?lon >= {min_lon} && ?lon <= {max_lon})
  }}
}} ORDER BY ?name LIMIT 20
"""
    try:
        bindings, _ = await sparql_client.run_select(query)
    except Exception as e:
        log.warning("query_commands.nearby_failed", error=str(e))
        return bernard.query_failed_ack()

    seeded_count = await _count_seeded_in_bbox(min_lat, max_lat, min_lon, max_lon)

    if not bindings:
        seeded_note = bernard.seeded_note_ack(seeded_count) if seeded_count > 0 else ""
        return bernard.nearby_empty_ack(radius=int(radius_km), city=city, seeded_note=seeded_note)

    items = _format_space_list(bindings)
    result = bernard.nearby_results_ack(radius=int(radius_km), city=city, count=len(bindings), list_text=items)
    if len(bindings) >= 20:
        result += "\n" + bernard.result_cap_note_ack(n=20)
    if seeded_count > 0:
        result += "\n" + bernard.seeded_note_ack(seeded_count)
    return result


async def _count_seeded_in_bbox(min_lat, max_lat, min_lon, max_lon) -> int:
    query = PREFIX + f"""
SELECT (COUNT(?s) AS ?count) WHERE {{
  GRAPH ?g {{
    ?s a mom:Space ;
       schema:geo [schema:latitude ?lat ; schema:longitude ?lon] .
    FILTER(STRSTARTS(STR(?g), "urn:mak:space/"))
    FILTER(?lat >= {min_lat} && ?lat <= {max_lat})
    FILTER(?lon >= {min_lon} && ?lon <= {max_lon})
    FILTER NOT EXISTS {{ ?s mom:endpointUrl ?e }}
  }}
}}
"""
    try:
        bindings, _ = await sparql_client.run_select(query)
        return int(bindings[0].get("count", {}).get("value", 0)) if bindings else 0
    except Exception:
        return 0


async def network(network_name: str) -> str:
    """Find confirmed spaces in a named network."""
    net_s = _sanitize(network_name)
    query = PREFIX + f"""
SELECT ?name ?city ?website WHERE {{
  GRAPH ?g {{
    ?s a mom:Space ;
       schema:name ?name ;
       mom:memberOf ?net ;
       mom:endpointUrl ?e .
    OPTIONAL {{ ?s schema:addressLocality ?city }}
    OPTIONAL {{ ?s schema:url ?website }}
    FILTER(STRSTARTS(STR(?g), "urn:mak:space/"))
    FILTER(CONTAINS(LCASE(STR(?net)), LCASE("{net_s}")))
  }}
}} LIMIT 20
"""
    try:
        bindings, _ = await sparql_client.run_select(query)
    except Exception as e:
        log.warning("query_commands.network_failed", error=str(e))
        return bernard.query_failed_ack()

    seeded_count = await _count_seeded_in_network(net_s)

    if not bindings:
        seeded_note = bernard.seeded_note_ack(seeded_count) if seeded_count > 0 else ""
        return bernard.network_empty_ack(network=network_name) + (f"\n{seeded_note}" if seeded_note else "")

    items = _format_space_list(bindings)
    result = bernard.network_results_ack(network=network_name, count=len(bindings), list_text=items)
    if len(bindings) >= 20:
        result += "\n" + bernard.result_cap_note_ack(n=20)
    if seeded_count > 0:
        result += "\n" + bernard.seeded_note_ack(seeded_count)
    return result


async def _count_seeded_in_network(net_s: str) -> int:
    """Count seeded (unregistered) spaces matching network criteria."""
    query = PREFIX + f"""
SELECT (COUNT(?s) AS ?count) WHERE {{
  GRAPH ?g {{
    ?s a mom:Space ;
       mom:memberOf ?net .
    FILTER(STRSTARTS(STR(?g), "urn:mak:space/"))
    FILTER(CONTAINS(LCASE(STR(?net)), LCASE("{net_s}")))
    FILTER NOT EXISTS {{ ?s mom:endpointUrl ?e }}
  }}
}}
"""
    try:
        bindings, _ = await sparql_client.run_select(query)
        return int(bindings[0].get("count", {}).get("value", 0)) if bindings else 0
    except Exception:
        return 0


def _format_space_list(bindings: list[dict]) -> str:
    lines = []
    for b in bindings:
        name = b.get("name", {}).get("value", "Unknown")
        city = b.get("city", {}).get("value", "")
        website = b.get("website", {}).get("value", "")
        city_part = f" — {city}" if city else ""
        web_part = f" ({website})" if website else ""
        lines.append(f"• {name}{city_part}{web_part}")
    return "\n".join(lines)


async def nearby_from_coords(coords: tuple[float, float], radius_km: float) -> str:
    """Like nearby() but skips geocoding — for use when coords are already resolved."""
    lat, lon = coords
    delta = radius_km / 111.0
    min_lat, max_lat = lat - delta, lat + delta
    min_lon, max_lon = lon - delta, lon + delta

    query = PREFIX + f"""
SELECT ?name ?lat ?lon ?website WHERE {{
  GRAPH ?g {{
    ?s a mom:Space ;
       schema:name ?name ;
       schema:geo [schema:latitude ?lat ; schema:longitude ?lon] ;
       mom:endpointUrl ?e .
    OPTIONAL {{ ?s schema:url ?website }}
    FILTER(STRSTARTS(STR(?g), "urn:mak:space/"))
    FILTER(?lat >= {min_lat} && ?lat <= {max_lat})
    FILTER(?lon >= {min_lon} && ?lon <= {max_lon})
  }}
}} ORDER BY ?name LIMIT 20
"""
    try:
        bindings, _ = await sparql_client.run_select(query)
    except Exception as e:
        log.warning("query_commands.nearby_from_coords_failed", error=str(e))
        return bernard.query_failed_ack()

    if not bindings:
        return bernard.nearby_empty_ack(radius=int(radius_km), city="the origin", seeded_note="")

    items = _format_space_list(bindings)
    result = bernard.nearby_results_ack(radius=int(radius_km), city="the origin", count=len(bindings), list_text=items)
    if len(bindings) >= 20:
        result += "\n" + bernard.result_cap_note_ack(n=20)
    return result


async def dispatch(message, session_id: str) -> str:
    """Dispatch free-text query intent messages (from router.py).
    Currently returns unknown_ack — NL→SPARQL routing in 6.4."""
    log.info("query_commands.dispatch_fallback", session_id=session_id)
    return bernard.unknown_ack()
