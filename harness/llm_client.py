from openai import AsyncOpenAI
import os
import time
import structlog

log = structlog.get_logger()


async def complete(prompt: str) -> tuple[str, str, int]:
    """One LLM completion via OpenRouter. Returns (text, model_used, latency_ms)."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set in .env or environment")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://mapsofmaking.org",
            "X-Title": "maps-of-making spike",
        },
    )
    t0 = time.monotonic()
    resp = await client.chat.completions.create(
        model="minimax/minimax-m2.1",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=64,
    )
    latency = int((time.monotonic() - t0) * 1000)
    text = resp.choices[0].message.content or ""
    log.info("llm.completed", model=resp.model, latency_ms=latency)
    return text, resp.model, latency
