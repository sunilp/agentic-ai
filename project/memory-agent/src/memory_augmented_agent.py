"""Memory-augmented multi-agent orchestrator.

Extends the Chapter 4 multi-agent pipeline with all three memory layers
from Chapter 12: session memory (sliding context window), long-term memory
(episodic corrections and escalations), and shared memory (cross-agent
coordination state and cached retrieval results).

The pipeline flow:
1. Record the query in session memory.
2. Write pipeline state to shared memory (TEAM scope).
3. Check shared memory for cached retrieval results.
4. Retrieve via RetrieverAgent (or use cache).
5. Reason via ReasoningAgent.
6. Verify via VerifierAgent (with retry loop).
7. On verification failure, write rejection to shared memory.
8. Record the response in session memory.
9. Update pipeline status to "completed".
"""

from __future__ import annotations

import hashlib
import json
import time

from src.ch02.tools.retriever import DocumentIndex
from src.ch04_multiagent.agents import ReasoningAgent, RetrieverAgent, VerifierAgent
from src.ch04_multiagent.contracts import (
    ReasoningRequest,
    RetrievalRequest,
    VerificationRequest,
)
from src.ch12_memory.long_term_memory import LongTermMemory
from src.ch12_memory.session_memory import SessionMemory
from src.ch12_memory.shared_memory import SharedMemory
from src.ch12_memory.types import ScopeType
from src.shared.model_client import ModelClient
from src.shared.types import AgentResponse, TokenUsage


def _query_hash(query: str) -> str:
    """SHA256 hash of the query string, truncated to 12 characters."""
    return hashlib.sha256(query.encode("utf-8")).hexdigest()[:12]


def _merge_all_usage(*usages: TokenUsage) -> TokenUsage:
    return TokenUsage(
        prompt_tokens=sum(u.prompt_tokens for u in usages),
        completion_tokens=sum(u.completion_tokens for u in usages),
        total_tokens=sum(u.total_tokens for u in usages),
    )


class MemoryAugmentedOrchestrator:
    """Coordinates retriever, reasoner, and verifier agents with three memory layers.

    Extends the base MultiAgentOrchestrator from Chapter 4 by adding:
    - Session memory: tracks the conversation across turns.
    - Long-term memory: stores corrections and escalations for future reference.
    - Shared memory: caches retrieval results and coordinates pipeline state.
    """

    def __init__(
        self,
        client: ModelClient,
        index: DocumentIndex,
        session_memory: SessionMemory,
        long_term_memory: LongTermMemory,
        shared_memory: SharedMemory,
        max_verification_rounds: int = 2,
    ) -> None:
        self._retriever = RetrieverAgent(index)
        self._reasoner = ReasoningAgent(client)
        self._verifier = VerifierAgent(client)
        self._max_rounds = max_verification_rounds
        self._session_memory = session_memory
        self._long_term_memory = long_term_memory
        self._shared_memory = shared_memory

    async def run(self, query: str, top_k: int = 5) -> AgentResponse:
        """Execute the full pipeline with memory augmentation."""
        start = time.monotonic()
        steps = 0
        qhash = _query_hash(query)

        # Record query in session memory
        self._session_memory.add_message({"role": "user", "content": query})

        # Write pipeline state to shared memory (TEAM scope)
        self._shared_memory.write(
            ScopeType.TEAM,
            "pipeline:status",
            "running",
            agent_id="orchestrator",
            reason=f"Processing query: {qhash}",
        )
        self._shared_memory.write(
            ScopeType.TEAM,
            f"pipeline:query:{qhash}",
            query,
            agent_id="orchestrator",
        )

        # Step 1: Retrieve -- check shared memory cache first
        cache_key = f"retrieval:{qhash}"
        cached = self._shared_memory.read(ScopeType.TEAM, cache_key)

        if cached is not None:
            # Use cached retrieval results -- deserialize citations
            retrieval_data = json.loads(cached)
            from src.shared.types import Citation

            citations = [Citation(**c) for c in retrieval_data]
            from src.ch04_multiagent.contracts import RetrievalResult

            retrieval = RetrievalResult(
                citations=citations,
                chunks_searched=top_k,
            )
        else:
            retrieval = await self._retriever.run(
                RetrievalRequest(query=query, top_k=top_k)
            )
            # Cache retrieval results in shared memory
            citation_dicts = [c.model_dump() for c in retrieval.citations]
            self._shared_memory.write(
                ScopeType.TEAM,
                cache_key,
                json.dumps(citation_dicts),
                agent_id="retriever",
                reason="Cache retrieval results",
            )
        steps += 1

        # Step 2: Reason
        reasoning = await self._reasoner.run(
            ReasoningRequest(query=query, citations=retrieval.citations)
        )
        steps += 1

        # Step 3: Verify (with retry loop)
        verified = False
        verification_rounds = 0

        while not verified and verification_rounds < self._max_rounds:
            verification = await self._verifier.run(
                VerificationRequest(
                    answer=reasoning.answer,
                    cited_sources=reasoning.cited_sources,
                    citations=retrieval.citations,
                )
            )
            steps += 1
            verification_rounds += 1

            if verification.verified:
                verified = True
            else:
                # Write rejection to shared memory
                self._shared_memory.write(
                    ScopeType.TEAM,
                    f"verification:rejection:{qhash}:{verification_rounds}",
                    json.dumps(verification.issues),
                    agent_id="verifier",
                    reason="Verification failed",
                )

                # Re-reason with feedback
                feedback_query = (
                    f"{query}\n\nPrevious answer had issues: "
                    f"{', '.join(verification.issues)}. "
                    f"Please correct and re-answer using only the provided evidence."
                )
                reasoning = await self._reasoner.run(
                    ReasoningRequest(
                        query=feedback_query, citations=retrieval.citations
                    )
                )
                steps += 1

        elapsed = (time.monotonic() - start) * 1000
        total_usage = _merge_all_usage(
            self._retriever.total_usage,
            self._reasoner.total_usage,
            self._verifier.total_usage,
        )

        avg_relevance = (
            sum(c.relevance_score for c in retrieval.citations)
            / len(retrieval.citations)
            if retrieval.citations
            else 0.0
        )

        confidence = min(0.95, avg_relevance) if verified else avg_relevance * 0.5

        response = AgentResponse(
            answer=reasoning.answer,
            citations=retrieval.citations,
            confidence=confidence,
            escalated=confidence < 0.3,
            escalation_reason="Low confidence after memory-augmented pipeline"
            if confidence < 0.3
            else None,
            steps_taken=steps,
            token_usage=total_usage,
            latency_ms=elapsed,
        )

        # Record response in session memory
        self._session_memory.add_message(
            {"role": "assistant", "content": response.answer}
        )

        # Update pipeline status to "completed"
        self._shared_memory.write(
            ScopeType.TEAM,
            "pipeline:status",
            "completed",
            agent_id="orchestrator",
            reason=f"Completed query: {qhash}",
        )

        return response

    def record_correction(
        self,
        query: str,
        original: str,
        corrected: str,
        embedding: list[float] | None = None,
    ) -> str:
        """Store a correction via long-term memory and return the record ID."""
        return self._long_term_memory.store_correction(
            query=query,
            original_answer=original,
            corrected_answer=corrected,
            context=f"query_hash={_query_hash(query)}",
            embedding=embedding,
        )
