# Roadmap

---

## Published

The book is available on [Amazon](https://www.amazon.com/dp/B0GVG6848F). Seven chapters covering definitions, tool design, workflow-vs-agent architecture, multi-agent systems, human-in-the-loop, evaluation and hardening, and the judgment chapter on when not to use agents.

This repository is the **code companion** -- working implementations, tests, diagrams, and evaluation evidence.

## Shipped in this repo

- **Working code** for every concept: tool registry, context pipeline, agent loop, workflow implementation, bounded agent, state management, multi-agent orchestration, approval gates, escalation engine, audit logging, eval harness, tracer, reliability hardening, cost profiler, security hardening
- **2 end-to-end projects**: Document Intelligence Agent and Incident Runbook Agent
- **Eval harness** with gold dataset, rubric, scored comparison script, and failure buckets
- **52+ passing tests** across unit and integration suites
- **22 architecture-grade diagrams** (hand-crafted SVGs)
- **Infrastructure**: pyproject.toml, Makefile, .env.example

## What might come next

- Additional code examples for advanced topics (metacognition, durable execution, advanced memory)
- More end-to-end projects (Codebase Analyst, Data Analyst Agent)
- Community contributions: real-world case studies, additional eval datasets

---

Content ships when it meets the quality bar. No timelines promised.
