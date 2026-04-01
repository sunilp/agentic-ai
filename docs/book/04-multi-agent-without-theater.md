---
description: "When multi-agent systems are justified and when they are complexity theater. Patterns, coordination overhead, and honest cost analysis."
---

# Chapter 4: Multi-Agent Systems Without Theater

Multi-agent systems are where the gap between demo and production is widest. This chapter draws the line between coordination patterns that solve real problems and complexity theater that looks impressive but fails at 2 AM.

## What this chapter covers

- **When multi-agent is justified** -- the specific conditions where a single agent cannot hold the task
- **When multi-agent is theater** -- recognizing unnecessary decomposition
- **Core patterns** -- orchestrator, message contracts, and agent specialization
- **The working example** -- retriever, reasoner, and verifier on the document intelligence task
- **The comparison** -- single-agent vs multi-agent on accuracy, cost, and latency
- **Coordination overhead and cost explosion** -- the real price of multi-agent
- **Failure modes** -- what goes wrong when agents coordinate

## Code companion

The working code for this chapter is in [`src/ch04_multiagent/`](https://github.com/sunilp/agentic-ai/tree/main/src/ch04_multiagent):

- `contracts.py` -- Agent message contracts
- `agents.py` -- Specialized agents (retriever, reasoner, verifier)
- `orchestrator.py` -- Multi-agent orchestration
- `compare.py` -- Single vs multi-agent comparison
- `run.py` -- Executable example

## Get the full chapter

The complete chapter text is available in the book.

[Get the book on Amazon](https://www.amazon.com/dp/B0GVG6848F){ .md-button .md-button--primary }
