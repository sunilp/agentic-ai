"""Memory security defenses: validation and anomaly detection.

Implements two guard-rail classes that sit in front of the memory pipeline:

* **MemoryValidator** — decides whether a candidate ``MemoryRecord`` should be
  persisted.  Human-reviewed corrections and operationally safe categories
  (ESCALATION, NEGATIVE_RETRIEVAL) pass automatically; unreviewed corrections
  are checked for suspicious numeric divergence from the source evidence.

* **MemoryAnomalyDetector** — flags dormant memories that suddenly activate
  (zero prior accesses after exceeding an age threshold), a common signal for
  memory-poisoning attacks.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from src.ch12_memory.types import MemoryCategory, MemoryRecord


class MemoryValidator:
    """Gate-keeps memory writes by validating records before persistence."""

    # Categories that are always safe to store regardless of review status.
    _ALWAYS_VALID: frozenset[MemoryCategory] = frozenset(
        {MemoryCategory.ESCALATION, MemoryCategory.NEGATIVE_RETRIEVAL}
    )

    def validate(self, record: MemoryRecord, human_reviewed: bool = False) -> bool:
        """Return *True* if *record* should be persisted, *False* otherwise.

        Rules (evaluated in order):
        1. ESCALATION and NEGATIVE_RETRIEVAL are always valid.
        2. Human-reviewed corrections are always valid.
        3. Unreviewed CORRECTIONs are rejected when the correction text
           contradicts the numeric evidence found in ``record.context``.
        4. Everything else is accepted.
        """
        if record.category in self._ALWAYS_VALID:
            return True

        if human_reviewed:
            return True

        if record.category == MemoryCategory.CORRECTION:
            evidence = record.context or ""
            correction = record.correction or ""
            if self._contradicts_evidence(evidence, correction):
                return False

        return True

    # ------------------------------------------------------------------
    @staticmethod
    def _contradicts_evidence(evidence: str, correction: str) -> bool:
        """Heuristic contradiction check based on numeric divergence.

        Extracts all integers from *evidence* and *correction*.  If
        *correction* introduces more **new** numbers than *evidence*
        originally contained, the correction is treated as suspicious.
        """
        evidence_numbers = set(re.findall(r"\d+", evidence))
        correction_numbers = set(re.findall(r"\d+", correction))

        if not evidence_numbers or not correction_numbers:
            return False

        new_numbers = correction_numbers - evidence_numbers
        if len(new_numbers) > len(evidence_numbers):
            return True

        return False


class MemoryAnomalyDetector:
    """Detects suspicious activation patterns in the memory store."""

    def __init__(self, dormancy_threshold_days: int = 7) -> None:
        self._threshold = timedelta(days=dormancy_threshold_days)

    def is_suspicious_activation(self, record: MemoryRecord) -> bool:
        """Return *True* if *record* looks like a dormant-memory attack.

        A memory is suspicious when it has **never been accessed**
        (``access_count == 0``) and is older than the configured dormancy
        threshold.
        """
        if record.access_count != 0:
            return False

        age = datetime.now(UTC) - record.timestamp
        return age > self._threshold
