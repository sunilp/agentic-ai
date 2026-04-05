"""Tests for session memory and truncation strategies."""

from src.ch12_memory.session_memory import (
    CompactionStrategy,
    ImportanceStrategy,
    RecencyStrategy,
    SessionMemory,
)


def test_add_and_get_messages():
    sm = SessionMemory(max_tokens=10000)
    sm.add_message({"role": "user", "content": "Hello"})
    sm.add_message({"role": "assistant", "content": "Hi there"})
    msgs = sm.get_context()
    assert len(msgs) == 2


def test_recency_truncation_drops_oldest():
    sm = SessionMemory(max_tokens=100, strategy=RecencyStrategy())
    sm.add_message({"role": "user", "content": "First message with important context " * 5})
    sm.add_message({"role": "assistant", "content": "Response " * 5})
    sm.add_message({"role": "user", "content": "Second question"})
    msgs = sm.get_context()
    assert all("First message" not in m["content"] for m in msgs)
    assert any("Second question" in m["content"] for m in msgs)


def test_importance_truncation_keeps_high_value():
    sm = SessionMemory(max_tokens=100, strategy=ImportanceStrategy())
    sm.add_message(
        {
            "role": "user",
            "content": "My account #12345 was charged $187.43 on 2026-03-15 incorrectly",
        }
    )
    sm.add_message({"role": "assistant", "content": "I understand, let me look into that"})
    sm.add_message({"role": "user", "content": "Thanks"})
    sm.add_message({"role": "assistant", "content": "Sure thing"})
    sm.add_message({"role": "user", "content": "What is the status of my refund?"})
    msgs = sm.get_context()
    contents = " ".join(m["content"] for m in msgs)
    assert "$187.43" in contents or "#12345" in contents


def test_compaction_summarizes_old_messages():
    def mock_summarize(messages):
        return f"Summary of {len(messages)} messages"

    sm = SessionMemory(max_tokens=100, strategy=CompactionStrategy(summarize_fn=mock_summarize))
    for i in range(10):
        sm.add_message({"role": "user", "content": f"Message {i} with some content padding text"})
    msgs = sm.get_context()
    contents = " ".join(m["content"] for m in msgs)
    assert "Summary of" in contents


def test_scrubbing_runs_before_storage():
    sm = SessionMemory(max_tokens=10000, scrub_pii=True)
    sm.add_message({"role": "user", "content": "My card is 4111-1111-1111-1111"})
    msgs = sm.get_context()
    contents = " ".join(m["content"] for m in msgs)
    assert "4111" not in contents
    assert "[REDACTED_CARD]" in contents


def test_token_estimate():
    sm = SessionMemory(max_tokens=10000)
    sm.add_message({"role": "user", "content": "Hello world"})
    assert sm.estimated_tokens > 0


def test_empty_session():
    sm = SessionMemory(max_tokens=10000)
    assert sm.get_context() == []


def test_message_count():
    sm = SessionMemory(max_tokens=10000)
    sm.add_message({"role": "user", "content": "One"})
    sm.add_message({"role": "assistant", "content": "Two"})
    sm.add_message({"role": "user", "content": "Three"})
    assert sm.message_count == 3
