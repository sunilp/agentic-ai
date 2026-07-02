"""Deterministic workflow implementation of the document intelligence task.

This is the SAME task as the agent, but as a fixed pipeline.
No decisions, no loops, no autonomy. Just: retrieve -> context -> answer.
"""

from __future__ import annotations

import time

from src.ch02.context import ContextPipeline
from src.ch02.tools.retriever import DocumentIndex
from src.shared.model_client import ModelClient
from src.shared.types import (
    AgentResponse,
    CompletionRequest,
    TokenUsage,
)


class DocumentWorkflow:
    """Fixed pipeline: retrieve -> build context -> answer."""

    def __init__(
        self,
        client: ModelClient,
        index: DocumentIndex,
        context_pipeline: ContextPipeline | None = None,
    ):
        self._client = client
        self._index = index
        self._context = context_pipeline or ContextPipeline()

    async def run(self, query: str, top_k: int = 5) -> AgentResponse:
        """Execute the fixed workflow pipeline."""
        start = time.monotonic()

        citations = self._index.retrieve(query, top_k=top_k)
        messages = self._context.build(query=query, citations=citations)
        request = CompletionRequest(messages=messages, temperature=0.0)
        response = await self._client.complete(request)

        elapsed = (time.monotonic() - start) * 1000

        avg_relevance = (
            sum(c.relevance_score for c in citations) / len(citations) if citations else 0.0
        )

        return AgentResponse(
            answer=response.content or "Could not generate an answer.",
            citations=citations,
            confidence=min(0.95, avg_relevance) if citations else 0.1,
            escalated=avg_relevance < 0.3,
            escalation_reason="Low retrieval relevance" if avg_relevance < 0.3 else None,
            steps_taken=1,
            token_usage=response.usage or TokenUsage(),
            latency_ms=elapsed,
        )
