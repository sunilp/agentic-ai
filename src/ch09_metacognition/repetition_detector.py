"""Loop detection for agent execution.

Four layers, cheapest first:

1. Exact match on (tool, arguments) -- catches the most expensive pattern.
2. Action-sequence fingerprinting -- catches A/B alternation without progress.
3. Semantic similarity between consecutive reasoning traces -- catches the
   same question asked in different words.
4. Output convergence -- the proposed answer has stopped changing.

Layers 1 and 2 are pure hashing and run by default at near-zero cost.
Layers 3 and 4 need an embedding function or answer text and only pay for
themselves on agents running five or more steps.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Sequence
from typing import Any

from pydantic import BaseModel, Field


def is_looping(history: Sequence[Any], threshold: int = 2) -> bool:
    """Layer 1 in its smallest form -- the version printed in the book."""
    if len(history) < threshold:
        return False
    recent = history[-threshold:]
    return len(set(recent)) == 1  # all identical


class StepRecord(BaseModel):
    """One observed agent step, as seen by the detector."""

    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    observation: str = ""
    reasoning: str = ""
    answer: str = ""


class RepetitionVerdict(BaseModel):
    """Why the detector did or did not flag a loop."""

    is_looping: bool = False
    layer: str | None = None
    detail: str = ""


def fingerprint(tool: str, arguments: dict[str, Any]) -> str:
    """Stable hash of a tool call. Argument order must not matter."""
    payload = json.dumps({"tool": tool, "args": arguments}, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode()).hexdigest()[:12]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def _normalize_answer(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


class RepetitionDetector:
    """Layered loop detection over a running agent.

    Feed every step to `record`. The returned verdict names the layer that
    fired, which is what you want in a trace when you are explaining a
    terminated run to somebody at 3 AM.
    """

    def __init__(
        self,
        exact_threshold: int = 2,
        sequence_length: int = 2,
        similarity_threshold: float = 0.93,
        convergence_window: int = 2,
        embed: Callable[[str], Sequence[float]] | None = None,
    ) -> None:
        self.exact_threshold = exact_threshold
        self.sequence_length = sequence_length
        self.similarity_threshold = similarity_threshold
        self.convergence_window = convergence_window
        self.embed = embed
        self.steps: list[StepRecord] = []
        self.fingerprints: list[str] = []

    def reset(self) -> None:
        self.steps.clear()
        self.fingerprints.clear()

    def record(self, step: StepRecord) -> RepetitionVerdict:
        self.steps.append(step)
        self.fingerprints.append(fingerprint(step.tool, step.arguments))
        return self.check()

    def check(self) -> RepetitionVerdict:
        for layer in (
            self._exact_match,
            self._sequence_match,
            self._semantic_match,
            self._output_convergence,
        ):
            verdict = layer()
            if verdict.is_looping:
                return verdict
        return RepetitionVerdict(detail="no repetition detected")

    def _exact_match(self) -> RepetitionVerdict:
        if is_looping(self.fingerprints, self.exact_threshold):
            return RepetitionVerdict(
                is_looping=True,
                layer="exact_match",
                detail=f"last {self.exact_threshold} tool calls identical",
            )
        return RepetitionVerdict()

    def _sequence_match(self) -> RepetitionVerdict:
        n = self.sequence_length
        if len(self.fingerprints) < 2 * n:
            return RepetitionVerdict()
        tail = self.fingerprints[-2 * n :]
        if tail[:n] == tail[n:] and len(set(tail)) > 1:
            return RepetitionVerdict(
                is_looping=True,
                layer="sequence_fingerprint",
                detail=f"{n}-step action sequence repeated without progress",
            )
        return RepetitionVerdict()

    def _semantic_match(self) -> RepetitionVerdict:
        if self.embed is None or len(self.steps) < 2:
            return RepetitionVerdict()
        previous, current = self.steps[-2].reasoning, self.steps[-1].reasoning
        if not previous or not current:
            return RepetitionVerdict()
        similarity = cosine_similarity(self.embed(previous), self.embed(current))
        if similarity >= self.similarity_threshold:
            return RepetitionVerdict(
                is_looping=True,
                layer="semantic_similarity",
                detail=f"consecutive reasoning similarity {similarity:.3f}",
            )
        return RepetitionVerdict()

    def _output_convergence(self) -> RepetitionVerdict:
        window = self.convergence_window + 1
        answers = [s.answer for s in self.steps[-window:] if s.answer]
        if len(answers) < window:
            return RepetitionVerdict()
        if len({_normalize_answer(a) for a in answers}) == 1:
            return RepetitionVerdict(
                is_looping=True,
                layer="output_convergence",
                detail=f"answer unchanged across {window} steps",
            )
        return RepetitionVerdict()
