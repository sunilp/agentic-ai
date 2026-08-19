"""Diminishing-returns detection.

Counts how many words in each step's output have not appeared in any previous
step. When the ratio of new words to total words falls below the threshold,
the step is stale: it cost a full model call and added nothing.

The gain curve is worth keeping. If it flattens after step 2 and your budget
is 5, you are paying for three steps you do not need.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

STOP_WORDS = frozenset(
    """a an and are as at be by for from has have in is it its of on or that the
    this to was were will with""".split()
)


def record_step(seen_content: set[str], new_content: str, threshold: float = 0.1):
    """The version printed in the book -- state passed in, tuple returned."""
    words = set(new_content.lower().split())
    new_words = words - seen_content
    gain = len(new_words) / len(words) if words else 0.0
    seen_content.update(words)
    return gain, gain < threshold  # (gain_value, is_stale)


class StepGain(BaseModel):
    """Marginal information gain for a single step."""

    step: int
    gain: float
    is_stale: bool
    new_words: int
    total_words: int


class ProgressTracker:
    """Stateful wrapper around `record_step` that keeps the gain curve."""

    def __init__(self, threshold: float = 0.1, ignore_stop_words: bool = True) -> None:
        self.threshold = threshold
        self.ignore_stop_words = ignore_stop_words
        self.seen: set[str] = set()
        self.gains: list[StepGain] = []

    def reset(self) -> None:
        self.seen.clear()
        self.gains.clear()

    def _tokenize(self, content: str) -> set[str]:
        words = {w.strip(".,;:!?()[]\"'") for w in content.lower().split()}
        words.discard("")
        if self.ignore_stop_words:
            words -= STOP_WORDS
        return words

    def record(self, content: str) -> StepGain:
        words = self._tokenize(content)
        new_words = words - self.seen
        gain = len(new_words) / len(words) if words else 0.0
        self.seen.update(words)
        entry = StepGain(
            step=len(self.gains) + 1,
            gain=gain,
            is_stale=gain < self.threshold,
            new_words=len(new_words),
            total_words=len(words),
        )
        self.gains.append(entry)
        return entry

    @property
    def total_gain_curve(self) -> list[float]:
        return [g.gain for g in self.gains]

    @property
    def last_gain(self) -> float:
        return self.gains[-1].gain if self.gains else 1.0

    def is_stale(self, window: int = 1) -> bool:
        """True when the last `window` steps all fell below the threshold."""
        if len(self.gains) < window:
            return False
        return all(g.is_stale for g in self.gains[-window:])

    def suggested_step_budget(self) -> int:
        """The step after which the curve flattened -- calibrate your budget here."""
        for entry in self.gains:
            if entry.is_stale:
                return max(1, entry.step - 1)
        return len(self.gains)


class GainCurve(BaseModel):
    """Serializable view of a tracker, for logging alongside a trace."""

    threshold: float
    gains: list[StepGain] = Field(default_factory=list)

    @classmethod
    def from_tracker(cls, tracker: ProgressTracker) -> GainCurve:
        return cls(threshold=tracker.threshold, gains=list(tracker.gains))
