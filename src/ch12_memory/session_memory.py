"""Session memory with pluggable truncation strategies.

Manages the sliding context window that an agent presents to its LLM on each
turn.  When accumulated messages exceed the token budget, a configurable
truncation strategy decides what to keep, summarise, or drop.

Three strategies ship out of the box:

* **RecencyStrategy** -- keeps the newest messages, drops the oldest.
* **ImportanceStrategy** -- scores messages by heuristic signals (numbers,
  questions, back-references) and drops the least valuable first.
* **CompactionStrategy** -- summarises the oldest portion of the conversation
  into a single system message via an injectable summarise function.
"""

from __future__ import annotations

import json
import math
import re
from abc import ABC, abstractmethod
from collections.abc import Callable

from src.ch12_memory.scrubber import PIIScrubber

# Per-message overhead in tokens: accounts for role tags, control tokens
# (<|im_start|>, <|im_end|>), and message separators that real LLM APIs
# charge for but that are absent from the raw content string.
_MESSAGE_OVERHEAD = 8


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 characters per token."""
    return max(1, len(text) // 4)


def _message_tokens(message: dict[str, str]) -> int:
    """Estimate the token cost of a full chat message.

    Real tokenisers charge for the serialised message structure -- role tags,
    control tokens, and separators -- not just the content string.  We
    approximate by running :func:`_estimate_tokens` over the compact JSON
    representation and adding a fixed overhead for control tokens.
    """
    return _estimate_tokens(json.dumps(message, separators=(",", ":"))) + _MESSAGE_OVERHEAD


# ---------------------------------------------------------------------------
# Truncation strategies
# ---------------------------------------------------------------------------

class TruncationStrategy(ABC):
    """Base class for context-window truncation strategies."""

    @abstractmethod
    def truncate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
    ) -> list[dict[str, str]]:
        """Return a subset (or transformation) of *messages* that fits
        within *max_tokens*."""


class RecencyStrategy(TruncationStrategy):
    """Keep the most recent messages, dropping the oldest first."""

    def truncate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
    ) -> list[dict[str, str]]:
        result = list(messages)
        while result and self._total_tokens(result) > max_tokens:
            result.pop(0)
        return result

    @staticmethod
    def _total_tokens(messages: list[dict[str, str]]) -> int:
        return sum(_message_tokens(m) for m in messages)


class ImportanceStrategy(TruncationStrategy):
    """Score messages by heuristic signals, drop the least important first.

    Scoring rules (no LLM call):
    - Presence of numbers, dates, account IDs, monetary amounts
    - Question marks (likely user queries worth preserving)
    - Back-references to earlier context
    - Length bonus (longer messages tend to carry more substance)
    """

    def score(self, message: dict[str, str]) -> float:
        content = message.get("content", "")
        total = 0.0

        # Numbers, dates, account IDs, monetary values
        numeric_hits = re.findall(
            r"\$[\d,.]+|\d{4}-\d{2}-\d{2}|#\d+|\b\d{5,}\b",
            content,
        )
        total += len(numeric_hits) * 2.0

        # Question marks signal queries worth keeping
        total += content.count("?") * 1.5

        # Back-references to earlier context
        refs = re.findall(
            r"\b(earlier|original|you said|I mentioned|previously)\b",
            content,
            re.I,
        )
        total += len(refs) * 1.5

        # Length bonus -- capped at 3.0
        total += min(len(content) / 200, 3.0)

        return total

    def truncate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
    ) -> list[dict[str, str]]:
        # Build index-score pairs so we can remove lowest first
        # while preserving original order of survivors.
        indexed = list(enumerate(messages))
        indexed.sort(key=lambda pair: self.score(pair[1]))

        # Greedily remove the lowest-scoring messages until under budget
        removed: set[int] = set()
        current_tokens = sum(_message_tokens(m) for m in messages)

        for idx, msg in indexed:
            if current_tokens <= max_tokens:
                break
            removed.add(idx)
            current_tokens -= _message_tokens(msg)

        # Preserve original order
        return [m for i, m in enumerate(messages) if i not in removed]


class CompactionStrategy(TruncationStrategy):
    """Summarise older messages via an injectable function, keeping recent ones.

    The caller supplies a *summarize_fn* that accepts a list of messages and
    returns a plain-text summary.  When truncation fires, the oldest 2/3 of
    the conversation is summarised into a single ``[Session summary]`` system
    message, and the most recent 1/3 is kept verbatim.
    """

    def __init__(self, summarize_fn: Callable[[list[dict[str, str]]], str]) -> None:
        self._summarize = summarize_fn

    def truncate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
    ) -> list[dict[str, str]]:
        keep_count = max(1, math.ceil(len(messages) / 3))
        old_messages = messages[:-keep_count]
        recent_messages = messages[-keep_count:]

        summary_text = self._summarize(old_messages)
        summary_msg: dict[str, str] = {
            "role": "system",
            "content": f"[Session summary] {summary_text}",
        }

        return [summary_msg] + recent_messages


# ---------------------------------------------------------------------------
# SessionMemory
# ---------------------------------------------------------------------------

class SessionMemory:
    """Sliding-window conversation memory with optional PII scrubbing.

    Parameters
    ----------
    max_tokens:
        Token budget for the context returned by :meth:`get_context`.
    strategy:
        Truncation strategy to apply when the budget is exceeded.
        Defaults to :class:`RecencyStrategy`.
    scrub_pii:
        When ``True``, every message is run through :class:`PIIScrubber`
        before it is stored.
    """

    def __init__(
        self,
        max_tokens: int,
        strategy: TruncationStrategy | None = None,
        scrub_pii: bool = False,
    ) -> None:
        self._max_tokens = max_tokens
        self._strategy = strategy or RecencyStrategy()
        self._messages: list[dict[str, str]] = []
        self._scrubber: PIIScrubber | None = PIIScrubber() if scrub_pii else None

    # -- public API ---------------------------------------------------------

    def add_message(self, message: dict[str, str]) -> None:
        """Append a message, scrubbing PII first if enabled."""
        if self._scrubber:
            message = {
                **message,
                "content": self._scrubber.scrub(message["content"]),
            }
        self._messages.append(message)

    def get_context(self) -> list[dict[str, str]]:
        """Return messages that fit within the token budget.

        If the raw conversation is under budget, all messages are returned
        unchanged. Otherwise the configured truncation strategy decides what
        to keep.
        """
        if not self._messages:
            return []
        if self.estimated_tokens <= self._max_tokens:
            return list(self._messages)
        return self._strategy.truncate(list(self._messages), self._max_tokens)

    # -- properties ---------------------------------------------------------

    @property
    def estimated_tokens(self) -> int:
        """Sum of rough token estimates across all stored messages."""
        return sum(_message_tokens(m) for m in self._messages)

    @property
    def message_count(self) -> int:
        """Number of messages currently held."""
        return len(self._messages)
