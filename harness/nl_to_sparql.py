"""NL→SPARQL dispatch for the nl_discovery intent (Story 6.4)."""
import os
import re
import uuid
from datetime import datetime, timezone

import structlog

import bernard
import llm_client
import sparql_client
from message import Message

log = structlog.get_logger()

_ONTOLOGY_CACHE: str | None = None

ONTOLOGY_CONSTRUCT = """
CONSTRUCT {
  ?cls a <http://www.w3.org/2002/07/owl#Class> ;
       <http://www.w3.org/2000/01/rdf-schema#label> ?label ;
       <http://www.w3.org/2000/01/rdf-schema#comment> ?comment .
  ?prop a <http://www.w3.org/2002/07/owl#DatatypeProperty> ;
        <http://www.w3.org/2000/01/rdf-schema#label> ?plabel ;
        <http://www.w3.org/2000/01/rdf-schema#domain> ?domain ;
        <http://www.w3.org/2000/01/rdf-schema#range> ?range .
  ?cls <http://www.w3.org/2004/02/skos/core#closeMatch> ?match .
}
WHERE {
  {
    GRAPH <urn:mak:ontology/iop> {
      { ?cls a <http://www.w3.org/2002/07/owl#Class> .
        OPTIONAL { ?cls <http://www.w3.org/2000/01/rdf-schema#label> ?label }
        OPTIONAL { ?cls <http://www.w3.org/2000/01/rdf-schema#comment> ?comment }
      }
      UNION
      { ?prop a <http://www.w3.org/2002/07/owl#DatatypeProperty> ;
              <http://www.w3.org/2000/01/rdf-schema#domain> ?domain ;
              <http://www.w3.org/2000/01/rdf-schema#range> ?range .
        OPTIONAL { ?prop <http://www.w3.org/2000/01/rdf-schema#label> ?plabel }
      }
      UNION
      { ?cls <http://www.w3.org/2004/02/skos/core#closeMatch> ?match }
    }
  }
  UNION
  {
    GRAPH <urn:mak:ontology/mom> {
      { ?cls a <http://www.w3.org/2002/07/owl#Class> .
        OPTIONAL { ?cls <http://www.w3.org/2000/01/rdf-schema#label> ?label }
      }
      UNION
      { ?prop a <http://www.w3.org/2002/07/owl#DatatypeProperty> ;
              <http://www.w3.org/2000/01/rdf-schema#domain> ?domain .
        OPTIONAL { ?prop <http://www.w3.org/2000/01/rdf-schema#label> ?plabel }
      }
    }
  }
}
"""

FORBIDDEN = re.compile(
    r'\b(DROP|INSERT|DELETE|UPDATE|CLEAR|CREATE|LOAD|MOVE|COPY|ADD)\b',
    re.IGNORECASE,
)

# Sanitize user input going into LLM prompt to prevent prompt injection
_SANITIZE = re.compile(r'[{}<>"\\' + r"\n\r\x00-\x1f]", re.ASCII)

NL_TO_SPARQL_SYSTEM = """You are a SPARQL generator for a makerspace directory.
Available named graphs: urn:mak:space/<slug> (registered spaces), urn:mak:canary/<slug>.
Prefixes:
  PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
  PREFIX schema: <https://schema.org/>
  PREFIX iop: <https://nicolasdb.github.io/mapsofmaking_ontology/iop#>

Ontology context:
{ontology_slice}

Rules:
- Return ONLY a SPARQL SELECT query. No explanation, no markdown.
- Query only the named graphs above. Never use DROP/INSERT/DELETE/UPDATE.
- Limit results to 15 unless the question implies otherwise.
- Use CONTAINS(LCASE(?x), LCASE("term")) for string matching.
"""

GAP_INSERT = """PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT DATA {{
  GRAPH <urn:mak:gaps> {{
    <urn:mak:gap/{gap_id}> a mom:OntologyGap ;
      mom:rawQuery "{raw_query}" ;
      mom:rawLLMOutput "{raw_llm}" ;
      mom:gapTimestamp "{timestamp}"^^xsd:dateTime .
  }}
}}"""


_FENCE_RE = re.compile(r"^```[a-z]*\n?|\n?```$", re.MULTILINE)


def _strip_fence(s: str) -> str:
    return _FENCE_RE.sub("", s).strip()


def _escape_sparql_literal(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("\t", " ")
        .replace("{", "{{")
        .replace("}", "}}")
    )


async def _load_ontology_cache() -> str:
    global _ONTOLOGY_CACHE
    try:
        turtle, _ = await sparql_client.run_construct(ONTOLOGY_CONSTRUCT)
        _ONTOLOGY_CACHE = turtle
        log.info("ontology.cache_loaded", length=len(turtle))
    except Exception as exc:
        log.warning("ontology.cache_load_failed", error=str(exc))
        _ONTOLOGY_CACHE = None  # keep None so next request retries
    return _ONTOLOGY_CACHE or ""


async def _emit_gap_triple(raw_query: str, raw_llm: str) -> None:
    gap_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    sparql = GAP_INSERT.format(
        gap_id=gap_id,
        raw_query=_escape_sparql_literal(raw_query),
        raw_llm=_escape_sparql_literal(raw_llm),
        timestamp=timestamp,
    )
    try:
        await sparql_client.run_update(sparql)
        log.info("gap.written", gap_id=gap_id)
    except Exception as exc:
        log.warning("gap.write_failed", gap_id=gap_id, error=str(exc))


async def dispatch(message: Message, session_id: str = "") -> str:
    global _ONTOLOGY_CACHE

    # Load or refresh ontology cache
    if _ONTOLOGY_CACHE is None or os.environ.get("RELOAD_ONTOLOGY") == "1":
        await _load_ontology_cache()

    if not _ONTOLOGY_CACHE:
        log.warning("ontology.cache_unavailable", session_id=session_id)
        await _emit_gap_triple(message.text, "ontology cache unavailable")
        return bernard.nl_gap_ack()

    safe_text = _SANITIZE.sub(" ", message.text)

    # Generate SPARQL via LLM
    try:
        raw, _, _ = await llm_client.complete_with_system(
            system=NL_TO_SPARQL_SYSTEM.format(ontology_slice=_ONTOLOGY_CACHE),
            user=safe_text,
            model="anthropic/claude-sonnet-4-5",
            temperature=0.0,
            max_tokens=512,
            session_id=session_id,
        )
        sparql = _strip_fence(raw)
        log.info("sparql.generated", session_id=session_id)
    except Exception as exc:
        log.warning("llm.nl_sparql_failed", error=str(exc), session_id=session_id)
        await _emit_gap_triple(message.text, "LLM error: " + str(exc))
        return bernard.nl_gap_ack()

    # Security: reject mutating statements
    if FORBIDDEN.search(sparql):
        log.warning(
            "sparql.security_rejected",
            session_id=session_id,
            sparql_preview=sparql[:120],
        )
        return bernard.nl_invalid_sparql_ack()

    # Execute query
    try:
        bindings, _ = await sparql_client.run_select(sparql)
    except Exception as exc:
        log.warning("sparql.nl_select_failed", error=str(exc), session_id=session_id)
        await _emit_gap_triple(message.text, sparql)
        return bernard.nl_gap_ack()

    if not bindings:
        await _emit_gap_triple(message.text, sparql)
        return bernard.nl_empty_ack()

    # Format results
    def _val(row: dict, *keys: str) -> str:
        for k in keys:
            v = row.get(k)
            if isinstance(v, dict):
                return v.get("value", "") or ""
        return ""

    displayed = bindings[:15]
    lines = []
    for row in displayed:
        name = _val(row, "name")
        url = _val(row, "url", "website")
        if name and url:
            lines.append(f"• [{name}]({url})")
        elif name:
            lines.append(f"• {name}")
        else:
            first_val = _val(row, *row.keys())
            lines.append(f"• {first_val}")

    total = len(bindings)
    count_label = f"{len(displayed)} of {total}" if total > len(displayed) else str(total)
    list_text = "\n".join(lines)
    return bernard.nl_result_ack(count=count_label, list_text=list_text, sparql_block=sparql)
