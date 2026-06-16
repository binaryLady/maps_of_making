from openai import AsyncOpenAI
import os
import time
import structlog

log = structlog.get_logger()


DEFAULT_MODEL = "google/gemma-3-12b-it"

# Set from config.yaml bot.model at startup; falls back to DEFAULT_MODEL.
MODEL = DEFAULT_MODEL


async def complete(prompt: str, model: str | None = None, max_tokens: int = 64) -> tuple[str, str, int]:
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
        model=model or MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    latency = int((time.monotonic() - t0) * 1000)
    text = resp.choices[0].message.content or ""
    log.info("llm.completed", model=resp.model, latency_ms=latency)
    return text, resp.model, latency
