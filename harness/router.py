import structlog

import bernard
import intent_classifier
import nl_to_sparql
import query_commands
from message import Message

log = structlog.get_logger()


async def route(message: Message, session_id: str) -> str:
    """Classify the message and dispatch to the matching skill."""
    intent = await intent_classifier.classify(message.text, session_id=session_id)

    if intent == "unknown":
        return bernard.unknown_ack()

    if intent == "query":
        return await query_commands.dispatch(message, session_id=session_id)

    if intent == "nl_discovery":
        return await nl_to_sparql.dispatch(message, session_id=session_id)

    # write: not implemented yet
    log.warning("router.intent_not_implemented", intent=intent, session_id=session_id)
    return bernard.unknown_ack()
