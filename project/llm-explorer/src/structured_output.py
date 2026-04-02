"""Structured output patterns (llm-explorer, Section 0a).

Demonstrates three practical patterns for extracting structured data from model output:

1. JSON mode: parse the full response as JSON (assumes the model returns only JSON).
2. Schema enforcement: validate parsed JSON against a Pydantic model.
3. Extraction with fallback: extract a specific field with a default on failure.

Uses MockClient for reproducibility -- no API key required.

Run with:
    python project/llm-explorer/src/structured_output.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# Path bootstrap for direct script execution.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pydantic import BaseModel, ValidationError, field_validator  # noqa: E402

from src.ch00.llm_basics import call_llm, parse_structured_output  # noqa: E402
from src.shared.model_client import MockClient  # noqa: E402
from src.shared.types import CompletionResponse, TokenUsage  # noqa: E402


# ---------------------------------------------------------------------------
# Pydantic schemas for structured extraction
# ---------------------------------------------------------------------------


class SentimentResult(BaseModel):
    """Expected output from a sentiment analysis request."""

    sentiment: str  # "positive", "negative", or "neutral"
    confidence: float  # 0.0 to 1.0
    summary: str

    @field_validator("sentiment")
    @classmethod
    def validate_sentiment(cls, v: str) -> str:
        allowed = {"positive", "negative", "neutral"}
        if v.lower() not in allowed:
            raise ValueError(f"sentiment must be one of {allowed}, got {v!r}")
        return v.lower()

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {v}")
        return v


class EntityExtractionResult(BaseModel):
    """Expected output from a named entity extraction request."""

    entities: list[dict[str, str]]  # [{"text": "...", "type": "..."}]
    entity_count: int

    @field_validator("entity_count")
    @classmethod
    def validate_count_matches_entities(cls, v: int, info: Any) -> int:
        entities = info.data.get("entities", [])
        if entities and v != len(entities):
            raise ValueError(
                f"entity_count ({v}) does not match len(entities) ({len(entities)})"
            )
        return v


class ClassificationResult(BaseModel):
    """Expected output from a document classification request."""

    category: str
    subcategory: str | None = None
    tags: list[str]
    requires_review: bool


# ---------------------------------------------------------------------------
# Pattern 1: JSON mode
# ---------------------------------------------------------------------------


async def demo_json_mode() -> None:
    """Pattern 1: Assume the model returns only JSON. Parse directly."""
    print("Pattern 1: JSON mode (model returns only JSON)")
    print("-" * 50)

    examples = [
        # Clean JSON response
        '{"status": "complete", "result": 42, "confidence": 0.97}',
        # JSON with surrounding prose (common failure mode)
        'Here is the result: {"status": "complete", "result": 42} Done.',
        # Invalid JSON (model hallucinated a non-JSON response)
        "The result is 42 with high confidence.",
    ]

    for raw_response in examples:
        client = MockClient(
            responses=[
                CompletionResponse(
                    content=raw_response,
                    model="mock",
                    usage=TokenUsage(prompt_tokens=20, completion_tokens=15, total_tokens=35),
                )
            ]
        )
        response = await call_llm(client, "Return the analysis as JSON.")
        parsed = parse_structured_output(response.content or "")

        status = "ok" if parsed else "failed"
        print(f"  [{status}] raw: {raw_response[:60]!r}")
        if parsed:
            print(f"       parsed: {parsed}")
        print()


# ---------------------------------------------------------------------------
# Pattern 2: Schema enforcement
# ---------------------------------------------------------------------------


async def demo_schema_enforcement() -> None:
    """Pattern 2: Validate parsed JSON against a Pydantic model."""
    print("Pattern 2: Schema enforcement (Pydantic validation)")
    print("-" * 50)

    test_cases = [
        (
            "valid response",
            '{"sentiment": "positive", "confidence": 0.92, "summary": "Clear endorsement with strong positive language."}',
            True,
        ),
        (
            "invalid sentiment value",
            '{"sentiment": "very_positive", "confidence": 0.88, "summary": "Enthusiastic review."}',
            False,
        ),
        (
            "confidence out of range",
            '{"sentiment": "negative", "confidence": 1.5, "summary": "Disappointed customer."}',
            False,
        ),
        (
            "missing required field",
            '{"sentiment": "neutral", "confidence": 0.61}',
            False,
        ),
    ]

    for label, raw_json, should_pass in test_cases:
        client = MockClient(
            responses=[
                CompletionResponse(
                    content=raw_json,
                    model="mock",
                    usage=TokenUsage(prompt_tokens=30, completion_tokens=20, total_tokens=50),
                )
            ]
        )
        response = await call_llm(client, "Analyse the sentiment of this review.")
        parsed = parse_structured_output(response.content or "")

        if parsed is None:
            print(f"  [parse_fail] {label}")
            print(f"    raw: {raw_json!r}")
            print()
            continue

        try:
            result = SentimentResult.model_validate(parsed)
            outcome = "pass" if should_pass else "unexpected_pass"
            print(f"  [{outcome}] {label}")
            print(f"    sentiment={result.sentiment}, confidence={result.confidence:.2f}")
        except ValidationError as exc:
            outcome = "expected_fail" if not should_pass else "unexpected_fail"
            first_error = exc.errors()[0]
            print(f"  [{outcome}] {label}")
            print(f"    validation error: {first_error['msg']}")
        print()


# ---------------------------------------------------------------------------
# Pattern 3: Extraction with fallback
# ---------------------------------------------------------------------------


async def demo_extraction_with_fallback() -> None:
    """Pattern 3: Extract a specific field from model output, with a safe default."""
    print("Pattern 3: Extraction with fallback")
    print("-" * 50)

    def extract_category(raw: str, default: str = "uncategorised") -> str:
        """Extract the 'category' field from raw model output, defaulting on failure."""
        parsed = parse_structured_output(raw)
        if parsed is None:
            return default
        try:
            result = ClassificationResult.model_validate(parsed)
            return result.category
        except ValidationError:
            # Partial extraction: try to get category even if the full schema fails.
            raw_category = parsed.get("category")
            if isinstance(raw_category, str) and raw_category.strip():
                return raw_category.strip()
            return default

    test_outputs = [
        (
            "well-formed output",
            '{"category": "technical", "subcategory": "infrastructure", "tags": ["cloud", "k8s"], "requires_review": false}',
        ),
        (
            "category only (other fields missing)",
            '{"category": "billing", "tags": []}',
        ),
        (
            "prose with embedded JSON",
            'Based on the content: {"category": "legal", "tags": ["contract"], "requires_review": true}',
        ),
        (
            "no JSON at all",
            "This looks like a billing question.",
        ),
    ]

    for label, raw_output in test_outputs:
        client = MockClient(
            responses=[
                CompletionResponse(
                    content=raw_output,
                    model="mock",
                    usage=TokenUsage(prompt_tokens=25, completion_tokens=18, total_tokens=43),
                )
            ]
        )
        response = await call_llm(client, "Classify this support ticket.")
        category = extract_category(response.content or "")
        print(f"  {label:<40} -> category={category!r}")
    print()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    async def _main() -> None:
        print("=" * 60)
        print("Structured output patterns")
        print("=" * 60)
        print()
        await demo_json_mode()
        await demo_schema_enforcement()
        await demo_extraction_with_fallback()

        print("Key observations:")
        print("  - JSON mode only works if the model returns pure JSON")
        print("  - parse_structured_output handles prose-wrapped JSON via regex")
        print("  - Pydantic validation catches bad enum values, range errors, missing fields")
        print("  - Extraction with fallback is the safest pattern for production")

    asyncio.run(_main())
