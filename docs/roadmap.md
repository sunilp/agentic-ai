---
description: "Roadmap for the Agentic AI for Serious Engineers code companion repository."
---

# Roadmap

---

## Published

The book is available on [Amazon](https://www.amazon.com/dp/B0GVG6848F). Seven chapters covering the full lifecycle of building production agent systems.

This repository is the **code companion** -- working implementations, tests, diagrams, and evaluation evidence.

## Foundations (pre-read)

Four hands-on sections published as a free pre-read for readers new to LLMs and agentic AI:

- **[How LLMs Actually Work](book/00a-how-llms-work.md)** -- APIs, tokens, context windows, hallucination
- **[From API Calls to Tool Use](book/00b-api-to-tools.md)** -- Function calling, schema validation, tool execution
- **[Your First Agent, No Framework](book/00c-first-agent.md)** -- Complete agent in 100 lines, end-to-end
- **[The Same Agent, With a Framework](book/00d-frameworks.md)** -- ADK and LangChain side-by-side with eval comparison

## Shipped in this repo

- **Working code** for every concept: tool registry, context pipeline, agent loop, workflow implementation, bounded agent, state management, multi-agent orchestration, approval gates, escalation engine, audit logging, eval harness, tracer, reliability hardening, cost profiler, security hardening
- **2 end-to-end projects**: Document Intelligence Agent and Incident Runbook Agent
- **Eval harness** with gold dataset, rubric, scored comparison script, and failure buckets
- **52+ passing tests** across unit and integration suites
- **22 architecture-grade diagrams** (hand-crafted SVGs)
- **Infrastructure**: pyproject.toml, Makefile, .env.example

## Part IV: Advanced Patterns (bonus chapters)

New chapters extending the book's operating patterns into advanced territory:

- **[Chapter 12: Memory Management](book/12-memory-management.md)** -- Session memory, long-term learning, multi-agent coordination, and memory security
- More chapters planned

## What might come next

- Additional code examples for advanced topics
- More end-to-end projects
- Community contributions: real-world case studies, additional eval datasets

---

Content ships when it meets the quality bar. No timelines promised.
