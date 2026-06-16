import structlog

import llm_client

log = structlog.get_logger()

INTENTS = ("write", "query", "nl_discovery", "unknown")

CLASSIFIER_PROMPT = """You are an intent classifier for a bot that manages a directory of \
makerspaces. Classify the user's message into exactly one of these intents:

- write: the user wants to register, update, or change a space's listing.
- query: the user wants to look up known facts about a specific space (hours, location, etc).
- nl_discovery: the user wants to find/discover spaces matching some criteria.
- unknown: anything else, including greetings, smoke tests, or unclear requests.

Reply with exactly one word: write, query, nl_discovery, or unknown. No punctuation, no \
explanation.

Message: {text}"""


async def classify(text: str, session_id: str = "") -> str:
    """Classify a message into one of INTENTS via one compact LLM call."""
    bound = log.bind(session_id=session_id)
    prompt = CLASSIFIER_PROMPT.format(text=text)
    raw_text, model, latency_ms = await llm_client.complete(prompt, session_id=session_id)
    intent = raw_text.strip().lower()
    if intent not in INTENTS:
        intent = "unknown"
    bound.info("intent.classified", intent=intent, model=model, latency_ms=latency_ms)
    return intent
