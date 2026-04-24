# Code Reference

Source code for all examples and projects. [View on GitHub](https://github.com/sunilp/agentic-ai/tree/master/src)

## Shared (`src/shared/`)

Utilities used across all chapters and projects.

| Module | Description |
|--------|-------------|
| `model_client.py` | Thin wrapper over the LLM API: handles retries, timeouts, and response parsing |
| `types.py` | Shared data types: Message, ToolCall, ToolResult, AgentState |
| `config.py` | Environment configuration: model names, API keys, default parameters |

## Chapter 2 (`src/ch02/`)

Building blocks: tool registry, context engineering, the agent loop.

| Module | Description |
|--------|-------------|
| `tool_registry.py` | Tool registration, schema generation, dispatch, and permission checking |
| `tools/` | Individual tools: document_loader, chunker, retriever, extractor |
| `context.py` | Context window management: budget tracking, trimming, priority ordering |
| `agent.py` | Observe-think-act loop implementation |
| `run.py` | CLI entry point for Chapter 2 examples |

## Chapter 3 (`src/ch03/`)

Workflow-first architecture: fixed pipeline vs bounded agent.

| Module | Description |
|--------|-------------|
| `workflow.py` | Deterministic pipeline: retrieve, build context, answer in sequence |
| `agent.py` | Bounded agent: can refine search and escalate, with step limits |
| `state.py` | Explicit state management: tracks what the agent has tried and seen |
| `compare.py` | Side-by-side comparison: runs both implementations on the same queries |

## Chapter 4 (`src/ch04_multiagent/`)

Multi-agent coordination: typed contracts, specialized agents, verification loop.

| Module | Description |
|--------|-------------|
| `contracts.py` | Typed message contracts for inter-agent communication |
| `agents.py` | RetrieverAgent, ReasoningAgent, VerifierAgent |
| `orchestrator.py` | Multi-agent coordinator with verification loop |
| `compare.py` | Single-agent vs multi-agent comparison runner |

## Chapter 5 (`src/ch05_hitl/`)

Human-in-the-loop: approval gates, escalation policy, structured audit logging.

| Module | Description |
|--------|-------------|
| `approval.py` | Approval gate middleware with auto-approve and human review |
| `escalation.py` | Escalation policy engine with per-risk-tier rules |
| `audit.py` | Append-only structured audit logging |

## Chapter 6 (`src/ch06/`)

Evaluation, observability, reliability, cost, and security.

| Module | Description |
|--------|-------------|
| `eval_harness.py` | Runs gold dataset through the agent, scores answers, produces failure buckets |
| `tracer.py` | Structured trace logging: captures every tool call, model call, and decision |
| `reliability.py` | Retry logic, timeout handling, fallback chains, circuit breakers |
| `cost_profiler.py` | Token counting, cost estimation, per-call and per-session tracking |
| `security.py` | Input sanitization, output validation, tool permission enforcement |

## Chapter 12 (`src/ch12_memory/`)

Memory management: session, long-term, shared memory, and security.

| Module | Description |
|--------|-------------|
| `session_memory.py` | Context management with importance-weighted truncation and compaction |
| `long_term_memory.py` | Persistent memory with worthiness filtering and two-pass retrieval |
| `shared_memory.py` | Multi-agent state coordination with scoped access and optimistic concurrency |
| `memory_validator.py` | Memory poisoning detection and validation at storage and retrieval time |
