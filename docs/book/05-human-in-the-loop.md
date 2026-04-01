---
description: "Human-in-the-loop as a first-class architectural decision. Approval gates, escalation policies, audit logging, and the Incident Runbook Agent."
---

# Chapter 5: Human-in-the-Loop as Architecture

HITL done poorly is worse than no human at all. It creates the appearance of oversight without the substance. This chapter treats human-in-the-loop as a first-class architectural concern, not an afterthought.

## What this chapter covers

- **The three primitives** -- approval gates, escalation policies, audit trails
- **Design guidance** -- structuring when and how humans intervene
- **The working example: Incident Runbook Agent** -- multi-agent with human approval before remediation
- **When HITL is security theater** -- rubber-stamping vs real oversight
- **Cost of HITL vs value of HITL** -- the tradeoff analysis most teams skip
- **Building for auditability** -- decision trails useful for debugging, compliance, and improvement
- **Failure modes** -- what breaks in human-agent interaction

## Code companion

The working code for this chapter is in [`src/ch05_hitl/`](https://github.com/sunilp/agentic-ai/tree/main/src/ch05_hitl):

- `approval.py` -- Approval gate implementation
- `escalation.py` -- Escalation policy engine
- `audit.py` -- Audit logging system

See the [Incident Runbook Agent](../projects/incident-runbook-agent.md) project page for the full system architecture.

## Get the full chapter

The complete chapter text is available in the book.

[Get the book on Amazon](https://www.amazon.com/dp/B0GVG6848F){ .md-button .md-button--primary }
