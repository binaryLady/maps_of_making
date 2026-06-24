import httpx
import time
import structlog

log = structlog.get_logger()

OXIGRAPH_ENDPOINT = ""  # set from env in main.py

HEALTH_ASK = """ASK { ?s ?p ?o }"""


async def run_select(query: str) -> tuple[list[dict], int]:
    """Run a SPARQL SELECT query. Returns (list_of_binding_dicts, latency_ms).
    Each binding dict maps variable name → {"type": ..., "value": ...}.
    Returns empty list on error (caller decides fallback)."""
    t0 = time.monotonic()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{OXIGRAPH_ENDPOINT}/query",
            content=query,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
            timeout=httpx.Timeout(15.0, connect=5.0),
        )
        resp.raise_for_status()
    latency = int((time.monotonic() - t0) * 1000)
    bindings = resp.json().get("results", {}).get("bindings", [])
    if len(bindings) > 500:
        log.warning("sparql.select_large_result", count=len(bindings))
    log.info("sparql.select_completed", count=len(bindings), latency_ms=latency)
    return bindings, latency


async def run_ask(query: str) -> tuple[bool, int]:
    """Run a SPARQL ASK query. Returns (boolean_result, latency_ms)."""
    t0 = time.monotonic()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{OXIGRAPH_ENDPOINT}/query",
            content=query,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
            timeout=httpx.Timeout(10.0, connect=5.0),
        )
        resp.raise_for_status()
    latency = int((time.monotonic() - t0) * 1000)
    result = resp.json().get("boolean", False)
    log.info("sparql.completed", result=result, latency_ms=latency)
    return result, latency


async def run_construct(query: str) -> tuple[str, int]:
    """Run a SPARQL CONSTRUCT query. Returns (turtle_text, latency_ms)."""
    t0 = time.monotonic()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{OXIGRAPH_ENDPOINT}/query",
            content=query,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "text/turtle",
            },
            timeout=httpx.Timeout(15.0, connect=5.0),
        )
        resp.raise_for_status()
    latency = int((time.monotonic() - t0) * 1000)
    log.info("sparql.construct_completed", latency_ms=latency)
    return resp.text, latency


async def run_update(update: str) -> tuple[bool, int]:
    """Run a SPARQL UPDATE via /update endpoint (internal Docker URL only).
    Returns (success, latency_ms). Oxigraph /update is nginx-blocked from public internet."""
    t0 = time.monotonic()
    update_url = OXIGRAPH_ENDPOINT.rstrip("/") + "/update"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            update_url,
            content=update,
            headers={"Content-Type": "application/sparql-update"},
            timeout=httpx.Timeout(15.0, connect=5.0),
        )
        resp.raise_for_status()
    latency = int((time.monotonic() - t0) * 1000)
    log.info("sparql.update_completed", latency_ms=latency)
    return True, latency
