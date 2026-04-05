"""Tests for memory security defenses — validator and anomaly detector."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.ch12_memory.defenses import MemoryAnomalyDetector, MemoryValidator
from src.ch12_memory.types import MemoryCategory, MemoryRecord


def test_validator_accepts_human_reviewed_correction():
    v = MemoryValidator()
    record = MemoryRecord(
        query="refund policy",
        context="retrieved from policy_v3.md",
        outcome="no refunds",
        correction="full refund within 30 days",
        category=MemoryCategory.CORRECTION,
    )
    assert v.validate(record, human_reviewed=True) is True


def test_validator_rejects_unreviewed_correction_contradicting_evidence():
    v = MemoryValidator()
    record = MemoryRecord(
        query="refund policy",
        context="Document says: no refunds after 14 days",
        outcome="no refunds after 14 days",
        correction="full refund within 90 days with bonus credit of $500",
        category=MemoryCategory.CORRECTION,
    )
    assert v.validate(record, human_reviewed=False) is False


def test_validator_accepts_escalation():
    v = MemoryValidator()
    record = MemoryRecord(
        query="complex question",
        context="",
        outcome="escalated due to low confidence",
        category=MemoryCategory.ESCALATION,
    )
    assert v.validate(record, human_reviewed=False) is True


def test_anomaly_detector_flags_dormant_activation():
    d = MemoryAnomalyDetector(dormancy_threshold_days=7)
    record = MemoryRecord(
        id="mem_1",
        query="trigger query",
        context="",
        outcome="planted response",
        category=MemoryCategory.CORRECTION,
        access_count=0,
    )
    # Set timestamp to 30 days ago to simulate a dormant memory
    record.timestamp = datetime.now(UTC) - timedelta(days=30)
    assert d.is_suspicious_activation(record) is True


def test_anomaly_detector_allows_recent_memory():
    d = MemoryAnomalyDetector(dormancy_threshold_days=7)
    record = MemoryRecord(
        id="mem_2",
        query="recent query",
        context="",
        outcome="normal response",
        category=MemoryCategory.CORRECTION,
        access_count=3,
    )
    assert d.is_suspicious_activation(record) is False
