"""Long-term memory with worthiness filtering for Chapter 12.

Provides a higher-level API over :class:`MemoryStore` that knows how to
construct well-formed :class:`MemoryRecord` instances for corrections,
negative retrievals, and escalations.  A pluggable
:class:`MemoryWorthinessFilter` decides whether a given observation is
worth persisting at all -- routine high-confidence successes are discarded
to keep the memory lean and focused on genuinely informative experiences.
"""

from __future__ import annotations

from src.ch12_memory.memory_store import MemoryStore
from src.ch12_memory.types import MemoryCategory, MemoryRecord


_ALWAYS_STORE_CATEGORIES = frozenset(
    {
        MemoryCategory.CORRECTION,
        MemoryCategory.ESCALATION,
        MemoryCategory.NEGATIVE_RETRIEVAL,
    }
)


class MemoryWorthinessFilter:
    """Decide whether an observation is worth committing to long-term memory.

    *   CORRECTION, ESCALATION, and NEGATIVE_RETRIEVAL are always stored --
        they represent genuinely novel information the agent did not know.
    *   HIGH_VALUE_SUCCESS is only stored when the agent's confidence was
        *below* a threshold, indicating the agent solved something non-obvious.
        Routine, high-confidence successes are not worth remembering.
    """

    def __init__(self, success_confidence_threshold: float = 0.8) -> None:
        self._threshold = success_confidence_threshold

    def is_worthy(self, category: MemoryCategory, confidence: float) -> bool:
        """Return True if the observation should be persisted."""
        if category in _ALWAYS_STORE_CATEGORIES:
            return True
        if category == MemoryCategory.HIGH_VALUE_SUCCESS:
            return confidence < self._threshold
        return False


class LongTermMemory:
    """High-level facade for persisting and querying episodic memories.

    Wraps a :class:`MemoryStore` with convenience methods for the three
    primary memory categories (corrections, negative retrievals, and
    escalations) and optional worthiness pre-filtering.
    """

    def __init__(
        self,
        store: MemoryStore,
        worthiness_filter: MemoryWorthinessFilter | None = None,
    ) -> None:
        self._store = store
        self._worthiness_filter = worthiness_filter or MemoryWorthinessFilter()

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def filter(self) -> MemoryWorthinessFilter:
        """Return the active worthiness filter."""
        return self._worthiness_filter

    # ── Store helpers ─────────────────────────────────────────────────────

    def store_correction(
        self,
        query: str,
        original_answer: str,
        corrected_answer: str,
        context: str,
        embedding: list[float] | None = None,
    ) -> str:
        """Persist a correction memory and return its ID."""
        record = MemoryRecord(
            query=query,
            context=context,
            outcome=original_answer,
            correction=corrected_answer,
            category=MemoryCategory.CORRECTION,
            embedding=embedding or [],
        )
        return self._store.store(record)

    def store_negative_retrieval(
        self,
        query: str,
        document_source: str,
        reason: str,
        embedding: list[float] | None = None,
    ) -> str:
        """Persist a negative-retrieval memory and return its ID."""
        record = MemoryRecord(
            query=query,
            context=f"source={document_source}",
            outcome=reason,
            category=MemoryCategory.NEGATIVE_RETRIEVAL,
            embedding=embedding or [],
        )
        return self._store.store(record)

    def store_escalation(
        self,
        query: str,
        reason: str,
        context: str = "",
        embedding: list[float] | None = None,
    ) -> str:
        """Persist an escalation memory and return its ID."""
        record = MemoryRecord(
            query=query,
            context=context,
            outcome=reason,
            category=MemoryCategory.ESCALATION,
            embedding=embedding or [],
        )
        return self._store.store(record)

    # ── Retrieval ─────────────────────────────────────────────────────────

    def retrieve(
        self,
        query_embedding: list[float],
        top_k: int = 3,
    ) -> list[MemoryRecord]:
        """Two-pass retrieval: find similar records, then record access on each."""
        results = self._store.retrieve_similar(query_embedding, top_k=top_k)
        for record in results:
            self._store.record_access(record.id)
        return results

    def get(self, record_id: str) -> MemoryRecord | None:
        """Retrieve a single record by ID."""
        return self._store.get(record_id)

    # ── Maintenance ───────────────────────────────────────────────────────

    def forget(self, record_id: str) -> bool:
        """Delete a record from long-term memory."""
        return self._store.forget(record_id)

    def find_stale(self, max_age_days: int = 30) -> list[MemoryRecord]:
        """Return records with zero accesses older than *max_age_days*."""
        return self._store.find_stale(max_age_days=max_age_days)
