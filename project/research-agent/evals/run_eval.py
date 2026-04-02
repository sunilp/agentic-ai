"""Eval runner for the research agent (Section 0c).

Loads test_queries.yaml, runs the research agent against each query using
a scripted MockClient, scores each answer with score_answer(), and prints
a results table.

Run with:
    python project/research-agent/evals/run_eval.py
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from typing import Any

# Path bootstrap.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import yaml  # noqa: E402
from agent import ResearchAgent  # noqa: E402
from tools import create_research_registry  # noqa: E402

from src.ch00.eval_compare import EvalResult, print_comparison, score_answer  # noqa: E402
from src.ch00.llm_basics import estimate_cost  # noqa: E402
from src.shared.model_client import MockClient  # noqa: E402
from src.shared.types import CompletionResponse, TokenUsage, ToolCall  # noqa: E402

# ---------------------------------------------------------------------------
# Load test cases
# ---------------------------------------------------------------------------

_YAML_PATH = Path(__file__).parent / "test_queries.yaml"


def load_test_queries() -> list[dict[str, str]]:
    """Load query/expected pairs from test_queries.yaml."""
    with _YAML_PATH.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data["queries"]


# ---------------------------------------------------------------------------
# Scripted mock responses
# ---------------------------------------------------------------------------


def _tc(name: str, args: dict[str, Any]) -> CompletionResponse:
    return CompletionResponse(
        content=None,
        tool_calls=[ToolCall(id="eval", name=name, arguments=args)],
        model="mock",
        usage=TokenUsage(prompt_tokens=40, completion_tokens=15, total_tokens=55),
    )


def _tr(text: str) -> CompletionResponse:
    return CompletionResponse(
        content=text,
        model="mock",
        usage=TokenUsage(prompt_tokens=60, completion_tokens=25, total_tokens=85),
    )


def _scripted_responses_for(query: str) -> list[CompletionResponse]:
    """Return scripted MockClient responses for a known query."""
    q = query.strip().lower()

    if "15 * 7" in q or "15 times 7" in q:
        return [
            _tc("calculator", {"operation": "multiply", "a": 15, "b": 7}),
            _tr("15 * 7 = 105"),
        ]
    if "100 / 4" in q and "10" in q:
        return [
            _tc("calculator", {"operation": "divide", "a": 100, "b": 4}),
            _tc("calculator", {"operation": "add", "a": 25.0, "b": 10}),
            _tr("100 / 4 = 25, then 25 + 10 = 35"),
        ]
    if "quick brown fox" in q:
        return [
            _tr("The phrase 'the quick brown fox jumps over the lazy dog' contains 9 words."),
        ]
    if "agentic ai" in q and "summarize" in q:
        return [
            _tc("search", {"query": "agentic AI", "max_results": 2}),
            _tr(
                "Based on search results, agentic AI refers to AI systems capable of "
                "autonomous multi-step reasoning. The Wikipedia article about agentic AI "
                "provides a comprehensive overview."
            ),
        ]
    if "machine learning" in q and "first result" in q:
        return [
            _tc("search", {"query": "machine learning", "max_results": 1}),
            _tr(
                "The first result is the Wikipedia article about machine learning: "
                "https://en.wikipedia.org/wiki/Machine_learning"
            ),
        ]

    # Generic fallback.
    return [_tr(f"Here is information about: {query}")]


# ---------------------------------------------------------------------------
# Eval runner
# ---------------------------------------------------------------------------


MODEL = "claude-haiku-4-5-20251001"


async def run_evals(test_cases: list[dict[str, str]]) -> list[EvalResult]:
    """Run the research agent against each test case and return scored results."""
    registry = create_research_registry()
    results: list[EvalResult] = []

    for case in test_cases:
        query = case["query"]
        expected = case["expected"]

        mock_responses = _scripted_responses_for(query)
        client = MockClient(responses=mock_responses)

        agent = ResearchAgent(
            client=client,
            registry=registry,
            model_name=MODEL,
            max_steps=8,
            verbose=False,
        )

        t0 = time.monotonic()
        agent_result = await agent.run(query)
        latency_ms = (time.monotonic() - t0) * 1000

        actual = agent_result.answer or ""
        base_result = score_answer(query=query, expected=expected, actual=actual)

        tokens = agent_result.total_tokens
        cost = estimate_cost(
            prompt_tokens=tokens // 2,
            completion_tokens=tokens // 2,
            model=MODEL,
        )

        results.append(
            EvalResult(
                query=base_result.query,
                expected=base_result.expected,
                actual=base_result.actual,
                score=base_result.score,
                tokens=tokens,
                latency_ms=latency_ms,
                cost_estimate=cost,
            )
        )

    return results


async def _main() -> None:
    print("Research Agent -- Eval Suite")
    print("=" * 60)
    test_cases = load_test_queries()
    print(f"Loaded {len(test_cases)} test cases from {_YAML_PATH.name}")
    print()

    results = await run_evals(test_cases)
    print_comparison({"research_agent": results})

    pass_count = sum(1 for r in results if r.score > 0.0)
    print(f"\nPass rate: {pass_count}/{len(results)} ({pass_count / len(results) * 100:.0f}%)")


if __name__ == "__main__":
    asyncio.run(_main())
