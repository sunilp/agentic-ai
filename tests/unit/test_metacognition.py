"""Tests for the metacognition layer: introspection and adaptation."""

from src.ch09_metacognition.adaptive_agent import (
    AdaptiveAgent,
    Strategy,
    StrategyRouter,
    should_stop_early,
)
from src.ch09_metacognition.monitor import BudgetTracker, MetacognitiveMonitor, StepAssessment
from src.ch09_metacognition.progress_tracker import ProgressTracker, record_step
from src.ch09_metacognition.quality_checker import OutputQualityChecker
from src.ch09_metacognition.repetition_detector import (
    RepetitionDetector,
    StepRecord,
    is_looping,
)
from src.shared.model_client import MockClient
from src.shared.types import Citation, CompletionResponse

SEARCH = "search"
QUERY = {"query": "quarterly revenue 2024"}


# --- Layer 1: exact match -------------------------------------------------


def test_book_is_looping_helper():
    assert is_looping(["a", "a"]) is True
    assert is_looping(["a", "b"]) is False
    assert is_looping(["a"]) is False


def test_identical_tool_calls_flagged():
    d = RepetitionDetector()
    d.record(StepRecord(tool=SEARCH, arguments=QUERY))
    verdict = d.record(StepRecord(tool=SEARCH, arguments=QUERY))
    assert verdict.is_looping
    assert verdict.layer == "exact_match"


def test_argument_order_does_not_defeat_detection():
    d = RepetitionDetector()
    d.record(StepRecord(tool=SEARCH, arguments={"q": "x", "k": 3}))
    verdict = d.record(StepRecord(tool=SEARCH, arguments={"k": 3, "q": "x"}))
    assert verdict.is_looping


def test_varied_calls_not_flagged():
    d = RepetitionDetector()
    d.record(StepRecord(tool=SEARCH, arguments={"query": "a"}))
    verdict = d.record(StepRecord(tool=SEARCH, arguments={"query": "b"}))
    assert not verdict.is_looping


# --- Layer 2: action-sequence fingerprinting ------------------------------


def test_alternating_sequence_flagged():
    d = RepetitionDetector()
    for query in ["a", "b", "a", "b"]:
        verdict = d.record(StepRecord(tool=SEARCH, arguments={"query": query}))
    assert verdict.is_looping
    assert verdict.layer == "sequence_fingerprint"


# --- Layer 3: semantic similarity -----------------------------------------


def test_semantic_similarity_flagged():
    vectors = {
        "What was Q3 revenue?": [1.0, 0.0, 0.1],
        "How much revenue in the third quarter?": [0.99, 0.0, 0.12],
    }
    d = RepetitionDetector(embed=lambda text: vectors[text])
    d.record(StepRecord(tool=SEARCH, arguments={"query": "a"}, reasoning="What was Q3 revenue?"))
    verdict = d.record(
        StepRecord(
            tool=SEARCH,
            arguments={"query": "b"},
            reasoning="How much revenue in the third quarter?",
        )
    )
    assert verdict.is_looping
    assert verdict.layer == "semantic_similarity"


# --- Layer 4: output convergence ------------------------------------------


def test_output_convergence_flagged():
    d = RepetitionDetector()
    for i in range(3):
        verdict = d.record(
            StepRecord(tool=SEARCH, arguments={"query": f"q{i}"}, answer="Revenue was $4.2M.")
        )
    assert verdict.is_looping
    assert verdict.layer == "output_convergence"


# --- Progress tracking ----------------------------------------------------


def test_record_step_book_form():
    seen: set[str] = set()
    gain, stale = record_step(seen, "alpha beta gamma")
    assert gain == 1.0 and stale is False
    gain, stale = record_step(seen, "alpha beta gamma")
    assert gain == 0.0 and stale is True


def test_gain_curve_flattens():
    t = ProgressTracker()
    t.record("the retry policy uses exponential backoff")
    t.record("the retry policy uses exponential backoff")
    assert t.total_gain_curve[0] == 1.0
    assert t.total_gain_curve[1] == 0.0
    assert t.is_stale() is True


def test_suggested_step_budget_marks_flattening_point():
    t = ProgressTracker()
    t.record("alpha beta gamma")
    t.record("delta epsilon zeta")
    t.record("alpha beta gamma")
    assert t.suggested_step_budget() == 2


def test_stop_words_ignored():
    t = ProgressTracker()
    first = t.record("the agent is in the loop")
    assert first.total_words == 2  # agent, loop


# --- Quality checking -----------------------------------------------------


GOOD_EVIDENCE = [
    Citation(source="runbook.pdf", text="The retry policy uses exponential backoff."),
    Citation(source="runbook.pdf", text="Jitter prevents thundering herd effects."),
]


def test_grounded_answer_scores_above_ungrounded():
    checker = OutputQualityChecker()
    grounded = checker.check(
        "The retry policy uses exponential backoff [1]. Jitter prevents thundering herd [2].",
        GOOD_EVIDENCE,
    )
    ungrounded = checker.check("Revenue grew significantly last quarter.", GOOD_EVIDENCE)
    assert grounded.score > ungrounded.score
    assert grounded.is_grounded
    assert not ungrounded.is_grounded


def test_confident_claims_on_thin_evidence_flagged():
    checker = OutputQualityChecker()
    report = checker.check("Revenue was exactly $4.2M [1].", GOOD_EVIDENCE)
    assert "confident claims on thin evidence" in report.issues


def test_hedging_on_thin_evidence_is_not_penalized_the_same():
    checker = OutputQualityChecker()
    confident = checker.check("Revenue was exactly $4.2M [1].", GOOD_EVIDENCE)
    hedged = checker.check("The evidence is insufficient to state revenue [1].", GOOD_EVIDENCE)
    assert hedged.score > confident.score


def test_empty_answer_reports_issue():
    assert OutputQualityChecker().check("", GOOD_EVIDENCE).issues == ["empty answer"]


# --- Budget ---------------------------------------------------------------


def test_budget_tracker_afford_and_summary():
    b = BudgetTracker(total_budget_tokens=2000, total_budget_usd=0.10)
    assert b.can_afford_step(1500) is True
    b.consume(1800, 0.05)
    assert b.can_afford_step(1500) is False
    assert "200 tokens remaining" in b.budget_summary()


# --- Monitor --------------------------------------------------------------


def test_monitor_stops_on_loop():
    m = MetacognitiveMonitor(max_steps=5)
    m.assess(step=1, tool=SEARCH, arguments=QUERY, observation="three documents found")
    a = m.assess(step=2, tool=SEARCH, arguments=QUERY, observation="three documents found")
    assert a.is_looping is True
    assert a.should_continue is False
    assert "looping" in a.reason


def test_monitor_ignores_quality_in_continue_decision():
    m = MetacognitiveMonitor(max_steps=5)
    a = m.assess(
        step=1,
        tool=SEARCH,
        arguments=QUERY,
        observation="entirely new material about backoff and jitter",
        answer="Ungrounded claim with no citation.",
    )
    assert a.quality_score < 0.5
    assert a.should_continue is True


def test_monitor_stops_when_budget_exhausted():
    m = MetacognitiveMonitor(budget=BudgetTracker(total_budget_tokens=100), max_steps=5)
    a = m.assess(step=1, tool=SEARCH, arguments=QUERY, observation="new material")
    assert a.should_continue is False
    assert "budget" in a.reason


def test_monitor_stops_at_step_limit():
    m = MetacognitiveMonitor(max_steps=2)
    m.assess(step=1, tool=SEARCH, arguments={"query": "a"}, observation="alpha beta")
    a = m.assess(step=2, tool=SEARCH, arguments={"query": "b"}, observation="gamma delta")
    assert a.should_continue is False
    assert "step limit" in a.reason


# --- Adaptation -----------------------------------------------------------


def _assessment(**kw) -> StepAssessment:
    defaults = dict(
        step=1,
        is_looping=False,
        quality_score=0.8,
        marginal_gain=0.5,
        budget_remaining=10_000.0,
        should_continue=True,
        reason="",
    )
    defaults.update(kw)
    return StepAssessment(**defaults)


def test_should_stop_early_on_near_zero_gain():
    assert should_stop_early(_assessment(marginal_gain=0.01), steps_remaining=3) is True


def test_should_stop_early_on_good_enough_answer():
    assert should_stop_early(_assessment(quality_score=0.7, marginal_gain=0.05), 1) is True


def test_should_stop_early_when_budget_too_low():
    assert should_stop_early(_assessment(budget_remaining=100.0), steps_remaining=1) is True


def test_should_not_stop_while_still_learning():
    assert should_stop_early(_assessment(quality_score=0.2, marginal_gain=0.6), 1) is False


def test_strategy_router_switches_then_exhausts():
    router = StrategyRouter(
        strategies=[
            Strategy(name="semantic", search=lambda q: []),
            Strategy(name="keyword", search=lambda q: []),
        ]
    )
    assert router.current.name == "semantic"
    assert router.switch().name == "keyword"
    assert router.switch() is None
    assert router.switches == ["keyword"]


async def test_adaptive_agent_recovers_from_loop_by_switching_strategy():
    thin = [Citation(source="hiring.pdf", text="Unrelated document about hiring policy.")]
    router = StrategyRouter(
        strategies=[
            Strategy(name="semantic_search", search=lambda q: thin),
            Strategy(name="keyword_search", search=lambda q: GOOD_EVIDENCE),
        ]
    )
    client = MockClient(
        responses=[
            CompletionResponse(content="Revenue grew significantly last quarter."),
            CompletionResponse(content="Revenue grew significantly last quarter."),
            CompletionResponse(
                content=(
                    "The retry policy uses exponential backoff [1]. "
                    "Jitter prevents thundering herd [2]."
                )
            ),
        ]
    )
    agent = AdaptiveAgent(client=client, router=router, max_steps=3)

    response = await agent.run("retry strategy")

    assert router.switches == ["keyword_search"]
    assert agent.assessments[1].is_looping is True
    assert response.steps_taken == 3
    assert response.escalated is False
    assert response.confidence > 0.5


async def test_adaptive_agent_escalates_when_correction_fails():
    thin = [Citation(source="hiring.pdf", text="Unrelated document about hiring policy.")]
    router = StrategyRouter(strategies=[Strategy(name="semantic_search", search=lambda q: thin)])
    client = MockClient(
        responses=[CompletionResponse(content="Revenue grew significantly last quarter.")] * 4
    )
    agent = AdaptiveAgent(client=client, router=router, max_steps=2)

    response = await agent.run("quarterly revenue")

    assert response.escalated is True
    assert response.escalation_reason == "quality below threshold after correction"
