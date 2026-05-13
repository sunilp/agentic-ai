---
description: "Working end-to-end tutorials on the current agentic AI stack. Anthropic Claude, AWS Bedrock AgentCore, MCP, A2A. Each Recipe is reproducible, verified on a specific date, and shipped with a runnable sample."
hide:
  - toc
---

# Recipes

Working end-to-end tutorials on the current agentic AI stack. Each Recipe is reproducible, verified on a specific date, and shipped with a runnable sample in the [companion repo](https://github.com/sunilp/agentic-ai).

The bar is "you can build this in an afternoon." Not "you can read about how someone else did it."

## Recent recipes

| # | Title | Stack | Verified |
|---|-------|-------|----------|
| [R-001](001-strands-on-agentcore-runtime.md) | Build and deploy your first Strands agent on AgentCore Runtime | AWS Bedrock AgentCore, Strands | 2026-05-13 |
| _R-002_ | OAuth 3LO with AgentCore Identity | Bedrock AgentCore Identity, Cognito or Auth0 | _shipping 2026-06-03_ |
| _R-003_ | Expose an MCP server as tools via AgentCore Gateway | AgentCore Gateway, MCP | _shipping 2026-06-13_ |
| _R-004_ | Prompt caching and cross-region inference for Claude on Bedrock | Bedrock, Claude 4.x family | _shipping 2026-06-24_ |

## What a Recipe is

Every Recipe follows the same anatomy:

- **Prerequisites** -- exact versions, exact accounts, exact permissions
- **The flow** -- step by step, with code that runs
- **Gotchas** -- the failure modes that cost you an afternoon
- **Verification** -- how you know it actually works
- **Sample** -- a link to the full working code in the repo
- **Verified on** -- a date and a version. If the docs drift, the Recipe gets reverified or retired

Recipes are written against GA features. Preview features get a footnote, not a tutorial.

## The Anthropic + AWS focus

Most Recipes in the first wave target the Anthropic + AWS stack, because that is the production path most enterprises are actually taking. Bedrock AgentCore reached GA across all components in October 2025. The `@aws/agentcore` CLI is the canonical entry point as of April 2026. Most blog posts on the open web still teach the legacy starter toolkit. Recipes here track current docs and current SDKs.
