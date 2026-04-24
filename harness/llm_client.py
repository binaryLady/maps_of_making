from openai import AsyncOpenAI
import os
import time
import structlog

log = structlog.get_logger()


async def complete(prompt: str) -> tuple[str, str, int]:
    """One LLM completion via OpenRouter. Returns (text, model_used, latency_ms)."""
    client = AsyncOpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://mapofmaking.debarquin.eu",
            "X-Title": "maps-of-making spike",
        },
    )
    t0 = time.monotonic()
    resp = await client.chat.completions.create(
        model="anthropic/claude-haiku-4-5",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=64,
    )
    latency = int((time.monotonic() - t0) * 1000)
    text = resp.choices[0].message.content or ""
    return text, resp.model, latency
