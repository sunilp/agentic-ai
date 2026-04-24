---
description: "Roadmap for the Agentic AI for Serious Engineers code companion repository."
---

# Roadmap

---

## Published

The book is available on [Amazon](https://www.amazon.com/dp/B0GVG6848F). Thirteen chapters across four parts covering the full lifecycle of building production agent systems -- from first principles through governance, security, memory, and protocols.

This site is the **code companion** -- working implementations, tests, diagrams, and evaluation evidence.

## Foundations (free)

Five hands-on sections published as a free pre-read for readers new to LLMs and agentic AI:

- **[How LLMs Actually Work](book/00a-how-llms-work.md)** -- APIs, tokens, context windows, hallucination
- **[From API Calls to Tool Use](book/00b-api-to-tools.md)** -- Function calling, schema validation, tool execution
- **[Your First Agent, No Framework](book/00c-first-agent.md)** -- Complete agent in 100 lines, end-to-end
- **[The Same Agent, With a Framework](book/00d-frameworks.md)** -- ADK and LangChain side-by-side with eval comparison
- **[Connecting Your Agent to MCP](book/00e-connecting-to-mcp.md)** -- Build an MCP server, connect to real tools and services

## Shipped in this repo

- **Working code** for every concept: tool registry, context pipeline, agent loop, workflow implementation, bounded agent, state management, multi-agent orchestration, approval gates, escalation engine, audit logging, eval harness, tracer, reliability hardening, cost profiler, security hardening, session memory, long-term memory, shared memory, memory security
- **3 end-to-end projects**: Document Intelligence Agent, Incident Runbook Agent, and Memory Agent
- **Eval harness** with gold dataset, rubric, scored comparison script, and failure buckets
- **130+ passing tests** across unit and integration suites
- **40+ architecture-grade diagrams** (hand-crafted SVGs)
- **Infrastructure**: pyproject.toml, Makefile, .env.example

## What might come next

- Code examples for Chapters 8-11 (metacognition, deployment, governance, security)
- Code examples for Chapter 13 (MCP server patterns, AIP delegation chains)
- Additional eval datasets and adversarial test suites
- Community contributions: real-world case studies, production deployment patterns

---

Content ships when it meets the quality bar. No timelines promised.
