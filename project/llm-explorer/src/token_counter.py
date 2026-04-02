"""Token counter experiments (llm-explorer, Section 0a).

Compares the character-based token estimator from llm_basics.py against tiktoken
(if installed), then projects batch processing costs across four model tiers.

Run with:
    python project/llm-explorer/src/token_counter.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# Path bootstrap for direct script execution.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ch00.llm_basics import MODEL_PRICING, count_tokens_estimate, estimate_cost  # noqa: E402

# ---------------------------------------------------------------------------
# Optional tiktoken import
# ---------------------------------------------------------------------------

try:
    import tiktoken  # type: ignore[import]

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------


@dataclass
class TokenEstimate:
    """Comparison of character-based vs tiktoken counts for one text sample."""

    label: str
    text: str
    char_estimate: int
    tiktoken_count: int | None  # None when tiktoken is not installed
    char_len: int

    @property
    def error_pct(self) -> float | None:
        """Signed percentage error: (estimate - true) / true * 100."""
        if self.tiktoken_count is None or self.tiktoken_count == 0:
            return None
        return (self.char_estimate - self.tiktoken_count) / self.tiktoken_count * 100


def _tiktoken_count(text: str, model: str = "gpt-4o") -> int | None:
    """Count tokens with tiktoken if available, else return None."""
    if not TIKTOKEN_AVAILABLE:
        return None
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


SAMPLE_TEXTS: list[tuple[str, str]] = [
    (
        "short_sentence",
        "Large language models process text as tokens, not characters.",
    ),
    (
        "medium_paragraph",
        (
            "An agent is a software system that perceives its environment, "
            "reasons about what to do, and takes actions to achieve its goals. "
            "Agentic AI systems combine a language model with tool-calling "
            "capabilities to complete multi-step tasks autonomously."
        ),
    ),
    (
        "technical_snippet",
        (
            "def call_llm(client, user_message, system_message='You are helpful.'):\n"
            "    request = CompletionRequest(\n"
            "        messages=[Message(role=Role.SYSTEM, content=system_message),\n"
            "                  Message(role=Role.USER, content=user_message)]\n"
            "    )\n"
            "    return client.complete(request)\n"
        ),
    ),
    (
        "long_prose",
        (
            "The context window is the total number of tokens a model can process "
            "in a single call, including both the prompt and the completion. Larger "
            "context windows cost more per call and have higher latency, but they "
            "allow you to include more history, more retrieved documents, or more "
            "complex system instructions. The practical limit is usually not the "
            "model's maximum context window -- it is the point at which performance "
            "starts to degrade. Research consistently shows that models attend more "
            "reliably to information at the beginning and end of a long context, "
            "and attention to the middle degrades as context length increases. "
            "For production systems, designing for a 60-70% context utilisation "
            "target gives headroom for dynamic content without hitting the ceiling."
        ),
    ),
    (
        "json_structured",
        '{"name": "tool_call", "arguments": {"operation": "multiply", "a": 15, "b": 7}, "id": "tc_001"}',
    ),
]


def run_comparison() -> list[TokenEstimate]:
    """Compare char-based estimate against tiktoken for each sample text."""
    results: list[TokenEstimate] = []
    for label, text in SAMPLE_TEXTS:
        results.append(
            TokenEstimate(
                label=label,
                text=text,
                char_estimate=count_tokens_estimate(text),
                tiktoken_count=_tiktoken_count(text),
                char_len=len(text),
            )
        )
    return results


def print_comparison(results: list[TokenEstimate]) -> None:
    """Print the comparison table."""
    tiktoken_col = "tiktoken" if TIKTOKEN_AVAILABLE else "tiktoken (not installed)"
    header = f"{'Sample':<22} {'chars':>7} {'estimate':>9} {tiktoken_col:>12} {'error %':>8}"
    print(header)
    print("-" * len(header))
    for r in results:
        tiktoken_str = str(r.tiktoken_count) if r.tiktoken_count is not None else "n/a"
        error_str = f"{r.error_pct:+.1f}%" if r.error_pct is not None else "n/a"
        print(
            f"{r.label:<22} {r.char_len:>7} {r.char_estimate:>9} {tiktoken_str:>12} {error_str:>8}"
        )
    print()


# ---------------------------------------------------------------------------
# Batch cost projection
# ---------------------------------------------------------------------------


@dataclass
class BatchProjection:
    """Projected cost for processing N documents with a given model."""

    model: str
    doc_count: int
    avg_prompt_tokens: int
    avg_completion_tokens: int
    total_cost_usd: float

    @property
    def cost_per_doc(self) -> float:
        return self.total_cost_usd / max(1, self.doc_count)


def project_batch_costs(
    doc_count: int = 10_000,
    avg_doc_tokens: int = 800,
    avg_completion_tokens: int = 200,
) -> list[BatchProjection]:
    """Project total cost for processing a batch of documents across all known models.

    Args:
        doc_count:              Number of documents to process.
        avg_doc_tokens:         Average tokens per document (prompt side).
        avg_completion_tokens:  Average tokens per completion.

    Returns:
        List of BatchProjection entries sorted by total cost ascending.
    """
    projections: list[BatchProjection] = []
    for model in MODEL_PRICING:
        per_doc_cost = estimate_cost(
            prompt_tokens=avg_doc_tokens,
            completion_tokens=avg_completion_tokens,
            model=model,
        )
        total_cost = per_doc_cost * doc_count
        projections.append(
            BatchProjection(
                model=model,
                doc_count=doc_count,
                avg_prompt_tokens=avg_doc_tokens,
                avg_completion_tokens=avg_completion_tokens,
                total_cost_usd=total_cost,
            )
        )
    projections.sort(key=lambda p: p.total_cost_usd)
    return projections


def print_batch_projections(projections: list[BatchProjection]) -> None:
    """Print batch cost projection table."""
    if not projections:
        return
    p = projections[0]
    print(
        f"Batch cost projection: {p.doc_count:,} documents, "
        f"{p.avg_prompt_tokens} prompt tokens, {p.avg_completion_tokens} completion tokens each"
    )
    print()
    header = f"{'Model':<35} {'$/doc':>10} {'Total cost':>12}"
    print(header)
    print("-" * len(header))
    for proj in projections:
        print(f"{proj.model:<35} ${proj.cost_per_doc:>9.6f} ${proj.total_cost_usd:>11.2f}")
    cheapest = projections[0]
    priciest = projections[-1]
    if len(projections) > 1:
        ratio = priciest.total_cost_usd / max(cheapest.total_cost_usd, 1e-12)
        print(f"\nCost spread: {cheapest.model} vs {priciest.model} = {ratio:.1f}x difference")
    print()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    print("=" * 60)
    print("Token estimation: character-based vs tiktoken")
    print("=" * 60)
    if not TIKTOKEN_AVAILABLE:
        print("(tiktoken not installed -- install with: pip install tiktoken)\n")
    results = run_comparison()
    print_comparison(results)

    print("=" * 60)
    print("Batch cost projection")
    print("=" * 60)
    projections = project_batch_costs()
    print_batch_projections(projections)

    # Vary document length to show sensitivity.
    print("Cost sensitivity to document length (10,000 docs, 200 completion tokens):")
    header = f"{'Doc tokens':>12} {'Model':<30} {'Total cost':>12}"
    print(header)
    print("-" * len(header))
    for doc_tokens in (200, 500, 1_000, 2_000, 4_000):
        for model in list(MODEL_PRICING.keys())[:2]:  # cheapest two for brevity
            per_doc = estimate_cost(doc_tokens, 200, model)
            total = per_doc * 10_000
            print(f"{doc_tokens:>12} {model:<30} ${total:>11.2f}")
    print()
    sys.exit(0)
