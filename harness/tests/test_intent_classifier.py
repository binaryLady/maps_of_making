import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import intent_classifier
import llm_client


@pytest.mark.asyncio
@pytest.mark.parametrize("raw_reply,expected", [
    ("write", "write"),
    ("query", "query"),
    ("nl_discovery", "nl_discovery"),
    ("unknown", "unknown"),
    ("Write.", "unknown"),       # punctuation/casing drift outside the exact token set
    ("I don't know", "unknown"),  # garbage/refusal output
    ("", "unknown"),              # empty completion
])
async def test_classify_always_returns_one_of_four_intents(monkeypatch, raw_reply, expected):
    async def fake_complete(prompt, model=None, max_tokens=64, session_id=""):
        return raw_reply, "fake-model", 1

    monkeypatch.setattr(llm_client, "complete", fake_complete)
    result = await intent_classifier.classify("some message", session_id="test-session")
    assert result == expected
    assert result in intent_classifier.INTENTS
