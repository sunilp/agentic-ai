"""The MetacognitiveMonitor and the budget tracker it consults.

The monitor combines the detectors into one `StepAssessment` per step. It is a
composition of simple parts: each detector is independently testable, and
adding a new one (latency, model error rate) is adding a component and wiring
it in.

One design rule worth stating out loud: the quality checker does not feed the
`should_continue` decision. Quality is an output property, not a loop-control
signal. A low quality score means "try to improve the output," not "stop
looping." Introspection detects; adaptation decides.

`StepAssessment` and `BudgetTracker` are dataclasses here to match the form
printed in the book. The other types in this package are Pydantic models,
following the rest of the repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.ch09_metacognition.progress_tracker import ProgressTracker
from src.ch09_metacognition.quality_checker import OutputQualityChecker, QualityReport
from src.ch09_metacognition.repetition_detector import RepetitionDetector, StepRecord
from src.shared.types import Citation


@dataclass
class StepAssessment:
    step: int
    is_looping: bool
    quality_score: float
    marginal_gain: float
    budget_remaining: float  # tokens or cost remaining
    should_continue: bool
    reason: str


@dataclass
class BudgetTracker:
    total_budget_tokens: int
    consumed_tokens: int = 0
    total_budget_usd: float = 0.10
    consumed_usd: float = 0.0

    @property
    def remaining_tokens(self) -> int:
        return self.total_budget_tokens - self.consumed_tokens

    @property
    def remaining_usd(self) -> float:
        return self.total_budget_usd - self.consumed_usd

    def can_afford_step(self, estimated_step_tokens: int) -> bool:
        return self.remaining_tokens > estimated_step_tokens

    def consume(self, tokens: int, usd: float = 0.0) -> None:
        self.consumed_tokens += tokens
        self.consumed_usd += usd

    def budget_summary(self) -> str:
        """Inject this into the agent's context each step."""
        return (
            f"Budget: {self.remaining_tokens} tokens remaining "
            f"(${self.remaining_usd:.3f} of ${self.total_budget_usd:.2f}). "
            f"Use remaining budget wisely."
        )


@dataclass
class MetacognitiveMonitor:
    """Runs every detector after each step and returns one assessment."""

    detector: RepetitionDetector = field(default_factory=RepetitionDetector)
    tracker: ProgressTracker = field(default_factory=ProgressTracker)
    checker: OutputQualityChecker = field(default_factory=OutputQualityChecker)
    budget: BudgetTracker | None = None
    max_steps: int = 5
    estimated_step_tokens: int = 1500

    def assess(
        self,
        step: int,
        tool: str,
        arguments: dict,
        observation: str = "",
        reasoning: str = "",
        answer: str = "",
        citations: list[Citation] | None = None,
    ) -> StepAssessment:
        verdict = self.detector.record(
            StepRecord(
                tool=tool,
                arguments=arguments,
                observation=observation,
                reasoning=reasoning,
                answer=answer,
            )
        )
        gain = self.tracker.record(observation or answer).gain
        quality = self.quality(answer, citations)

        remaining = float(self.budget.remaining_tokens) if self.budget else float("inf")
        affordable = (
            self.budget.can_afford_step(self.estimated_step_tokens) if self.budget else True
        )

        if verdict.is_looping:
            return StepAssessment(
                step, True, quality.score, gain, remaining, False, f"looping: {verdict.detail}"
            )
        if not affordable:
            return StepAssessment(
                step,
                False,
                quality.score,
                gain,
                remaining,
                False,
                "budget exhausted for another step",
            )
        if step >= self.max_steps:
            return StepAssessment(
                step,
                False,
                quality.score,
                gain,
                remaining,
                False,
                f"step limit {self.max_steps} reached",
            )
        if self.tracker.is_stale():
            return StepAssessment(
                step,
                False,
                quality.score,
                gain,
                remaining,
                False,
                f"marginal gain {gain:.2f} below threshold",
            )
        return StepAssessment(step, False, quality.score, gain, remaining, True, "progressing")

    def quality(self, answer: str, citations: list[Citation] | None = None) -> QualityReport:
        return self.checker.check(answer, citations or [])

    def reset(self) -> None:
        self.detector.reset()
        self.tracker.reset()
