import re
from typing import Optional
from urllib.parse import urlparse

MOM = "https://nicolasdb.github.io/mapsofmaking_ontology/ns#"
SCHEMA = "https://schema.org/"

_ALLOWED_SCHEMES = {"http", "https"}


def _sparql_str(s: str) -> str:
    """Escape a string for use in a SPARQL double-quoted literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")


def _sparql_iri(url: str) -> Optional[str]:
    """Validate and return a safe IRI string, or None if invalid."""
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        return None
    if "<" in url or ">" in url or " " in url:
        return None
    return url


def _slug(name: str) -> str:
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', name.lower())).strip('-')
