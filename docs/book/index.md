# Agentic AI for Serious Engineers

**Build trustworthy AI systems, not demos.**

---

<div style="text-align: center; margin: 2rem 0;">
  <img src="../assets/images/book-cover.jpg" alt="Agentic AI for Serious Engineers book cover" style="max-width: 280px; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />
</div>

This book teaches you when to build an agent, when not to, and how to make the ones you build survive production. It threads a single project from first principles through production hardening, using working Python code that you can read, run, and adapt.

Chapter 1 is available here as a free sample. The full book is available on [Amazon](https://www.amazon.com/dp/B0GVG6848F).

## Foundations

Not familiar with LLMs or the basics of function calling? Start here before diving into the chapters. These four sections take you from zero to a working agent -- no framework required.

| # | Section | What you learn |
|---|---------|----------------|
| 0a | [How LLMs Actually Work](00a-how-llms-work.md) | The engineer's mental model: APIs, tokens, context, hallucination |
| 0b | [From API Calls to Tool Use](00b-api-to-tools.md) | Function calling, schema validation, giving the model hands |
| 0c | [Your First Agent, No Framework](00c-first-agent.md) | Build a complete agent in 100 lines. See it work. See it break. |
| 0d | [The Same Agent, With a Framework](00d-frameworks.md) | ADK and LangChain side-by-side. Eval comparison. Choose with data. |
| 0e | [Connecting Your Agent to MCP](00e-connecting-to-mcp.md) | Build an MCP server, connect your agent to real tools and services. |

**[Start with the Foundations](00a-how-llms-work.md)** if you are new to agentic AI. Skip ahead to Chapter 1 if you are already comfortable with LLM APIs and tool calling.

## Chapters

**Part I: Building**

| # | Title | Focus |
|---|-------|-------|
| 1 | [What "Agentic" Actually Means](01-what-agentic-means.md) | Precise definitions, comparison table, decision map |
| 2 | [Tools, Context, and the Agent Loop](02-tools-context-agent-loop.md) | Tool registry, context pipeline, first working agent |
| 3 | [Workflow First, Agent Second](03-workflow-first-agent-second.md) | Same task two ways -- the key architectural decision |
| 4 | [Multi-Agent Systems Without Theater](04-multi-agent-without-theater.md) | Coordination patterns, MCP, A2A, AIP protocols |

**Part II: Judging**

| # | Title | Focus |
|---|-------|-------|
| 5 | [Human-in-the-Loop as Architecture](05-human-in-the-loop.md) | Approval gates, escalation, and audit trails |
| 6 | [Evaluating and Hardening Agents](06-evaluating-and-hardening.md) | Eval, tracing, reliability, cost, security |
| 7 | [When Not to Use Agents](07-when-not-to-use-agents.md) | The signature chapter -- engineering judgment |

**Part III: Operating**

| # | Title | Focus |
|---|-------|-------|
| 8 | Metacognition and Self-Reflection | Loop detection, quality assessment, strategy switching |
| 9 | Deploying and Scaling Agent Systems | Durable execution, observability, autoscaling |
| 10 | Agent Governance and Auditability | Decision traces, compliance boundaries, risk tiers |
| 11 | Security Deep Dive | The Lethal Trifecta, defense in depth, red teaming |

**Part IV: Advanced Patterns**

| # | Title | Focus |
|---|-------|-------|
| 12 | [Memory Management](12-memory-management.md) | Session, long-term, shared memory, memory security |
| 13 | [Agent Protocols in Production](13-agent-protocols-in-production.md) | Enterprise MCP, A2A at scale, AIP delegation chains |

## The Running Example: Document Intelligence Agent

Every chapter uses the same project -- a Document Intelligence Agent that ingests documents, answers questions with citations, and knows when it does not know enough to answer. The project code lives in `src/` and the project documentation lives in the [Document Intelligence Agent](../projects/doc-intelligence-agent.md) project page.

## Get the Full Book

<a href="https://www.amazon.com/dp/B0GVG6848F" style="display: inline-block; padding: 0.75rem 2rem; background: #FF9900; color: #000; text-decoration: none; font-weight: 600; border-radius: 4px;">Available on Amazon</a>
