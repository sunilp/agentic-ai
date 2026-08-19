"""Heuristic output-quality scoring, run per request.

Three dimensions:

* citation coverage -- what share of factual sentences carry a citation
* evidence overlap  -- what share of the answer's content words appear in the
  retrieved evidence
* hedging           -- whether the answer hedges when the evidence is thin,
  and commits when the evidence is solid

This is the cheap screen that runs on every request. It catches the obvious
cases: fluent answers built from training data rather than from the evidence
in front of them. It is not a grounding oracle. Layer a sampled evaluation
harness behind it, and inference-time detection in front of it if you control
the serving layer.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from src.shared.types import Citation

HEDGE_TERMS = frozenset(
    [
        "may",
        "might",
        "could",
        "appears",
        "suggests",
        "likely",
        "unclear",
        "possibly",
        "seems",
        "insufficient",
        "cannot determine",
        "not stated",
        "no evidence",
    ]
)

CITATION_PATTERN = re.compile(r"\[\s*(?:\d+|[Dd]oc\s*\d+|[Ss]ource\s*\d+)\s*\]")

STOP_WORDS = frozenset(
    """a an and are as at be by for from has have in is it its of on or that the
    this to was were will with we you they i""".split()
)


class QualityReport(BaseModel):
    """Per-request quality assessment."""

    score: float = 0.0
    citation_coverage: float = 0.0
    evidence_overlap: float = 0.0
    hedging: float = 0.0
    issues: list[str] = Field(default_factory=list)

    @property
    def is_grounded(self) -> bool:
        return not self.issues


def _sentences(text: str) -> list[str]:
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    return parts


def _content_words(text: str) -> set[str]:
    words = {w.strip(".,;:!?()[]\"'").lower() for w in text.split()}
    words.discard("")
    return {w for w in words if w not in STOP_WORDS}


class OutputQualityChecker:
    """Scores an answer against the evidence that was supposed to support it."""

    def __init__(
        self,
        coverage_weight: float = 0.45,
        overlap_weight: float = 0.45,
        hedging_weight: float = 0.10,
        overlap_floor: float = 0.5,
    ) -> None:
        self.coverage_weight = coverage_weight
        self.overlap_weight = overlap_weight
        self.hedging_weight = hedging_weight
        self.overlap_floor = overlap_floor

    def check(self, answer: str, citations: list[Citation] | None = None) -> QualityReport:
        citations = citations or []
        sentences = _sentences(answer)
        issues: list[str] = []

        if not sentences:
            return QualityReport(issues=["empty answer"])

        cited = sum(1 for s in sentences if CITATION_PATTERN.search(s))
        coverage = cited / len(sentences)

        evidence_words: set[str] = set()
        for c in citations:
            evidence_words |= _content_words(c.text)
        answer_words = _content_words(CITATION_PATTERN.sub("", answer))
        overlap = len(answer_words & evidence_words) / len(answer_words) if answer_words else 0.0

        hedged = sum(1 for s in sentences if any(t in s.lower() for t in HEDGE_TERMS))
        hedging = hedged / len(sentences)

        # Hedge when the evidence is thin; commit when it is solid.
        thin_evidence = overlap < self.overlap_floor
        appropriate = 1.0 if (thin_evidence and hedging > 0) or (not thin_evidence) else 0.0

        if not citations:
            issues.append("no evidence attached")
        if coverage < 0.5:
            issues.append(f"citation coverage {coverage:.2f} below 0.50")
        if thin_evidence:
            issues.append(f"evidence overlap {overlap:.2f} below {self.overlap_floor:.2f}")
        if thin_evidence and hedging == 0.0:
            issues.append("confident claims on thin evidence")

        score = (
            self.coverage_weight * coverage
            + self.overlap_weight * overlap
            + self.hedging_weight * appropriate
        )
        return QualityReport(
            score=round(score, 4),
            citation_coverage=round(coverage, 4),
            evidence_overlap=round(overlap, 4),
            hedging=round(hedging, 4),
            issues=issues,
        )
