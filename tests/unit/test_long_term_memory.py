"""Tests for Chapter 12 long-term memory with worthiness filter."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.ch12_memory.long_term_memory import LongTermMemory, MemoryWorthinessFilter
from src.ch12_memory.memory_store import MemoryStore
from src.ch12_memory.types import MemoryCategory, MemoryRecord


@pytest.fixture
def store(tmp_path):
    db_path = tmp_path / "test_ltm.db"
    s = MemoryStore(str(db_path))
    yield s
    s.close()


@pytest.fixture
def ltm(store):
    return LongTermMemory(store=store)


def test_store_correction(ltm):
    record_id = ltm.store_correction(
        query="What is the refund policy?",
        original_answer="No refunds allowed",
        corrected_answer="Full refund within 30 days",
        context="Retrieved from wrong document",
    )
    assert record_id is not None
    record = ltm.get(record_id)
    assert record.category == MemoryCategory.CORRECTION
    assert record.correction == "Full refund within 30 days"


def test_store_negative_retrieval(ltm):
    record_id = ltm.store_negative_retrieval(
        query="refund policy",
        document_source="internal_process_v2.md",
        reason="Internal process doc, not customer-facing policy",
    )
    record = ltm.get(record_id)
    assert record.category == MemoryCategory.NEGATIVE_RETRIEVAL


def test_retrieve_relevant_memories(ltm):
    ltm.store_correction(
        query="refund policy question",
        original_answer="wrong",
        corrected_answer="correct",
        context="ctx",
        embedding=[1.0, 0.0, 0.0, 0.0],
    )
    ltm.store_correction(
        query="shipping delay question",
        original_answer="wrong",
        corrected_answer="correct",
        context="ctx",
        embedding=[0.0, 1.0, 0.0, 0.0],
    )
    results = ltm.retrieve(query_embedding=[0.9, 0.1, 0.0, 0.0], top_k=1)
    assert len(results) == 1
    assert "refund" in results[0].query


def test_forget_memory(ltm):
    record_id = ltm.store_correction(
        query="test",
        original_answer="a",
        corrected_answer="b",
        context="c",
    )
    assert ltm.get(record_id) is not None
    ltm.forget(record_id)
    assert ltm.get(record_id) is None


def test_worthiness_filter_accepts_correction():
    f = MemoryWorthinessFilter()
    assert f.is_worthy(category=MemoryCategory.CORRECTION, confidence=0.5) is True


def test_worthiness_filter_rejects_routine_success():
    f = MemoryWorthinessFilter()
    assert f.is_worthy(category=MemoryCategory.HIGH_VALUE_SUCCESS, confidence=0.9) is False


def test_worthiness_filter_accepts_low_confidence_escalation():
    f = MemoryWorthinessFilter()
    assert f.is_worthy(category=MemoryCategory.ESCALATION, confidence=0.3) is True


def test_stale_flagging(ltm):
    old_timestamp = datetime.now(timezone.utc) - timedelta(days=31)
    record = MemoryRecord(
        query="old query",
        context="old context",
        outcome="old outcome",
        category=MemoryCategory.CORRECTION,
        timestamp=old_timestamp,
        embedding=[0.1, 0.2, 0.3, 0.4],
    )
    ltm._store.store(record)
    stale = ltm.find_stale(max_age_days=30)
    assert len(stale) >= 1
