---
description: "How to evaluate and harden production agent systems. Metrics, adversarial testing, regression suites, and the difference between opinions and evidence."
---

# Chapter 6: Evaluating and Hardening Agents

You have built an agent. You have opinions about whether it works. But opinions are not evidence, and in production, only evidence counts. This chapter covers the five layers that turn a prototype into a production system.

## What this chapter covers

- **Evaluation** -- gold datasets, rubric scoring, failure bucketing, and regression suites
- **Observability** -- structured traces, token accounting, latency decomposition
- **Reliability** -- retries, checkpointing, crash recovery, graceful degradation
- **Cost management** -- token profiling, budget controls, architecture-level cost optimization
- **Security** -- prompt injection, tool abuse, data exfiltration, least privilege enforcement
- **Before and after hardening** -- concrete metrics showing the difference
- **Failure modes in this chapter's code** -- what breaks during hardening

## Code companion

The working code for this chapter is in [`src/ch06/`](https://github.com/sunilp/agentic-ai/tree/main/src/ch06):

- `eval_harness.py` -- Gold dataset and rubric scoring
- `tracer.py` -- Structured tracing
- `reliability.py` -- Retry and recovery patterns
- `cost_profiler.py` -- Token and cost tracking
- `security.py` -- Prompt injection and tool abuse detection

See the [Baseline Eval Report](../proof/baseline-eval-report.md) and [Failure Case Studies](../proof/failure-cases.md) for real evaluation data.

## Get the full chapter

The complete chapter text is available in the book.

[Get the book on Amazon](https://www.amazon.com/dp/B0GVG6848F){ .md-button .md-button--primary }
