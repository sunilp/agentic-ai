"""Tests for PII scrubber."""

import pytest

from src.ch12_memory.scrubber import PIIScrubber


@pytest.fixture
def scrubber() -> PIIScrubber:
    return PIIScrubber()


def test_scrub_credit_card(scrubber: PIIScrubber) -> None:
    text = "Please charge card 4111-1111-1111-1111 for the order."
    result = scrubber.scrub(text)
    assert "4111-1111-1111-1111" not in result
    assert "[REDACTED_CARD]" in result
    assert result == "Please charge card [REDACTED_CARD] for the order."


def test_scrub_email(scrubber: PIIScrubber) -> None:
    text = "Send the receipt to john.doe@example.com please."
    result = scrubber.scrub(text)
    assert "john.doe@example.com" not in result
    assert "[REDACTED_EMAIL]" in result
    assert result == "Send the receipt to [REDACTED_EMAIL] please."


def test_scrub_phone(scrubber: PIIScrubber) -> None:
    text = "Call me at +1-555-123-4567 or 555.123.4567 for details."
    result = scrubber.scrub(text)
    assert "+1-555-123-4567" not in result
    assert "555.123.4567" not in result
    assert result.count("[REDACTED_PHONE]") == 2


def test_scrub_preserves_non_pii(scrubber: PIIScrubber) -> None:
    text = "The quarterly report shows 15% growth in Q3 2025."
    result = scrubber.scrub(text)
    assert result == text


def test_scrub_multiple_types(scrubber: PIIScrubber) -> None:
    text = (
        "User john.doe@example.com paid with 4111-1111-1111-1111 "
        "and left callback number +1-555-123-4567."
    )
    result = scrubber.scrub(text)
    assert "[REDACTED_EMAIL]" in result
    assert "[REDACTED_CARD]" in result
    assert "[REDACTED_PHONE]" in result
    assert "john.doe@example.com" not in result
    assert "4111-1111-1111-1111" not in result
    assert "+1-555-123-4567" not in result
