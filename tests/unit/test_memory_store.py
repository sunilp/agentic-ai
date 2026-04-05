"""Tests for Chapter 12 memory store."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.ch12_memory.memory_store import MemoryStore
from src.ch12_memory.types import MemoryCategory, MemoryRecord


def _make_record(
    query: str = "test query",
    context: str = "test context",
    outcome: str = "test outcome",
    correction: str | None = None,
    category: MemoryCategory = MemoryCategory.HIGH_VALUE_SUCCESS,
    embedding: list[float] | None = None,
    timestamp: datetime | None = None,
) -> MemoryRecord:
    return MemoryRecord(
        query=query,
        context=context,
        outcome=outcome,
        correction=correction,
        category=category,
        embedding=embedding or [0.1, 0.2, 0.3, 0.4],
        timestamp=timestamp or datetime.now(timezone.utc),
    )


@pytest.fixture
def store(tmp_path):
    db_path = tmp_path / "test_memories.db"
    s = MemoryStore(str(db_path))
    yield s
    s.close()


class TestStoreAndRetrieveById:
    def test_store_and_retrieve_by_id(self, store: MemoryStore):
        record = _make_record(query="What is RAG?", outcome="Retrieval-Augmented Generation")
        record_id = store.store(record)

        assert record_id is not None
        retrieved = store.get(record_id)
        assert retrieved is not None
        assert retrieved.query == "What is RAG?"
        assert retrieved.outcome == "Retrieval-Augmented Generation"
        assert retrieved.category == MemoryCategory.HIGH_VALUE_SUCCESS
        assert retrieved.embedding == pytest.approx([0.1, 0.2, 0.3, 0.4], abs=1e-6)


class TestRetrieveSimilar:
    def test_retrieve_similar(self, store: MemoryStore):
        # Store two records with distinct embeddings
        rec_a = _make_record(query="alpha", embedding=[1.0, 0.0, 0.0, 0.0])
        rec_b = _make_record(query="beta", embedding=[0.0, 1.0, 0.0, 0.0])
        store.store(rec_a)
        store.store(rec_b)

        # Query close to rec_a
        results = store.retrieve_similar(query_embedding=[0.9, 0.1, 0.0, 0.0], top_k=1)
        assert len(results) == 1
        assert results[0].query == "alpha"

        # Query close to rec_b
        results = store.retrieve_similar(query_embedding=[0.1, 0.9, 0.0, 0.0], top_k=1)
        assert len(results) == 1
        assert results[0].query == "beta"


class TestForgetRemovesRecord:
    def test_forget_removes_record(self, store: MemoryStore):
        record = _make_record(query="ephemeral")
        record_id = store.store(record)

        assert store.get(record_id) is not None
        assert store.forget(record_id) is True
        assert store.get(record_id) is None

    def test_forget_nonexistent_returns_false(self, store: MemoryStore):
        assert store.forget("nonexistent-id") is False


class TestIncrementAccessCount:
    def test_increment_access_count(self, store: MemoryStore):
        record = _make_record()
        record_id = store.store(record)

        store.record_access(record_id, usefulness_delta=0.5)
        retrieved = store.get(record_id)
        assert retrieved is not None
        assert retrieved.access_count == 1
        assert retrieved.usefulness_score == pytest.approx(0.5)

        store.record_access(record_id, usefulness_delta=0.3)
        retrieved = store.get(record_id)
        assert retrieved is not None
        assert retrieved.access_count == 2
        assert retrieved.usefulness_score == pytest.approx(0.8)


class TestFlagStaleRecords:
    def test_flag_stale_records(self, store: MemoryStore):
        # Record created 60 days ago with zero access
        old_time = datetime.now(timezone.utc) - timedelta(days=60)
        old_record = _make_record(query="ancient", timestamp=old_time)
        store.store(old_record)

        # Recent record
        recent_record = _make_record(query="fresh")
        store.store(recent_record)

        stale = store.find_stale(max_age_days=30)
        assert len(stale) == 1
        assert stale[0].query == "ancient"


class TestStats:
    def test_stats_returns_correct_totals(self, store: MemoryStore):
        store.store(_make_record(query="first"))
        store.store(_make_record(query="second"))

        result = store.stats()

        assert result.total_records == 2
        assert result.stale_records == 2  # neither has been accessed
        assert result.avg_usefulness == pytest.approx(0.0)
        assert result.avg_access_count == pytest.approx(0.0)
