# Agentic AI for Serious Engineers

<p align="center">
  <img src="docs/assets/cover.svg" alt="Agentic AI for Serious Engineers" width="360" />
</p>

<p align="center">
  <a href="https://www.amazon.com/dp/B0GVG6848F"><img src="https://img.shields.io/badge/Get_the_Book-Amazon-FF9900?style=flat-square&logo=amazon" alt="Available on Amazon"></a>
  <a href="https://github.com/sunilp/agentic-ai"><img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License: MIT"></a>
</p>

**A practical field guide to building reliable, evaluable, and production-grade agent systems.**

**[Get the book on Amazon](https://www.amazon.com/dp/B0GVG6848F)**

---

This repository is the **code companion** to *Agentic AI for Serious Engineers*. It contains working Python implementations, architecture diagrams, evaluation harnesses, and end-to-end projects that accompany the book.

The book teaches you when to build an agent, when not to, and how to make the ones you build survive production. The code here lets you run every concept hands-on.

## New to agentic AI?

Start with the **Foundations** -- four hands-on sections that take you from zero to building your first agent. No framework required. No prior AI experience needed.

| # | Section | What you learn |
|---|---------|----------------|
| 0a | [How LLMs Actually Work](docs/book/00a-how-llms-work.md) | The engineer's mental model: APIs, tokens, context, hallucination |
| 0b | [From API Calls to Tool Use](docs/book/00b-api-to-tools.md) | Function calling, schema validation, giving the model hands |
| 0c | [Your First Agent, No Framework](docs/book/00c-first-agent.md) | Build a complete agent in 100 lines. See it work. See it break. |
| 0d | [The Same Agent, With a Framework](docs/book/00d-frameworks.md) | ADK and LangChain side-by-side. Eval comparison. Choose with data. |

## What is in this repo

- **Working code for every chapter** -- tool registries, context pipelines, agent loops, multi-agent orchestration, human-in-the-loop gates, evaluation harnesses, and security hardening
- **Two end-to-end projects** -- Document Intelligence Agent and Incident Runbook Agent
- **52+ passing tests** -- unit and integration tests for every module
- **22 architecture diagrams** -- hand-crafted SVGs covering system types, coordination patterns, trust boundaries, and failure surfaces
- **Evaluation evidence** -- baseline eval reports, architecture comparisons, traced execution examples, and failure case studies

## The Book

Seven chapters covering the full lifecycle of building production agent systems.

| # | Chapter | Focus |
|---|---------|-------|
| 1 | What "Agentic" Actually Means | Precise definitions, comparison table, decision map |
| 2 | Tools, Context, and the Agent Loop | Tool registry, context pipeline, first working agent |
| 3 | Workflow First, Agent Second | Same task two ways -- the key architectural decision |
| 4 | Multi-Agent Systems Without Theater | Coordination patterns that solve real problems, not demos |
| 5 | Human-in-the-Loop as Architecture | Approval gates, escalation policy, and audit trails |
| 6 | Evaluating and Hardening Agents | Eval, tracing, reliability, cost, security |
| 7 | When Not to Use Agents | The signature chapter -- building engineering judgment |

**[Read the free sample chapter](docs/book/01-what-agentic-means.md)** or **[get the full book on Amazon](https://www.amazon.com/dp/B0GVG6848F)**.

## Getting Started

```bash
# Install
make install

# Run tests (52+ passing)
make test

# Run the Document Intelligence Agent
make run

# Run the eval harness
make eval
```

Copy `.env.example` to `.env` and add your API key before running.

## Repo Structure

```
├── src/                           # Working examples, per-chapter
│   ├── shared/                    # Model client, config, common types
│   ├── ch02/                      # Tool registry, context pipeline, first agent
│   ├── ch03/                      # Workflow vs agent comparison, state, planning
│   ├── ch04_multiagent/           # Multi-agent contracts, agents, orchestrator
│   ├── ch05_hitl/                 # Approval gates, escalation, audit logging
│   └── ch06/                      # Eval harness, traces, reliability, security
├── project/                       # End-to-end projects
│   ├── doc-intelligence-agent/    # Ingestion, retrieval, citations, escalation
│   └── incident-runbook-agent/    # Multi-agent with human approval
├── tests/
│   ├── unit/                      # Component-level tests
│   └── integration/               # Pipeline and system tests
├── docs/
│   ├── book/                      # Sample chapter + chapter summaries
│   ├── diagrams/                  # Architecture-grade SVG diagrams
│   ├── projects/                  # Project documentation
│   └── proof/                     # Evaluation evidence and analysis
├── pyproject.toml                 # Dependencies
├── Makefile                       # install, test, eval, run, compare, serve
└── PRINCIPLES.md                  # Engineering principles
```

## Who This Is For

Backend engineers, platform engineers, staff+ engineers, software architects, and technical leads building AI systems for production use.

**Assumed baseline:** APIs, Python, software architecture, services, testing, databases, production experience.

**Not assumed:** Transformers, embeddings, agent orchestration, AI evaluation. These are taught in the book.

## Author

Written by [Sunil Prakash](https://sunilprakash.com) -- engineering leader focused on enterprise AI systems, governance, and agent architecture.

## License

Code in this repository is licensed under MIT. The book text is copyright Sunil Prakash -- [available on Amazon](https://www.amazon.com/dp/B0GVG6848F).
