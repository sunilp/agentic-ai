# Foundations: Pre-Read Design Spec

**Date:** 2026-04-02
**Status:** Draft
**Author:** Sunil Prakash

---

## Overview

A four-section "Foundations" pre-read integrated into the existing Agentic AI for Serious Engineers code companion repo and MkDocs site. Positioned before Chapter 1 in the book navigation, it serves as the on-ramp for developers who are new to building with LLMs and agentic systems.

The Foundations content is free, open, and designed to funnel readers seamlessly into the Amazon book. The reading path: Foundations (free, 4 sections) -> Chapter 1 (free sample) -> Chapters 2-7 (buy the book on Amazon).

## Problem Statement

Most beginners encounter agentic AI through fragmented, noisy resources: framework-specific tutorials, shallow demo posts, or deep ML theory. There is no opinionated, framework-neutral, engineering-first guide that takes a developer from "I know Python but not LLMs" to "I understand agents well enough to make real decisions." This gap causes engineers to either give up or build on foundations they don't understand.

### What this is NOT

This is not a book about how LLMs are built internally. There are excellent resources for that (Raschka's *LLMs from Scratch* is the best). This is about how to build production systems with LLMs as components. The reader never needs to understand transformers, attention heads, or training. They need to understand what happens when they send text to an API, what breaks, and how to engineer around it.

## Target Audience

Two profiles, served by the same content:

1. **Backend/systems engineer, zero LLM experience.** Knows Python, APIs, databases, production systems. Has never called an OpenAI or Anthropic API. Needs the mental model built from scratch.

2. **Developer who has played with ChatGPT and maybe a tutorial.** Has sent prompts, maybe tried LangChain once. Confused by the noise, lacks a coherent mental model. Needs clarity and strong opinions, not another introduction.

Both profiles need the same thing: a coherent model built from the ground up, fast. Profile A gets introduced properly. Profile B gets the "oh, that's how it all fits together" moment they never got from scattered tutorials.

## Voice and Tone

Direct, warm, opinionated. Like a senior engineer explaining things to a smart colleague over coffee, with occasional contrarian stances that cut through noise.

**Rules:**
- No hedging. "It depends" is banned without immediately following with "here's what I'd do."
- Strong opinions stated as opinions, not facts. "I think X is wrong because Y."
- Kill sacred cows early. "You don't need a vector database. You don't need LangChain. You need to understand what happens when you send text to an API."
- Concrete over abstract. Every concept gets a code example within 2 paragraphs.
- Failure modes shown inline, not in a separate section. "Run this, watch it break, now you understand why."
- Warm enough to be inviting, opinionated enough to be memorable and shareable.

## Structure

Four sections, integrated into the existing "The Book" nav as a "Foundations" sub-section before the numbered chapters.

| # | File | Title | Core Question | Words | Visuals |
|---|------|-------|---------------|-------|---------|
| 0a | `book/00a-how-llms-work.md` | How LLMs Actually Work | "What is this thing I'm building with?" | ~3,000 | 4 SVGs |
| 0b | `book/00b-api-to-tools.md` | From API Calls to Tool Use | "How do I go from text to the model taking actions?" | ~3,500 | 3 SVGs |
| 0c | `book/00c-first-agent.md` | Your First Agent, No Framework | "What does an agent look like in raw code?" | ~3,000 | 4 SVGs |
| 0d | `book/00d-frameworks.md` | The Same Agent, With a Framework | "How do frameworks help, and what do they hide?" | ~3,000 | 3 SVGs |

**Total:** ~12,500 words, ~2 hour read including running code. 14 hand-crafted SVG diagrams.

All code is fully runnable. Each section has a companion project in `project/` for deep dives.

---

## Section 0a: How LLMs Actually Work

**Purpose:** Build the mental model that everything else rests on. Not transformer math. The engineer's working model.

**Opens with:** "You don't need to understand attention heads to build with LLMs. You need to understand five things. Here they are."

### Content

1. **The API contract.** You send text, you get text back. That's it. Everything else (agents, RAG, chains) is built on top of this one operation. Show a raw API call (curl, then Python). "This is the foundation. If you understand this, you understand 80% of what frameworks are doing."

2. **Tokens, not words.** What tokenization means for you as an engineer. Why "128K token context window" is both more and less than it sounds. Show token counting. Show cost math. "Every token costs money. Every token adds latency. This is the unit of your budget."

3. **The context window is your entire working memory.** System prompt, user message, conversation history, retrieved documents, tool results -- all competing for one fixed-size bucket. Show what happens when context overflows (quality degrades silently, model ignores instructions). The reader instantly sees: it's all one pool.

4. **Why it hallucinates (and why you can't prompt it away).** Completion vs reasoning. The model predicts the next likely token, not checks facts. This is not a bug to fix; it's the architecture. "Every mitigation for hallucination is engineering, not prompting. Grounding, validation, eval -- these are code solutions, not prompt solutions."

5. **Temperature and sampling.** What temperature actually controls. When to use 0 (deterministic tasks) vs higher (creative tasks). "For agents, use temperature 0 or near-zero. You want predictable decisions, not creative ones."

6. **Structured output.** Getting JSON/typed responses reliably. Response format, function calling schema. "This is the bridge between 'text generator' and 'system component.' When the model returns structured data, you can write normal code around it."

**Closing:** "You now have a mental model of the machine you're building with. It takes text, returns text, costs money per token, has a fixed memory, and confidently makes things up. Every engineering decision from here forward is about working within -- and around -- these constraints."

### Code Examples (4-5, all runnable)
- Raw API call (Python, using Anthropic/OpenAI SDK)
- Token counting and cost calculation
- Context window overflow demo (show quality degradation)
- Structured output with response schema
- Temperature comparison (same prompt, different temperatures)

### Visuals (4 SVGs)

1. **The API Contract** -- Simple flow diagram. "You send text -> API -> You get text back." Three boxes, one arrow each direction. Agents, RAG, chains shown as layers built on top.

2. **The Context Window** -- Stacked bar / bucket diagram. System prompt, few-shot examples, retrieved docs, conversation history, tool results all competing for one fixed-size bucket. Shows what gets pushed out when it overflows.

3. **Token Cost Calculator** -- Annotated table visual. A typical agent request broken down: prompt tokens, completion tokens, cost per call, calls per task, total. Concrete numbers.

4. **Why It Hallucinates** -- Two-panel comparison. Left: "What you think is happening" (model checking facts). Right: "What is actually happening" (model predicting likely next token). Simple, slightly humorous, immediately clarifying.

### Companion Project
`project/llm-explorer/` -- Token counting, context window limits, hallucination detection, structured output. All as runnable experiments with actual measurements.

---

## Section 0b: From API Calls to Tool Use

**Purpose:** Bridge the gap from "I can call an API" to "the model can take actions in my system." This is where most beginners get lost. This section makes function calling mechanical, not magical.

**Opens with:** "In the last section, the model could only talk. In this one, it learns to do things. The difference is smaller than you think -- about 15 lines of code."

### Content

1. **Prompting as engineering, not art.** System prompts are code. Treat them like code: version them, test them, review them. Show a bad prompt vs a good prompt for the same task, with measurable quality difference. "If your prompt engineering process is 'try things until it works,' you're debugging without logs."

2. **Few-shot examples are your type system.** When the model needs to follow a pattern, show it the pattern. This is not a hack; it's the most reliable way to control output shape. Show how 2-3 examples dramatically change output quality.

3. **Function calling from scratch.** Demystify it completely. Show the JSON schema that tells the model what tools exist. Show the model's response when it wants to call a tool. Show your code executing that tool call. "There is no magic. The model outputs JSON that says 'call this function with these arguments.' Your code does the calling." Walk through the full cycle: define tool -> model selects it -> you execute it -> you return the result.

4. **Schema validation is your safety net.** The model will hallucinate arguments. It will pass a string where you need an integer. It will invent parameters that don't exist. Show Pydantic validation on tool inputs. Show what happens without it (runtime crash) vs with it (graceful error).

5. **Multiple tools and selection.** Give the model 3-4 tools. Watch it choose. Show when it chooses wrong. "Tool descriptions are your API documentation for the model. Write them like you'd write docs for a junior developer who takes everything literally."

6. **The gap this doesn't cover.** "You now have a system that can take actions. But it takes them once. It can't look at the result and decide what to do next. That's the loop. That's what makes it an agent. Next section."

**Closing:** A working tool-using system (not an agent yet) that can answer questions using 3-4 tools. The reader sees exactly where the limitation is -- single turn, no reasoning loop.

### Code Examples (5-6, all runnable)
- System prompt engineering (bad vs good, with output comparison)
- Few-shot prompting (with/without examples comparison)
- Function calling: full cycle (schema definition, model response, execution, result return)
- Pydantic validation on tool inputs (with/without validation comparison)
- Multi-tool system with 3-4 tools
- Tool selection failure example

### Visuals (3 SVGs)

1. **The Function Calling Cycle** -- Circular flow diagram. Your code -> sends schema + prompt -> Model -> returns "call this function" -> Your code executes it -> returns result -> Model. The full round trip.

2. **Tool Selection: Right vs Wrong** -- Two-panel before/after. Left: model picks right tool (green). Right: model picks wrong tool or hallucinates arguments (red). Same query, different outcomes. Shows WHY validation matters.

3. **The Single-Turn Ceiling** -- Flow diagram with a wall. Tool-using system flow that hits a wall: "Got result. Can't look at it and decide what to do next." Arrow pointing right to "This is where agents start." Creates visual anticipation for 0c.

### Companion Project
`project/tool-using-assistant/` -- A practical tool-using system (calculator, web search, file reader) with schema validation, error handling, logging.

---

## Section 0c: Your First Agent, No Framework

**Purpose:** The reader builds a complete working agent from raw Python. Every line explained. They see it work, see it fail, fix it, and understand why the loop is what makes it an agent.

**Opens with:** "You have a system that can call tools. But it calls them once and stops. What if it could look at the result, decide it's not enough, and try again? That's an agent. The entire concept is a while loop with an LLM inside it. Let's build one."

### Content

1. **The loop in 20 lines.** The bare agent loop. Observe (assemble context), think (call LLM), act (execute tool or return answer), repeat. "This is the entire architecture. Everything else -- every framework, every SDK, every 'agent platform' -- is a wrapper around this loop."

2. **Building it step by step:**
   - The system prompt that tells the model it's an agent with tools
   - The observation assembly (how you pack context into the prompt each iteration)
   - The decision parsing (did the model want to call a tool or return an answer?)
   - The tool execution and result injection
   - The loop termination (budget, stop condition, or answer produced)

3. **Run it on a real task.** A research-style task: "Find information about X, synthesize what you find, cite your sources." Watch the agent search, read, search again, synthesize. Show the full trace.

4. **Watch it fail.** Give it tasks that trigger failure modes:
   - The infinite loop (agent keeps searching without converging)
   - The hallucinated tool call (model invents a function that doesn't exist)
   - The confident wrong answer (model stops too early with bad evidence)

   "These are not edge cases. These are the default behaviors of an agent without engineering discipline. Every one of these failures is what the book teaches you to prevent."

5. **Add basic guardrails.** Iteration budget, input validation, simple logging. Show how 10 lines of engineering turns a fragile demo into something that fails gracefully. "This is 10% of what production hardening looks like. Chapter 6 gives you the other 90%."

6. **The code in full.** The complete agent, ~100-120 lines, with every line commented. No hidden utilities. No imports from libraries that do the hard work. "You can read this top to bottom in 10 minutes and understand everything."

**Closing:** "You just built an agent. It works. It also breaks in predictable ways. You added basic guardrails that help, but you made a dozen judgment calls by instinct -- how many tools, how big the budget, when to stop, what to do when confidence is low. Chapter 1 gives you the precise vocabulary to think about these decisions. The rest of the book gives you the engineering to get them right."

### Code Examples
- The bare agent loop (~20 lines, annotated)
- Step-by-step build (system prompt, observation, decision parsing, tool execution, termination)
- Full working agent (~100-120 lines, every line commented)
- Failure demonstrations (3 distinct failure modes)
- Guardrails addition (~10 lines that add budget, validation, logging)

### Visuals (4 SVGs)

1. **The Agent Loop** -- Circular diagram. Observe -> Think -> Act -> back to Observe. With iteration counter and budget indicator. The core visual of the entire pre-read.

2. **Agent Trace Waterfall** -- Vertical timeline. Step 1: searched for X (tokens: 340, 0.8s). Step 2: read result, searched for Y (tokens: 520, 1.1s). Step 3: synthesized answer (tokens: 280, 0.6s). Total: 1,140 tokens, $0.04, 2.5s. Shows what "running an agent" looks like in practice.

3. **Three Failure Modes** -- Three-panel red diagram. Panel 1: infinite loop (circular arrow, spinning). Panel 2: hallucinated tool call (model invents a function). Panel 3: confident wrong answer (green checkmark on red output). Each scannable in 2 seconds.

4. **Before/After Guardrails** -- Split panel. Left: raw agent failures (red). Right: same agent with budget + validation + logging (green). 10 lines of code, visual difference.

### Companion Project
`project/research-agent/` -- The full agent with expanded tool set, proper error handling, logging, and example queries.

---

## Section 0d: The Same Agent, With a Framework

**Purpose:** Now that the reader understands every moving piece, show how frameworks help and what they hide. Same agent, three implementations (raw, Google ADK, LangChain). Side-by-side comparison with eval scores and cost data.

**Opens with:** "You built an agent from scratch. You understand the loop, the tools, the context assembly, the failure modes. Now let's rebuild it with a framework and see what changes. Spoiler: the hard parts don't disappear. They just move."

### Content

1. **Why frameworks exist (honest version).** "Frameworks solve real problems: tool registration boilerplate, conversation history management, retry logic, tracing. They also create real problems: magic you can't debug, abstractions that leak under pressure, upgrade churn. The point is to know what you're trading."

2. **Google ADK -- the primary walkthrough:**
   - Rebuild the research agent in ADK (~40 lines vs the raw 100)
   - Walk through what ADK does for you: tool registration, agent loop, context management
   - Show the tracing: "run this and look at the trace. Every tool call, every decision, every token count. This is what observability looks like."
   - Show eval with ADK: run the same test queries against both implementations (raw and ADK), compare accuracy, cost, latency
   - "The framework version is shorter. Is it better? Look at the numbers. Look at the traces. Make your own call."

3. **LangChain -- the comparison:**
   - Same agent in LangChain (~35 lines)
   - Key philosophical differences: chain-based composition vs ADK's agent-native approach
   - What LangChain makes easier (huge ecosystem, many integrations)
   - What LangChain makes harder (debugging chains, understanding what happens under abstraction, version churn)
   - Side-by-side code: raw vs ADK vs LangChain for the same operation

4. **The three-way comparison:**

   | Dimension | Raw | ADK | LangChain |
   |-----------|-----|-----|-----------|
   | Lines of code | ~100 | ~40 | ~35 |
   | Debug a failure | Read your code | Read traces | Read chains + source |
   | Add a new tool | Write a function | Decorate + register | Wrap in Tool class |
   | Eval integration | Build it yourself | Built-in | LangSmith (separate) |
   | Lock-in | None | Google ecosystem | LangChain ecosystem |
   | Best for | Learning, unusual needs | Production, need tracing | Prototyping, need integrations |

5. **The honest take:**
   - "If you're building something serious, pick a framework that gives you visibility, not convenience. Traces matter more than fewer lines of code."
   - "If you're learning, build raw first. Always. Then move to a framework. Never the other way around."
   - "If your team already uses LangChain, that's fine. Understand what it's doing (you now can), and add the engineering discipline the framework doesn't give you."
   - "If you're starting fresh, I'd reach for ADK. It's opinionated about the right things (tracing, eval) and stays out of your way on the rest."

6. **Eval as a mindset, not a tool:**
   - Show a simple eval: 5 test queries, expected answers, scored automatically
   - Run it against all three implementations
   - "The numbers don't lie. This is how you make framework decisions -- with data, not blog posts. Chapter 6 goes deep."

**Closing:** "You've now built the same agent three ways. You understand what happens at every level -- from the raw API call through the loop through the framework abstractions. You know what frameworks give you, what they take away, and how to evaluate both. You're ready for the book. Chapter 1 gives you the vocabulary to think precisely about what you just built. The rest of the book gives you the engineering discipline to build it for production."

### Code Examples
- ADK agent (~40 lines, annotated)
- LangChain agent (~35 lines, annotated)
- Side-by-side comparison (same operation in all three)
- Eval script (5 test queries, scoring, comparison output)
- Trace output examples (ADK trace vs raw logging)

### Visuals (3 SVGs)

1. **Framework Layer Diagram** -- Stacked layers. Bottom: raw Python (you control everything). Middle: ADK (handles loop + tracing). Top: LangChain (handles loop + chains + integrations). Each layer shows what it adds (green) AND what it hides (amber).

2. **Three-Way Comparison Dashboard** -- Side-by-side metrics card. Raw vs ADK vs LangChain: lines of code, accuracy score, cost per query, avg latency, debuggability. One glance tells you the tradeoffs.

3. **Decision Flowchart: Which Path?** -- Simple decision tree. "Are you learning?" -> Raw. "Building for production?" -> "Need tracing/eval built in?" -> ADK. "Need 50+ integrations fast?" -> LangChain. 4-5 nodes, clear endpoints.

### Companion Project
`project/framework-comparison/` -- All three implementations, shared eval dataset, comparison script that outputs accuracy/cost/latency table, trace output examples.

---

## Visual Design System

### Principles for Stress-Mode Readability
- One concept per visual, never two
- Large labels, minimal text
- Consistent color language: green = good/safe, red = bad/danger, blue = neutral/info, amber = caution
- Every diagram has a one-line caption that states the takeaway, not just the title
- Hand-crafted SVGs matching the existing 22 diagrams in the repo

### Code Callout Boxes
Every code example gets a "what just happened" callout box -- a highlighted block after the code that summarizes in one sentence what the reader should take away. For scanning, not reading.

### Total Visual Assets
14 hand-crafted SVG diagrams across four sections (4 + 3 + 4 + 3).

---

## Site Integration

### Navigation (mkdocs.yml)

```yaml
nav:
  - Home: index.md
  - Principles: principles.md
  - The Book:
    - book/index.md
    - Foundations:
      - How LLMs Actually Work: book/00a-how-llms-work.md
      - From API Calls to Tool Use: book/00b-api-to-tools.md
      - Your First Agent, No Framework: book/00c-first-agent.md
      - The Same Agent, With a Framework: book/00d-frameworks.md
    - Chapters:
      - 1. What "Agentic" Actually Means: book/01-what-agentic-means.md
      - 2. Tools, Context, and the Agent Loop: book/02-tools-context-agent-loop.md
      - 3. Workflow-First, Agent-Second: book/03-workflow-first-agent-second.md
      - 4. Multi-Agent Systems Without Theater: book/04-multi-agent-without-theater.md
      - 5. Human-in-the-Loop as Architecture: book/05-human-in-the-loop.md
      - 6. Evaluating and Hardening Agent Systems: book/06-evaluating-and-hardening.md
      - 7. When Not to Use Agents: book/07-when-not-to-use-agents.md
  - Projects:
    - LLM Explorer: projects/llm-explorer.md
    - Tool-Using Assistant: projects/tool-using-assistant.md
    - Research Agent: projects/research-agent.md
    - Framework Comparison: projects/framework-comparison.md
    - Document Intelligence Agent: projects/doc-intelligence-agent.md
    - Incident Runbook Agent: projects/incident-runbook-agent.md
  - Evidence:
    - Baseline Eval Report: proof/baseline-eval-report.md
    - Architecture Comparison: proof/workflow-vs-agent-comparison.md
    - Trace Examples: proof/trace-example.md
    - Failure Case Studies: proof/failure-cases.md
  - Code Reference: code/reference.md
  - Roadmap: roadmap.md
```

### Code Structure

```
src/
├── ch00/                      # Foundations code
│   ├── __init__.py
│   ├── llm_basics.py          # 0a: API calls, tokens, structured output
│   ├── tool_use.py            # 0b: Function calling, validation, multi-tool
│   ├── raw_agent.py           # 0c: The raw agent (~100 lines)
│   ├── adk_agent.py           # 0d: ADK implementation
│   ├── langchain_agent.py     # 0d: LangChain implementation
│   └── eval_compare.py        # 0d: Eval comparison script
├── shared/                    # Existing
├── ch02/ ... ch06/            # Existing
```

### New Projects

```
project/
├── llm-explorer/              # 0a companion
│   ├── README.md
│   ├── src/
│   │   ├── token_counter.py
│   │   ├── context_overflow.py
│   │   ├── hallucination_demo.py
│   │   └── structured_output.py
│   └── docs/
│       └── experiments.md
├── tool-using-assistant/      # 0b companion
│   ├── README.md
│   ├── src/
│   │   ├── tools.py
│   │   ├── validation.py
│   │   └── assistant.py
│   └── docs/
│       └── architecture.md
├── research-agent/            # 0c companion
│   ├── README.md
│   ├── src/
│   │   ├── agent.py
│   │   ├── tools.py
│   │   └── run.py
│   ├── evals/
│   │   ├── test_queries.yaml
│   │   └── run_eval.py
│   └── docs/
│       └── architecture.md
├── framework-comparison/      # 0d companion
│   ├── README.md
│   ├── src/
│   │   ├── raw_agent.py
│   │   ├── adk_agent.py
│   │   ├── langchain_agent.py
│   │   └── compare.py
│   ├── evals/
│   │   ├── test_queries.yaml
│   │   ├── rubric.yaml
│   │   └── run_eval.py
│   └── docs/
│       └── results.md
├── doc-intelligence-agent/    # Existing
└── incident-runbook-agent/    # Existing
```

### New Diagrams

```
docs/diagrams/
├── (existing 22 SVGs)
├── api-contract.svg              # 0a
├── context-window-bucket.svg     # 0a
├── token-cost-calculator.svg     # 0a
├── hallucination-mental-model.svg # 0a
├── function-calling-cycle.svg    # 0b
├── tool-selection-comparison.svg # 0b
├── single-turn-ceiling.svg       # 0b
├── agent-loop-foundations.svg    # 0c
├── agent-trace-waterfall.svg     # 0c
├── three-failure-modes.svg       # 0c
├── before-after-guardrails.svg   # 0c
├── framework-layers.svg          # 0d
├── three-way-comparison.svg      # 0d
└── framework-decision-tree.svg   # 0d
```

### Dependencies (additions to pyproject.toml)
- `google-adk` -- for section 0d ADK examples
- `langchain`, `langchain-core`, `langchain-anthropic` -- for section 0d LangChain examples (use Anthropic as the default model provider, matching the raw examples)

### Other File Updates
- **README.md** -- Add "New to agentic AI? Start with the Foundations" section at top
- **docs/index.md** -- Add Foundations as recommended starting point for newcomers
- **docs/book/index.md** -- Add Foundations section before chapter list
- **docs/roadmap.md** -- Add Foundations as shipped content
- **Makefile** -- Add targets: `make foundations` (run all foundation examples), `make compare` (run framework comparison)

---

## Bridge to the Book

The Foundations end with a deliberate bridge. After 0d, the reader has:

- A mental model of LLMs (0a)
- Hands-on experience with tool use (0b)
- Built a working agent from scratch (0c)
- Rebuilt it with frameworks and compared (0d)
- Seen eval results and traces (0d)

The closing of 0d says: "You've built the same agent three ways. You understand what happens at every level. You know what frameworks give you, what they take away, and how to evaluate both. You're ready for the book. Chapter 1 gives you the vocabulary to think precisely about what you just built. The rest of the book gives you the engineering discipline to build it for production."

Chapter 1 (the free sample) then reframes everything they just experienced with precise vocabulary: the five system types, bounded autonomy, the decision map. This creates an immediate "oh, THIS is what I was doing" moment.

After Chapter 1, the chapter summaries (2-7) point to Amazon. The reader is now invested -- they've built things, they understand the concepts, they've seen the vocabulary, and they want the depth. The funnel is complete.

---

## Success Criteria

1. A developer with zero LLM experience can complete all four sections in under 2 hours and have a working agent
2. A developer who has done tutorials feels "finally, someone told me straight" -- the content is more useful than anything they've read before
3. Every code example runs with `make foundations`
4. The framework comparison produces real, reproducible eval numbers
5. The reading path from Foundations -> Chapter 1 -> "buy on Amazon" is seamless with no dead ends
6. All 14 SVG diagrams are scannable in 5 seconds and communicate one concept each
