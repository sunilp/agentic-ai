---
description: "How tool-using agents work: function calling, context window management, the agent loop, and writing a working agent without a framework."
---

# Chapter 2: Tools, Context, and the Agent Loop

This chapter gives you the building blocks of a working agent system. You build a tool-using agent from scratch -- not a framework wrapper, but code you understand and can modify.

## What this chapter covers

- **An LLM primer for systems engineers** -- what matters for production, not theory
- **Tools as contracts** -- function calling with validation, permissions, and error handling
- **Context engineering** -- system prompts, retrieval context, grounding, injection boundaries
- **The agent loop** -- the observe-think-act cycle and what makes it work or fail
- **Failure modes in this chapter's code** -- what breaks and why
- **Building a working agent** -- a complete implementation without reaching for a framework

## Code companion

The working code for this chapter is in [`src/ch02/`](https://github.com/sunilp/agentic-ai/tree/main/src/ch02):

- `tool_registry.py` -- Tool registry implementation
- `context.py` -- Context pipeline
- `agent.py` -- First working agent
- `tools/` -- Document chunking, loading, extraction, and retrieval

Run it: `make run`

## Get the full chapter

The complete chapter text is available in the book.

[Get the book on Amazon](https://www.amazon.com/dp/B0GVG6848F){ .md-button .md-button--primary }
