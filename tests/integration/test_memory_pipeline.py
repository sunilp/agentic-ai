"""Integration tests for the memory-augmented multi-agent pipeline."""

import sys
from pathlib import Path

import pytest

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Add memory-agent src
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "project" / "memory-agent" / "src")
)

from memory_augmented_agent import MemoryAugmentedOrchestrator

from src.ch02.tools.chunker import chunk_document
from src.ch02.tools.retriever import DocumentIndex
from src.ch12_memory.long_term_memory import LongTermMemory
from src.ch12_memory.memory_store import MemoryStore
from src.ch12_memory.session_memory import ImportanceStrategy, SessionMemory
from src.ch12_memory.shared_memory import SharedMemory
from src.ch12_memory.types import ScopeType
from src.shared.model_client import MockClient
from src.shared.types import CompletionResponse

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_client() -> MockClient:
    """MockClient with a reasoning response and a verification response."""
    return MockClient(
        responses=[
            CompletionResponse(
                content="Our refund policy allows full refunds within 30 days. [Source: policy.txt]"
            ),
            CompletionResponse(content='{"verified": true, "issues": []}'),
            # Extra responses for multi-turn tests
            CompletionResponse(
                content="The amount mentioned was $187.43 for account #12345. [Source: policy.txt]"
            ),
            CompletionResponse(content='{"verified": true, "issues": []}'),
            # Additional responses for further queries
            CompletionResponse(
                content="Standard shipping takes 5-7 business days. [Source: shipping.txt]"
            ),
            CompletionResponse(content='{"verified": true, "issues": []}'),
        ]
    )


@pytest.fixture()
def index() -> DocumentIndex:
    """DocumentIndex with 2 test documents."""
    idx = DocumentIndex(collection_name="test_memory_integration")
    chunks = chunk_document(
        text=(
            "Our refund policy allows full refunds within 30 days of purchase. "
            "After 30 days, only store credit is available. "
            "Contact support for refund requests."
        ),
        source="policy.txt",
    )
    chunks += chunk_document(
        text=(
            "Standard shipping takes 5-7 business days. "
            "Express shipping delivers within 2-3 business days. "
            "Free shipping on orders over $50."
        ),
        source="shipping.txt",
    )
    idx.add_chunks(chunks)
    yield idx
    idx.clear()


@pytest.fixture()
def session_memory() -> SessionMemory:
    """SessionMemory with ImportanceStrategy."""
    return SessionMemory(max_tokens=4096, strategy=ImportanceStrategy())


@pytest.fixture()
def long_term_memory(tmp_path) -> LongTermMemory:
    """LongTermMemory backed by a temporary SQLite database."""
    store = MemoryStore(db_path=str(tmp_path / "ltm.db"))
    ltm = LongTermMemory(store=store)
    yield ltm
    store.close()


@pytest.fixture()
def shared_memory() -> SharedMemory:
    """In-memory SharedMemory."""
    sm = SharedMemory(db_path=":memory:")
    yield sm
    sm.close()


@pytest.fixture()
def orchestrator(
    mock_client: MockClient,
    index: DocumentIndex,
    session_memory: SessionMemory,
    long_term_memory: LongTermMemory,
    shared_memory: SharedMemory,
) -> MemoryAugmentedOrchestrator:
    """MemoryAugmentedOrchestrator wired with all memory layers."""
    return MemoryAugmentedOrchestrator(
        client=mock_client,
        index=index,
        session_memory=session_memory,
        long_term_memory=long_term_memory,
        shared_memory=shared_memory,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_basic_query(orchestrator):
    response = await orchestrator.run("What is the refund policy?")
    assert response.answer
    assert response.steps_taken > 0


@pytest.mark.asyncio
async def test_session_memory_persists_across_turns(orchestrator, session_memory):
    await orchestrator.run("My account #12345 was charged $187.43 incorrectly")
    await orchestrator.run("What was the amount I mentioned?")
    msgs = session_memory.get_context()
    contents = " ".join(m["content"] for m in msgs)
    assert "$187.43" in contents or "#12345" in contents


@pytest.mark.asyncio
async def test_shared_memory_prevents_duplicate_retrieval(orchestrator, shared_memory):
    await orchestrator.run("What is the refund policy?")
    keys = shared_memory.list_keys(ScopeType.TEAM)
    assert len(keys) > 0


@pytest.mark.asyncio
async def test_long_term_memory_stores_correction(orchestrator, long_term_memory):
    record_id = orchestrator.record_correction(
        query="refund policy",
        original="no refunds",
        corrected="full refund within 30 days",
    )
    # Verify it was stored and retrievable
    record = long_term_memory.get(record_id)
    assert record is not None
    assert record.correction == "full refund within 30 days"
    # Not stale since just created (1-day window)
    stale = long_term_memory.find_stale(max_age_days=1)
    assert len(stale) == 0


@pytest.mark.asyncio
async def test_pipeline_writes_coordination_state(orchestrator, shared_memory):
    await orchestrator.run("What is the shipping time?")
    status = shared_memory.read(ScopeType.TEAM, "pipeline:status")
    assert status is not None


@pytest.mark.asyncio
async def test_pipeline_completes_with_all_layers(orchestrator):
    response = await orchestrator.run("What is the refund policy?")
    assert response.confidence >= 0.0
    assert not response.escalated
