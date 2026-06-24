"""Tests for nl_to_sparql.py (Story 6.4)."""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "infra" / "link_handler"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "infra"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import bernard
import nl_to_sparql
import sparql_client
import llm_client
from message import Message


@pytest.fixture(autouse=True)
def _voice():
    bernard.load_voice()


@pytest.fixture(autouse=True)
def _reset_cache():
    nl_to_sparql._ONTOLOGY_CACHE = None
    yield
    nl_to_sparql._ONTOLOGY_CACHE = None


def _msg(text: str = "makerspaces in Brussels with laser cutters") -> Message:
    return Message(text=text, user_id="@u:x", room_id="!room:x", platform="matrix", raw=None, power_level=0)


VALID_SPARQL = """SELECT ?name ?url WHERE {
  GRAPH ?g { ?s <https://schema.org/name> ?name ; <https://schema.org/url> ?url }
} LIMIT 15"""

BINDINGS_2 = [
    {"name": {"value": "OpenFab"}, "url": {"value": "https://openfab.be"}},
    {"name": {"value": "Fablab Brussels"}, "url": {"value": "https://fablab.brussels"}},
]


@pytest.mark.asyncio
async def test_sparql_injection_rejected(monkeypatch):
    """LLM returns a mutating statement → rejected before Oxigraph call."""
    monkeypatch.setattr(
        sparql_client, "run_construct",
        AsyncMock(return_value=("# ontology", 5)),
    )
    monkeypatch.setattr(
        llm_client, "complete_with_system",
        AsyncMock(return_value=("DROP GRAPH <urn:mak:space/test>; SELECT * WHERE {}", "m", 100)),
    )
    run_select_mock = AsyncMock()
    run_update_mock = AsyncMock(return_value=(True, 5))
    monkeypatch.setattr(sparql_client, "run_select", run_select_mock)
    monkeypatch.setattr(sparql_client, "run_update", run_update_mock)

    result = await nl_to_sparql.dispatch(_msg())

    assert result == bernard.nl_invalid_sparql_ack()
    run_select_mock.assert_not_called()
    run_update_mock.assert_not_called()


@pytest.mark.asyncio
async def test_empty_result_emits_gap_triple(monkeypatch):
    """Valid SPARQL, empty result → gap triple written, nl_gap_ack returned."""
    monkeypatch.setattr(sparql_client, "run_construct", AsyncMock(return_value=("# ontology", 5)))
    monkeypatch.setattr(
        llm_client, "complete_with_system",
        AsyncMock(return_value=(VALID_SPARQL, "m", 100)),
    )
    monkeypatch.setattr(sparql_client, "run_select", AsyncMock(return_value=([], 10)))
    run_update_mock = AsyncMock(return_value=(True, 5))
    monkeypatch.setattr(sparql_client, "run_update", run_update_mock)

    result = await nl_to_sparql.dispatch(_msg())

    assert result == bernard.nl_empty_ack()
    run_update_mock.assert_called_once()
    call_args = run_update_mock.call_args[0][0]
    assert "mom:OntologyGap" in call_args
    assert "urn:mak:gaps" in call_args


@pytest.mark.asyncio
async def test_successful_result_formatted(monkeypatch):
    """run_select returns 2 bindings → formatted response with space names and SPARQL block."""
    monkeypatch.setattr(sparql_client, "run_construct", AsyncMock(return_value=("# ontology", 5)))
    monkeypatch.setattr(
        llm_client, "complete_with_system",
        AsyncMock(return_value=(VALID_SPARQL, "m", 100)),
    )
    monkeypatch.setattr(sparql_client, "run_select", AsyncMock(return_value=(BINDINGS_2, 10)))

    result = await nl_to_sparql.dispatch(_msg())

    assert "OpenFab" in result
    assert "Fablab Brussels" in result
    assert "How I searched" in result


@pytest.mark.asyncio
async def test_llm_failure_emits_gap_triple(monkeypatch):
    """LLM raises → gap triple written, nl_gap_ack returned."""
    monkeypatch.setattr(sparql_client, "run_construct", AsyncMock(return_value=("# ontology", 5)))
    monkeypatch.setattr(
        llm_client, "complete_with_system",
        AsyncMock(side_effect=RuntimeError("OpenRouter timeout")),
    )
    run_update_mock = AsyncMock(return_value=(True, 5))
    monkeypatch.setattr(sparql_client, "run_update", run_update_mock)

    result = await nl_to_sparql.dispatch(_msg())

    assert result == bernard.nl_gap_ack()
    run_update_mock.assert_called_once()


@pytest.mark.asyncio
async def test_ontology_cache_hit(monkeypatch):
    """Second dispatch call reuses cache — run_construct called only once."""
    run_construct_mock = AsyncMock(return_value=("# ontology", 5))
    monkeypatch.setattr(sparql_client, "run_construct", run_construct_mock)
    monkeypatch.setattr(
        llm_client, "complete_with_system",
        AsyncMock(return_value=(VALID_SPARQL, "m", 100)),
    )
    monkeypatch.setattr(sparql_client, "run_select", AsyncMock(return_value=(BINDINGS_2, 10)))

    await nl_to_sparql.dispatch(_msg())
    await nl_to_sparql.dispatch(_msg())

    run_construct_mock.assert_called_once()


@pytest.mark.asyncio
async def test_reload_ontology_env_refetches(monkeypatch):
    """RELOAD_ONTOLOGY=1 forces run_construct on every dispatch call."""
    run_construct_mock = AsyncMock(return_value=("# ontology", 5))
    monkeypatch.setattr(sparql_client, "run_construct", run_construct_mock)
    monkeypatch.setattr(
        llm_client, "complete_with_system",
        AsyncMock(return_value=(VALID_SPARQL, "m", 100)),
    )
    monkeypatch.setattr(sparql_client, "run_select", AsyncMock(return_value=(BINDINGS_2, 10)))
    monkeypatch.setenv("RELOAD_ONTOLOGY", "1")

    await nl_to_sparql.dispatch(_msg())
    await nl_to_sparql.dispatch(_msg())

    assert run_construct_mock.call_count == 2
