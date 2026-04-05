"""PII scrubber for session memory.

Applies regex-based redaction to strip personally identifiable information
from text before it enters long-term memory stores. This is a defence-in-depth
measure -- not a substitute for access controls or encryption, but a practical
way to reduce PII surface area in agent conversation logs.
"""

from __future__ import annotations

import re
from typing import List, Tuple


class PIIScrubber:
    """Regex-based PII redactor.

    Ships with patterns for credit cards, emails, phone numbers, and SSNs.
    Callers can extend coverage via *extra_patterns* at init time.

    Example::

        scrubber = PIIScrubber()
        clean = scrubber.scrub("Email me at alice@corp.com")
        # => "Email me at [REDACTED_EMAIL]"
    """

    # Each tuple is (raw_pattern, replacement_token).
    # Order matters: more specific patterns (credit cards with separators)
    # should appear before broader numeric patterns.
    PATTERNS: List[Tuple[str, str]] = [
        # Credit card numbers — with dashes, spaces, or no separators
        # Covers 13-19 digit card numbers (Visa, MC, Amex, Discover, etc.)
        (
            r"\b(?:\d[ -]*?){13,19}\b",
            "[REDACTED_CARD]",
        ),
        # SSN — XXX-XX-XXXX
        (
            r"\b\d{3}-\d{2}-\d{4}\b",
            "[REDACTED_SSN]",
        ),
        # Email addresses
        (
            r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            "[REDACTED_EMAIL]",
        ),
        # Phone — international prefix optional, separators vary
        # Matches: +1-555-123-4567, 555.123.4567, (555) 123-4567, 555-123-4567
        (
            r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b",
            "[REDACTED_PHONE]",
        ),
    ]

    def __init__(
        self,
        extra_patterns: List[Tuple[str, str]] | None = None,
    ) -> None:
        raw = list(self.PATTERNS)
        if extra_patterns:
            raw.extend(extra_patterns)
        self._compiled: List[Tuple[re.Pattern[str], str]] = [
            (re.compile(pat), repl) for pat, repl in raw
        ]

    def scrub(self, text: str) -> str:
        """Return *text* with all recognised PII patterns replaced."""
        for pattern, replacement in self._compiled:
            text = pattern.sub(replacement, text)
        return text
