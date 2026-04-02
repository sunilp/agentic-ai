"""Context overflow experiment (llm-explorer, Section 0a).

Progressively fills a mock context window and measures quality degradation.
Uses MockClient for reproducibility -- no API key required.

The experiment simulates the well-documented "lost in the middle" phenomenon:
models attend reliably to information at the start and end of a long context,
but attention to the middle degrades as context grows.

Run with:
    python project/llm-explorer/src/context_overflow.py
"""

from __future__ import annotations

import asyncio
import math
import sys
from dataclasses import dataclass
from pathlib import Path

# Path bootstrap for direct script execution.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ch00.llm_basics import call_llm, count_tokens_estimate  # noqa: E402
from src.shared.model_client import MockClient  # noqa: E402
from src.shared.types import CompletionResponse, TokenUsage  # noqa: E402

# ---------------------------------------------------------------------------
# Context window parameters
# ---------------------------------------------------------------------------

# A modest context window -- small enough that filling it is fast in demo mode.
CONTEXT_WINDOW_TOKENS = 4_096

# Target answer buried in the context. We track whether the model "finds" it.
TARGET_ANSWER = "The activation function in layer 3 is ReLU."

# Filler text that does not contain the target answer.
FILLER_SENTENCE = (
    "This is filler content that occupies context space without contributing "
    "to the answer. It simulates retrieved documents that are not relevant to "
    "the current query."
)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class OverflowExperimentResult:
    """Outcome of one fill-level experiment run."""

    fill_level_pct: int
    prompt_tokens_estimate: int
    context_utilisation_pct: float
    answer_present: bool
    simulated_quality_score: float  # 0.0 to 1.0


# ---------------------------------------------------------------------------
# Experiment
# ---------------------------------------------------------------------------


def _build_prompt(fill_level_pct: int) -> str:
    """Build a prompt that fills the context window to the given percentage.

    The target answer is embedded at a position proportional to the fill level:
    - At low fill levels, the answer is near the middle of the context.
    - As fill level increases, surrounding noise increases, making the answer
      harder for the model to attend to.

    Args:
        fill_level_pct: Target fill percentage (0-100).

    Returns:
        A prompt string of appropriate length.
    """
    target_tokens = int(CONTEXT_WINDOW_TOKENS * fill_level_pct / 100)

    # Reserve space for the question and the target answer sentence itself.
    question = "Based on the above context, what is the activation function in layer 3?"
    question_tokens = count_tokens_estimate(question)
    target_tokens_in_text = count_tokens_estimate(TARGET_ANSWER)

    filler_budget = max(0, target_tokens - question_tokens - target_tokens_in_text)
    filler_token_size = count_tokens_estimate(FILLER_SENTENCE)
    filler_repetitions = max(0, filler_budget // filler_token_size)

    # Build context: half filler before the answer, half after.
    half_filler = filler_repetitions // 2
    context_parts = [FILLER_SENTENCE] * half_filler
    context_parts.append(TARGET_ANSWER)
    context_parts.extend([FILLER_SENTENCE] * (filler_repetitions - half_filler))

    context = "\n".join(context_parts)
    return f"Context:\n{context}\n\nQuestion: {question}"


def _quality_score_from_fill(fill_level_pct: int) -> float:
    """Model simulated quality degradation as context fills.

    Based on empirical observations from the literature:
    - Quality is high at low context utilisation (<=40%).
    - Quality starts to degrade around 50-60% utilisation.
    - Above 80%, the model frequently misses information in the middle.
    - At 100%, quality is often near random for middle-positioned targets.

    This is intentionally a simplified model for demonstration purposes.
    """
    if fill_level_pct <= 40:
        return 1.0
    elif fill_level_pct <= 60:
        # Linear degradation from 1.0 to 0.85.
        return 1.0 - (fill_level_pct - 40) / 20 * 0.15
    elif fill_level_pct <= 80:
        # Steeper degradation from 0.85 to 0.55.
        return 0.85 - (fill_level_pct - 60) / 20 * 0.30
    else:
        # Rapid degradation from 0.55 toward 0.15.
        return max(0.15, 0.55 - (fill_level_pct - 80) / 20 * 0.40)


async def run_overflow_experiment(
    fill_levels: list[int] | None = None,
) -> list[OverflowExperimentResult]:
    """Run the context overflow experiment at each fill level.

    Args:
        fill_levels: List of fill percentages to test (default: 10% increments).

    Returns:
        List of results, one per fill level.
    """
    if fill_levels is None:
        fill_levels = list(range(10, 101, 10))

    results: list[OverflowExperimentResult] = []

    for fill_pct in fill_levels:
        prompt = _build_prompt(fill_pct)
        prompt_tokens = count_tokens_estimate(prompt)
        utilisation = min(100.0, prompt_tokens / CONTEXT_WINDOW_TOKENS * 100)

        # Simulated quality score -- in a real experiment this would be
        # measured against a ground-truth answer using a real model.
        quality = _quality_score_from_fill(fill_pct)
        answer_present = quality > 0.5

        # Mock client returns a response consistent with the simulated quality.
        mock_content = TARGET_ANSWER if answer_present else "I don't have enough information."
        client = MockClient(
            responses=[
                CompletionResponse(
                    content=mock_content,
                    model="mock",
                    usage=TokenUsage(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=20,
                        total_tokens=prompt_tokens + 20,
                    ),
                )
            ]
        )

        response = await call_llm(client, prompt)
        _ = response  # Response captured; we use simulated score for the experiment.

        results.append(
            OverflowExperimentResult(
                fill_level_pct=fill_pct,
                prompt_tokens_estimate=prompt_tokens,
                context_utilisation_pct=round(utilisation, 1),
                answer_present=answer_present,
                simulated_quality_score=round(quality, 2),
            )
        )

    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _quality_bar(score: float, width: int = 20) -> str:
    """Convert a 0.0-1.0 quality score to an ASCII bar."""
    filled = math.ceil(score * width)
    return "[" + "#" * filled + " " * (width - filled) + "]"


def print_overflow_results(results: list[OverflowExperimentResult]) -> None:
    """Print a table and quality bar chart for the experiment results."""
    print(f"Context window: {CONTEXT_WINDOW_TOKENS:,} tokens")
    print(f"Target sentence: {TARGET_ANSWER!r}")
    print()

    header = f"{'Fill %':>7} {'Est tokens':>11} {'Utilisation':>12} {'Found?':>7} {'Quality':>8}  Bar"
    print(header)
    print("-" * (len(header) + 22))
    for r in results:
        found_marker = "yes" if r.answer_present else "no"
        bar = _quality_bar(r.simulated_quality_score)
        print(
            f"{r.fill_level_pct:>6}% {r.prompt_tokens_estimate:>11} "
            f"{r.context_utilisation_pct:>11.1f}% {found_marker:>7} "
            f"{r.simulated_quality_score:>8.2f}  {bar}"
        )
    print()

    degradation_start = next(
        (r.fill_level_pct for r in results if r.simulated_quality_score < 1.0), None
    )
    if degradation_start:
        print(f"Quality degradation begins at ~{degradation_start}% context utilisation.")
    print()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    print("=" * 70)
    print("Context overflow experiment")
    print("=" * 70)
    print()
    print(
        "This experiment demonstrates how answer quality degrades as the context "
        "window fills. The target sentence is embedded in increasing amounts of "
        "irrelevant filler text. Quality is simulated based on published research "
        "showing the 'lost in the middle' effect.\n"
    )

    results = asyncio.run(run_overflow_experiment())
    print_overflow_results(results)

    print("Key observations:")
    print("  - Quality is stable at low fill levels (<= 40%)")
    print("  - Degradation begins around 50% utilisation")
    print("  - Above 80%, information in the middle is frequently missed")
    print("  - Design for 60-70% utilisation to maintain reliable quality")
