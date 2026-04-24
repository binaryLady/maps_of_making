"""
Integration tests for ontology loading into Oxigraph.

Tests verify that mom.ttl and iop.ttl are correctly loaded into their
respective named graphs via the load_ontology.sh script.

AC #4: ASK { GRAPH <urn:mak:ontology/mom> { mom:Space a owl:Class } }
AC #5: ASK { GRAPH <urn:mak:ontology/iop> { ?s a owl:Ontology } }
"""

import os

import httpx
import pytest


_base = os.environ.get("OXIGRAPH_ENDPOINT", "http://localhost:7878").rstrip("/")
OXIGRAPH_ENDPOINT = _base if _base.endswith("/query") else _base + "/query"


def sparql_ask(query: str) -> bool:
    """
    Execute a SPARQL ASK query against Oxigraph.

    Args:
        query: SPARQL ASK query string (with required PREFIX declarations)

    Returns:
        Boolean result from ASK query

    Raises:
        httpx.ConnectError: If Oxigraph is unreachable
        httpx.HTTPStatusError: If query execution fails
    """
    try:
        response = httpx.post(
            OXIGRAPH_ENDPOINT,
            content=query,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
            timeout=5.0,
        )
        response.raise_for_status()
        return response.json().get("boolean", False)
    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        pytest.skip(f"Oxigraph unreachable: {e}")


def test_mom_space_loaded():
    """
    AC #4: Verify mom:Space class is loaded in mom ontology graph.

    Tests that the MOM ontology is correctly loaded into the
    <urn:mak:ontology/mom> named graph.
    """
    query = """
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

ASK { GRAPH <urn:mak:ontology/mom> { mom:Space a owl:Class } }
"""
    assert sparql_ask(query), "mom:Space class not found in mom ontology graph"


def test_iop_ontology_loaded():
    """
    AC #5: Verify IoP ontology header is loaded in iop ontology graph.

    Tests that the IoP ontology is correctly loaded into the
    <urn:mak:ontology/iop> named graph with its owl:Ontology declaration.
    """
    query = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>

ASK { GRAPH <urn:mak:ontology/iop> { ?s a owl:Ontology } }
"""
    assert sparql_ask(query), "owl:Ontology not found in iop ontology graph"
