import httpx
import time
import structlog

log = structlog.get_logger()

OXIGRAPH_ENDPOINT = ""  # set from env in main.py

HEALTH_ASK = """ASK { ?s ?p ?o }"""


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
            timeout=httpx.Timeout(connect=5.0, read=10.0),
        )
        resp.raise_for_status()
    latency = int((time.monotonic() - t0) * 1000)
    result = resp.json().get("boolean", False)
    log.info("sparql.completed", result=result, latency_ms=latency)
    return result, latency
