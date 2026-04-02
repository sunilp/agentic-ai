"""Framework comparison runner (Section 0d).

Runs all three agent implementations (raw, ADK, LangChain) against a shared
set of test queries and prints a comparison table. Handles missing optional
dependencies gracefully -- if a framework is not installed it is listed as
"skipped" in the output rather than raising an error.

Run with:
    python project/framework-comparison/src/compare.py
"""

from __future__ import annotations

import asyncio
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Path bootstrap.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import yaml  # noqa: E402

from src.ch00.llm_basics import estimate_cost  # noqa: E402
from src.shared.types import CompletionResponse, TokenUsage, ToolCall  # noqa: E402

# ---------------------------------------------------------------------------
# Load test queries
# ---------------------------------------------------------------------------

_YAML_PATH = Path(__file__).parent.parent / "evals" / "test_queries.yaml"


def load_test_queries() -> list[dict[str, str]]:
    """Load query/expected pairs from evals/test_queries.yaml."""
    with _YAML_PATH.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data["queries"]


# ---------------------------------------------------------------------------
# Scripted mock responses (shared across all frameworks for raw agent)
# ---------------------------------------------------------------------------


def _tc(name: str, args: dict[str, Any]) -> CompletionResponse:
    return CompletionResponse(
        content=None,
        tool_calls=[ToolCall(id="cmp", name=name, arguments=args)],
        model="mock",
        usage=TokenUsage(prompt_tokens=40, completion_tokens=15, total_tokens=55),
    )


def _tr(text: str) -> CompletionResponse:
    return CompletionResponse(
        content=text,
        model="mock",
        usage=TokenUsage(prompt_tokens=60, completion_tokens=25, total_tokens=85),
    )


def _mock_responses_for(query: str) -> list[CompletionResponse]:
    """Return scripted mock responses for a query."""
    q = query.strip().lower()
    if "15 * 7" in q:
        return [_tc("calculator", {"operation": "multiply", "a": 15, "b": 7}), _tr("15 * 7 = 105")]
    if "100 / 4" in q and "10" in q:
        return [
            _tc("calculator", {"operation": "divide", "a": 100, "b": 4}),
            _tc("calculator", {"operation": "add", "a": 25.0, "b": 10}),
            _tr("100 / 4 + 10 = 35"),
        ]
    if "quick brown fox" in q:
        return [_tr("The sentence contains 9 words.")]
    if "agentic ai" in q:
        return [
            _tc("search", {"query": "agentic AI", "max_results": 2}),
            _tr("Wikipedia article about agentic AI: autonomous reasoning and tool use."),
        ]
    if "machine learning" in q:
        return [
            _tc("search", {"query": "machine learning", "max_results": 1}),
            _tr("The first result is the Wikipedia article about machine learning."),
        ]
    return [_tr(f"Answer for: {query}")]


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class FrameworkResult:
    """Per-query result for one framework implementation."""

    query: str
    expected: str
    actual: str
    score: float
    steps: int
    total_tokens: int
    elapsed_ms: float
    cost_usd: float
    skipped: bool = False
    skip_reason: str = ""


def score_answer(expected: str, actual: str) -> float:
    """Simple substring scorer (0.0 / 0.8 / 1.0)."""
    e = expected.strip().lower()
    a = actual.strip().lower()
    if e == a:
        return 1.0
    if e in a:
        return 0.8
    return 0.0


# ---------------------------------------------------------------------------
# Per-framework runners
# ---------------------------------------------------------------------------

MODEL = "claude-haiku-4-5-20251001"


async def _run_raw(queries: list[dict[str, str]]) -> list[FrameworkResult]:
    """Run the raw agent against each query."""
    from raw_agent import run_raw_agent

    results: list[FrameworkResult] = []

    for case in queries:
        query = case["query"]
        expected = case["expected"]
        mock_responses = _mock_responses_for(query)

        t0 = time.monotonic()
        agent_result = await run_raw_agent(
            query=query,
            mock_responses=mock_responses,
            max_steps=5,
        )
        elapsed = (time.monotonic() - t0) * 1000

        actual = agent_result.answer or ""
        cost = estimate_cost(
            prompt_tokens=agent_result.total_tokens // 2,
            completion_tokens=agent_result.total_tokens // 2,
            model=MODEL,
        )
        results.append(
            FrameworkResult(
                query=query,
                expected=expected,
                actual=actual,
                score=score_answer(expected, actual),
                steps=agent_result.steps,
                total_tokens=agent_result.total_tokens,
                elapsed_ms=round(elapsed, 1),
                cost_usd=cost,
            )
        )
    return results


async def _run_adk(queries: list[dict[str, str]]) -> list[FrameworkResult]:
    """Run the ADK agent against each query, skipping if not installed."""
    try:
        from adk_agent import run_adk_agent
    except ImportError as exc:
        return [
            FrameworkResult(
                query=c["query"],
                expected=c["expected"],
                actual="",
                score=0.0,
                steps=0,
                total_tokens=0,
                elapsed_ms=0.0,
                cost_usd=0.0,
                skipped=True,
                skip_reason=str(exc),
            )
            for c in queries
        ]

    results: list[FrameworkResult] = []
    for case in queries:
        query = case["query"]
        expected = case["expected"]
        try:
            adk_result = await run_adk_agent(query=query)
            actual = adk_result.answer or ""
            cost = estimate_cost(
                prompt_tokens=adk_result.total_tokens // 2,
                completion_tokens=adk_result.total_tokens // 2,
                model=MODEL,
            )
            results.append(
                FrameworkResult(
                    query=query,
                    expected=expected,
                    actual=actual,
                    score=score_answer(expected, actual),
                    steps=adk_result.steps,
                    total_tokens=adk_result.total_tokens,
                    elapsed_ms=adk_result.elapsed_ms,
                    cost_usd=cost,
                )
            )
        except (ImportError, Exception) as exc:
            results.append(
                FrameworkResult(
                    query=query,
                    expected=expected,
                    actual="",
                    score=0.0,
                    steps=0,
                    total_tokens=0,
                    elapsed_ms=0.0,
                    cost_usd=0.0,
                    skipped=True,
                    skip_reason=str(exc),
                )
            )
    return results


async def _run_langchain(queries: list[dict[str, str]]) -> list[FrameworkResult]:
    """Run the LangChain agent against each query, skipping if not installed."""
    try:
        from langchain_agent import run_langchain_agent
    except ImportError as exc:
        return [
            FrameworkResult(
                query=c["query"],
                expected=c["expected"],
                actual="",
                score=0.0,
                steps=0,
                total_tokens=0,
                elapsed_ms=0.0,
                cost_usd=0.0,
                skipped=True,
                skip_reason=str(exc),
            )
            for c in queries
        ]

    results: list[FrameworkResult] = []
    for case in queries:
        query = case["query"]
        expected = case["expected"]
        try:
            lc_result = await run_langchain_agent(query=query)
            actual = lc_result.answer or ""
            cost = estimate_cost(
                prompt_tokens=lc_result.total_tokens // 2,
                completion_tokens=lc_result.total_tokens // 2,
                model=MODEL,
            )
            results.append(
                FrameworkResult(
                    query=query,
                    expected=expected,
                    actual=actual,
                    score=score_answer(expected, actual),
                    steps=lc_result.steps,
                    total_tokens=lc_result.total_tokens,
                    elapsed_ms=lc_result.elapsed_ms,
                    cost_usd=cost,
                )
            )
        except (ImportError, Exception) as exc:
            results.append(
                FrameworkResult(
                    query=query,
                    expected=expected,
                    actual="",
                    score=0.0,
                    steps=0,
                    total_tokens=0,
                    elapsed_ms=0.0,
                    cost_usd=0.0,
                    skipped=True,
                    skip_reason=str(exc),
                )
            )
    return results


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------


def _print_framework_results(name: str, results: list[FrameworkResult]) -> None:
    """Print per-query detail for one implementation."""
    print(f"\n{'=' * 65}")
    print(f"Implementation: {name}")
    print(f"{'=' * 65}")

    first_skipped = next((r for r in results if r.skipped), None)
    if first_skipped:
        print(f"  SKIPPED: {first_skipped.skip_reason}")
        return

    header = f"{'Query':<38} {'Score':>6} {'Steps':>6} {'Tokens':>7} {'ms':>8}"
    print(header)
    print("-" * len(header))
    for r in results:
        q_short = r.query[:36] + ".." if len(r.query) > 38 else r.query
        print(
            f"{q_short:<38} {r.score:>6.1f} {r.steps:>6} {r.total_tokens:>7} {r.elapsed_ms:>7.1f}"
        )


def print_summary(all_results: dict[str, list[FrameworkResult]]) -> None:
    """Print the summary comparison table."""
    print(f"\n{'=' * 75}")
    print("Summary")
    print(f"{'=' * 75}")
    header = (
        f"{'Implementation':<22} {'Avg Score':>10} {'Total Tokens':>13} "
        f"{'Avg ms':>8} {'Total cost':>12}"
    )
    print(header)
    print("-" * len(header))

    for name, results in all_results.items():
        active = [r for r in results if not r.skipped]
        if not active:
            print(f"{name:<22}  skipped (not installed)")
            continue
        avg_score = sum(r.score for r in active) / len(active)
        total_tokens = sum(r.total_tokens for r in active)
        avg_ms = sum(r.elapsed_ms for r in active) / len(active)
        total_cost = sum(r.cost_usd for r in active)
        print(
            f"{name:<22} {avg_score:>10.2f} {total_tokens:>13} {avg_ms:>8.1f} ${total_cost:>11.6f}"
        )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


async def _main() -> None:
    print("Framework Comparison -- Foundations Section 0d")
    print("=" * 65)

    queries = load_test_queries()
    print(f"Running {len(queries)} queries across available implementations...")
    print()

    raw_results, adk_results, lc_results = await asyncio.gather(
        _run_raw(queries),
        _run_adk(queries),
        _run_langchain(queries),
    )

    all_results = {
        "raw_agent": raw_results,
        "adk_agent": adk_results,
        "langchain_agent": lc_results,
    }

    for name, results in all_results.items():
        _print_framework_results(name, results)

    print_summary(all_results)


if __name__ == "__main__":
    asyncio.run(_main())
