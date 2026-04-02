"""Tests for the eval comparison module (Section 0d)."""

from src.ch00.eval_compare import EvalResult, score_answer


def test_score_answer_exact_match():
    result = score_answer(query="What is 2+2?", expected="4", actual="4")
    assert result.score == 1.0


def test_score_answer_contains_expected():
    result = score_answer(query="What is 2+2?", expected="4", actual="The answer is 4.")
    assert result.score >= 0.5


def test_score_answer_wrong():
    result = score_answer(query="What is 2+2?", expected="4", actual="The answer is 7.")
    assert result.score == 0.0


def test_score_answer_case_insensitive():
    result = score_answer(query="What color is the sky?", expected="blue", actual="Blue")
    assert result.score >= 0.5


def test_eval_result_fields():
    result = EvalResult(
        query="test",
        expected="expected",
        actual="actual",
        score=0.5,
        tokens=100,
        latency_ms=500.0,
        cost_estimate=0.001,
    )
    assert result.query == "test"
    assert result.score == 0.5
