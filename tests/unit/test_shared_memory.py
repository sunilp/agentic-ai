"""Tests for Chapter 12 shared memory with scopes and optimistic concurrency."""

from __future__ import annotations

import pytest

from src.ch12_memory.shared_memory import SharedMemory, VersionConflictError
from src.ch12_memory.types import ScopeType


@pytest.fixture
def sm(tmp_path):
    db_path = tmp_path / "test_shared.db"
    mem = SharedMemory(str(db_path))
    yield mem
    mem.close()


def test_write_and_read(sm):
    sm.write(ScopeType.TEAM, "ticket:123:status", "in_progress", agent_id="triage")
    value = sm.read(ScopeType.TEAM, "ticket:123:status")
    assert value == "in_progress"


def test_version_increments_on_update(sm):
    sm.write(ScopeType.TEAM, "key1", "value1", agent_id="agent_a")
    entry = sm.read_entry(ScopeType.TEAM, "key1")
    assert entry.version == 1
    sm.write(ScopeType.TEAM, "key1", "value2", agent_id="agent_a", expected_version=1)
    entry = sm.read_entry(ScopeType.TEAM, "key1")
    assert entry.version == 2
    assert entry.value == "value2"


def test_version_conflict_raises(sm):
    sm.write(ScopeType.TEAM, "key1", "value1", agent_id="agent_a")
    sm.write(ScopeType.TEAM, "key1", "value2", agent_id="agent_b", expected_version=1)
    with pytest.raises(VersionConflictError):
        sm.write(ScopeType.TEAM, "key1", "value3", agent_id="agent_a", expected_version=1)


def test_claim_succeeds_when_unclaimed(sm):
    owner = sm.claim(ScopeType.TEAM, "ticket:456:assigned_to", "resolver_1")
    assert owner == "resolver_1"


def test_claim_returns_existing_owner(sm):
    sm.claim(ScopeType.TEAM, "ticket:456:assigned_to", "resolver_1")
    owner = sm.claim(ScopeType.TEAM, "ticket:456:assigned_to", "resolver_2")
    assert owner == "resolver_1"


def test_scope_isolation(sm):
    sm.write(ScopeType.AGENT, "private_key", "secret", agent_id="agent_a")
    sm.write(ScopeType.TEAM, "private_key", "shared", agent_id="agent_b")
    assert sm.read(ScopeType.AGENT, "private_key") == "secret"
    assert sm.read(ScopeType.TEAM, "private_key") == "shared"


def test_read_nonexistent_returns_none(sm):
    assert sm.read(ScopeType.TEAM, "does_not_exist") is None


def test_list_keys_in_scope(sm):
    sm.write(ScopeType.TEAM, "ticket:1:status", "open", agent_id="a")
    sm.write(ScopeType.TEAM, "ticket:2:status", "closed", agent_id="a")
    sm.write(ScopeType.AGENT, "private", "data", agent_id="a")
    keys = sm.list_keys(ScopeType.TEAM)
    assert len(keys) == 2
    assert "ticket:1:status" in keys
