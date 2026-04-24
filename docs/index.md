---
description: "Code companion to Agentic AI for Serious Engineers. Working Python implementations, architecture diagrams, and evaluation harnesses for production-grade agent systems."
hide:
  - navigation
  - toc
---

<div style="text-align: center; margin: 0 auto 2rem;">
  <img src="assets/images/book-cover.jpg" alt="Agentic AI for Serious Engineers" style="max-width: 300px; width: 100%; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />
</div>

# Agentic AI for Serious Engineers

**A practical field guide to building reliable, evaluable, and production-grade agent systems**

<p style="text-align: center; margin: 1.5rem 0;">
  <a href="https://www.amazon.com/dp/B0GVG6848F" style="display: inline-block; padding: 0.75rem 2rem; background: #FF9900; color: #000; text-decoration: none; font-weight: 600; border-radius: 4px;">Get the Book on Amazon</a>
</p>

Most agentic AI material teaches you how to build an impressive demo. This book teaches engineers how to build agent systems that survive real-world constraints: unclear requirements, bad tool outputs, partial failures, prompt injection, and cost pressure.

Thirteen chapters across four parts. A single project that grows from a prototype to a governed, secured, memory-enabled system connected via MCP and A2A protocols. The thesis: agents are useful only when they earn their complexity.

This site is the **code companion**. It contains working Python implementations for every concept, 130+ passing tests, three end-to-end projects, and 40+ hand-crafted architecture diagrams.

## New to agentic AI?

Start with the **[Foundations](book/00a-how-llms-work.md)** -- five hands-on sections that take you from zero to building your first agent and connecting it to tools via MCP.

| # | Section | What you learn |
|---|---------|----------------|
| 0a | [How LLMs Actually Work](book/00a-how-llms-work.md) | The engineer's mental model: APIs, tokens, context, hallucination |
| 0b | [From API Calls to Tool Use](book/00b-api-to-tools.md) | Function calling, schema validation, giving the model hands |
| 0c | [Your First Agent, No Framework](book/00c-first-agent.md) | Build a complete agent in 100 lines. See it work. See it break. |
| 0d | [The Same Agent, With a Framework](book/00d-frameworks.md) | ADK and LangChain side-by-side. Eval comparison. Choose with data. |
| 0e | [Connecting Your Agent to MCP](book/00e-connecting-to-mcp.md) | Build an MCP server, connect your agent to real tools and services. |

## Chapters

**Part I: Building** -- From components to multi-agent systems

| # | Chapter | Focus |
|---|---------|-------|
| 1 | [What "Agentic" Actually Means](book/01-what-agentic-means.md) | Precise vocabulary: LLM app vs workflow vs agent vs multi-agent |
| 2 | [Tools, Context, and the Agent Loop](book/02-tools-context-agent-loop.md) | Building blocks: tool registry, context engineering, observe-think-act |
| 3 | [Workflow First, Agent Second](book/03-workflow-first-agent-second.md) | The most important architectural decision |
| 4 | [Multi-Agent Systems Without Theater](book/04-multi-agent-without-theater.md) | Coordination patterns, MCP, A2A, AIP protocols |

**Part II: Judging** -- Oversight, evaluation, and knowing when to stop

| # | Chapter | Focus |
|---|---------|-------|
| 5 | [Human-in-the-Loop as Architecture](book/05-human-in-the-loop.md) | Approval gates, escalation, and auditability |
| 6 | [Evaluating and Hardening Agents](book/06-evaluating-and-hardening.md) | Eval harnesses, tracing, reliability, cost, security |
| 7 | [When Not to Use Agents](book/07-when-not-to-use-agents.md) | The signature chapter -- judgment over hype |

**Part III: Operating** -- Production reality

| # | Chapter | Focus |
|---|---------|-------|
| 8 | [Metacognition and Self-Reflection](book/08-metacognition.md) | Loop detection, quality assessment, strategy switching |
| 9 | [Deploying and Scaling](book/09-deployment.md) | Durable execution, observability, autoscaling |
| 10 | [Governance and Auditability](book/10-governance.md) | Decision traces, compliance boundaries, risk tiers |
| 11 | [Security Deep Dive](book/11-security.md) | The Lethal Trifecta, defense in depth, red teaming |

**Part IV: Advanced Patterns**

| # | Chapter | Focus |
|---|---------|-------|
| 12 | [Memory Management](book/12-memory-management.md) | Session, long-term, shared memory, memory security |
| 13 | [Agent Protocols in Production](book/13-agent-protocols-in-production.md) | Enterprise MCP, A2A at scale, AIP delegation chains |

Chapter 1 is available as a **[free sample](book/01-what-agentic-means.md)**. The full book is on **[Amazon](https://www.amazon.com/dp/B0GVG6848F)**.

## Projects

Three end-to-end systems built incrementally through the chapters:

- **[Document Intelligence Agent](projects/doc-intelligence-agent.md)** -- Ingest documents, retrieve evidence, answer with citations, escalate on uncertainty
- **[Incident Runbook Agent](projects/incident-runbook-agent.md)** -- Inspect signals, search runbooks, propose remediation, request human approval
- **[Memory Agent](projects/memory-agent.md)** -- Memory-augmented pipeline with session, long-term, and shared memory layers

## Evidence

- **[Baseline Eval Report](proof/baseline-eval-report.md)** -- Gold dataset evaluation with rubric scoring
- **[Architecture Comparison](proof/workflow-vs-agent-comparison.md)** -- Workflow vs agent side-by-side metrics
- **[Trace Examples](proof/trace-example.md)** -- Structured execution traces with token accounting
- **[Failure Case Studies](proof/failure-cases.md)** -- Real failure analysis and lessons learned

---

[Get the book on Amazon](https://www.amazon.com/dp/B0GVG6848F) | [GitHub Repository](https://github.com/sunilp/agentic-ai) | [sunilprakash.com](https://sunilprakash.com)
