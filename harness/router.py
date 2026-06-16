import structlog

import bernard
import intent_classifier
from message import Message

log = structlog.get_logger()


async def route(message: Message, session_id: str) -> str:
    """Classify the message and dispatch to the matching skill. Only the
    `unknown` path (the !mom ping smoke test) resolves to a real skill in
    this story — write/query/nl_discovery skills land in 6.1-6.4."""
    intent = await intent_classifier.classify(message.text, session_id=session_id)

    if intent == "unknown":
        return bernard.unknown_ack()

    # write | query | nl_discovery: skills not implemented yet (6.1-6.4).
    log.warning("router.intent_not_implemented", intent=intent, session_id=session_id)
    return bernard.unknown_ack()
