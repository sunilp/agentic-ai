"""The AdaptiveAgent: observe, think, act, reflect.

The reflect step consults the monitor and the budget tracker. Based on the
assessment the agent continues, switches strategy, stops early, or (after the
loop) self-corrects once and escalates if that fails.

The metacognitive machinery wraps existing agent logic. You do not rewrite the
agent -- you add a monitor, define strategies, add a budget tracker, and insert
the reflect step.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from src.ch09_metacognition.monitor import BudgetTracker, MetacognitiveMonitor, StepAssessment
from src.shared.model_client import ModelClient
from src.shared.types import AgentResponse, Citation, CompletionRequest, Message, Role

CORRECTION_PROMPT = """Your previous answer scored low on evidence grounding.
Rewrite so that every factual claim directly references the evidence.
If the evidence does not support a claim, remove it or note the gap."""

ANTI_SYCOPHANCY_PROMPT = """If your evidence supports your original answer, say so clearly.
Do not add information that is not in the evidence just because
you were asked to reconsider."""


@dataclass
class Strategy:
    """A named retrieval approach the router can select."""

    name: str
    search: Callable[[str], list[Citation]]


@dataclass
class StrategyRouter:
    """Bounded exploration: the agent selects from a ranked list the engineer defined.

    An agent that invents strategies is unpredictable. An agent that selects
    from a ranked list is auditable.
    """

    strategies: list[Strategy]
    index: int = 0
    switches: list[str] = field(default_factory=list)

    @property
    def current(self) -> Strategy:
        return self.strategies[self.index]

    @property
    def exhausted(self) -> bool:
        return self.index >= len(self.strategies) - 1

    def switch(self) -> Strategy | None:
        """Advance to the next untried strategy, or None if all are exhausted."""
        if self.exhausted:
            return None
        self.index += 1
        self.switches.append(self.current.name)
        return self.current

    def reset(self) -> None:
        self.index = 0
        self.switches.clear()


def should_stop_early(
    assessment: StepAssessment,
    steps_remaining: int,
    min_quality: float = 0.5,
    estimated_step_cost: float = 1500.0,
) -> bool:
    """Stop when further steps would cost tokens without improving the answer.

    `steps_remaining` matters. On step 4 of 5 one more step is cheap. On step 2
    of 10, eight unnecessary steps are expensive.
    """
    # Near-zero gain with many steps left = pure waste
    if assessment.marginal_gain < 0.05 and steps_remaining > 2:
        return True
    # Good-enough quality + low gain = done
    if assessment.quality_score >= min_quality and assessment.marginal_gain < 0.1:
        return True
    # Budget too low for another productive step
    if not assessment.budget_remaining > estimated_step_cost:
        return True
    return False


class AdaptiveAgent:
    """An agent whose loop has four steps: observe, think, act, reflect."""

    def __init__(
        self,
        client: ModelClient,
        router: StrategyRouter,
        monitor: MetacognitiveMonitor | None = None,
        budget: BudgetTracker | None = None,
        max_steps: int = 5,
        min_quality: float = 0.5,
    ) -> None:
        self.client = client
        self.router = router
        self.budget = budget or BudgetTracker(total_budget_tokens=20_000)
        self.monitor = monitor or MetacognitiveMonitor(budget=self.budget, max_steps=max_steps)
        self.monitor.budget = self.budget
        self.max_steps = max_steps
        self.min_quality = min_quality
        self.assessments: list[StepAssessment] = []
        self.stop_reason: str = ""

    async def run(self, query: str) -> AgentResponse:
        citations: list[Citation] = []
        answer = ""
        steps = 0
        self.stop_reason = "completed"

        for step in range(1, self.max_steps + 1):
            steps = step
            strategy = self.router.current

            # observe
            citations = strategy.search(query)
            observation = " ".join(c.text for c in citations)

            # think + act
            answer = await self._draft(query, citations)

            # reflect
            assessment = self.monitor.assess(
                step=step,
                tool=strategy.name,
                arguments={"query": query},
                observation=observation,
                reasoning=answer,
                answer=answer,
                citations=citations,
            )
            self.assessments.append(assessment)

            if assessment.is_looping:
                if self.router.switch() is not None:
                    self.monitor.detector.reset()
                    continue
                self.stop_reason = "all strategies exhausted"
                break

            steps_remaining = self.max_steps - step
            if should_stop_early(assessment, steps_remaining, self.min_quality):
                self.stop_reason = "early stop: " + assessment.reason
                break
            if not assessment.should_continue:
                self.stop_reason = assessment.reason
                break

        report = self.monitor.quality(answer, citations)

        # One self-correction attempt, never a loop.
        if report.score < self.min_quality and citations:
            answer = await self._correct(query, citations, answer)
            report = self.monitor.quality(answer, citations)

        escalated = report.score < self.min_quality
        return AgentResponse(
            answer=answer,
            citations=citations,
            confidence=round(min(max(report.score, 0.0), 1.0), 4),
            escalated=escalated,
            escalation_reason=("quality below threshold after correction" if escalated else None),
            steps_taken=steps,
            latency_ms=0.0,
        )

    async def _draft(self, query: str, citations: list[Citation]) -> str:
        messages = [
            Message(role=Role.SYSTEM, content=self.budget.budget_summary()),
            Message(role=Role.USER, content=self._prompt(query, citations)),
        ]
        response = await self.client.complete(CompletionRequest(messages=messages))
        self._charge(response)
        return response.content or ""

    async def _correct(self, query: str, citations: list[Citation], previous: str) -> str:
        messages = [
            Message(role=Role.SYSTEM, content=CORRECTION_PROMPT),
            Message(role=Role.USER, content=f"{self._prompt(query, citations)}\n\n{previous}"),
        ]
        response = await self.client.complete(CompletionRequest(messages=messages, temperature=0.0))
        self._charge(response)
        return response.content or previous

    def _charge(self, response) -> None:
        usage = getattr(response, "usage", None)
        if usage is not None:
            self.budget.consume(usage.total_tokens or 0)

    @staticmethod
    def _prompt(query: str, citations: list[Citation]) -> str:
        evidence = "\n".join(f"[{i + 1}] {c.text}" for i, c in enumerate(citations))
        return f"Question: {query}\n\nEvidence:\n{evidence}\n\nAnswer using only the evidence."
