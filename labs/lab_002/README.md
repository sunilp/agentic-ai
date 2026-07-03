# Lab-002: static baseline vs durable contender (local, reproducible)

A free, fully local run comparing a single static ADK agent (**baseline**) against
a dynamic investigator/verifier workflow with a human-approval gate before any
irreversible action (**contender**), on the same synthetic incident set, tools,
and model. A separate durability harness "crashes" the contender mid-run at the
approval gate and resumes it from disk in a fresh process, to measure what a
persisted session actually saves on resume.

## Read this first (honesty caveats)

1. **Local floor only, no Gemini comparison yet.** This run uses local open
   models via Ollama (`llama3.2:3b` for the agents, `qwen2.5:14b` for the
   judge). `run.py` has a `LAB002_MODEL=gemini-2.0-flash` path that switches to
   native Gemini (no `LiteLlm` wrapper), but no Gemini API key is configured in
   this environment, so that path is untested here. Treat any local-vs-Gemini
   comparison as future work, not a claim in the committed numbers.
2. **No dollar cost.** Local inference is free, so the cost axis is tokens and
   model calls per incident, not dollars.
3. **Synthetic incidents.** `incidents.json` is deterministically generated
   (four fault families, seeded), not a real incident corpus. It exercises the
   architecture difference (static single pass vs dynamic fan-out with a gate),
   not real-world incident diversity.
4. **Two scoring passes.** `run.py` computes a cheap heuristic success rate
   (keyword overlap against ground truth). `evaluate.py` is a separate, slower
   pass that re-scores the same recorded findings with an LLM judge, as a
   cross-check on the heuristic. Both numbers are in RESULTS.md.

## Reproduce

Requires [Ollama](https://ollama.com) running locally and the `lab002` extra
(`google-adk>=2.3.0`, `litellm>=1.40`) installed in a dedicated virtualenv --
the project's default environment pins an older ADK and must not be used here.

```bash
# 1. Pull the models (agents = small, judge = mid).
ollama pull llama3.2:3b
ollama pull qwen2.5:14b

# 2. Set up the ADK-2.3.0 virtualenv (once).
python3.12 -m venv .venv-lab002
.venv-lab002/bin/pip install -e ".[lab002]"

# 3. Generate the incident set (deterministic, seed 42).
make lab-002-data          # python -m labs.lab_002.dataset 30

# 4. Run both systems + the durability harness, record transcripts.
GOOGLE_GENAI_USE_VERTEXAI=0 make lab-002-run     # python -m labs.lab_002.run

# 5. Score the recorded findings with the LLM judge and write RESULTS.md.
GOOGLE_GENAI_USE_VERTEXAI=0 make lab-002-eval    # python -m labs.lab_002.evaluate
```

Run from the repository root so `labs` and `src` import correctly, and use
`.venv-lab002/bin/python` (or activate that venv) for steps 3-5, not the
project's default Python.

To smoke-test the pipeline cheaply before a full run, set `LAB002_LIMIT` to
process only the first N incidents:

```bash
GOOGLE_GENAI_USE_VERTEXAI=0 LAB002_LIMIT=2 .venv-lab002/bin/python -m labs.lab_002.run
GOOGLE_GENAI_USE_VERTEXAI=0 LAB002_LIMIT=2 .venv-lab002/bin/python -m labs.lab_002.evaluate
```

## What the repo contains vs what you generate

Committed (the reusable harness): `dataset.py`, `schema.py`, `tools.py`,
`gate.py`, `systems.py`, `durability.py`, `metrics.py`, `run.py`,
`evaluate.py`, `rubric.yaml`, `incidents.json` (the deterministic sample), and
this README.

Generated locally when you run it: `runs/<system>/<id>.json` transcripts (plus
`runs/durability/<id>.json` for the crash-tested subset), `results.json`, and
`RESULTS.md`. These are reproducible from the recipe above; re-running
overwrites them.

## Design

- `dataset.py` -- deterministic, family-balanced synthetic incidents (bad
  deploy, config drift, dependency failure, data issue), seed 42.
- `schema.py` -- the shared Pydantic contracts: `Incident`, `Hypothesis`,
  `Verdict`, `Finding`, `RemediationDecision`, `RunRecord`.
- `tools.py` / `gate.py` -- deterministic mock tools (log search, metric
  query, config/diff read) and the out-of-band approval-token check that
  gates the one irreversible action.
- `systems.py` -- the **baseline** (single static `Agent`, one pass, fixed
  gate on an exact-action match) and the **contender** (an ADK `Workflow`:
  a dynamic investigator/verifier fan-out across four branches, synthesized
  into one `Finding`, paused at a `RequestInput` human-approval gate before
  the remediation node runs).
- `durability.py` -- crashes the contender at the approval gate (drops the
  runner and session service) and resumes it from a fresh
  `SqliteSessionService` over the same on-disk file, proving ADK's dedup
  skips the pre-interrupt work instead of re-running it.
- `metrics.py` -- the heuristic success-rate scorer (keyword overlap against
  ground truth) and the durability-savings calculation.
- `run.py` -- runs baseline and contender over every incident, plus the
  durability harness over a fixed 5-incident subset; writes transcripts,
  `results.json`, and `RESULTS.md`. Guards a bad incident (exception, or the
  gate never reached) so it is skipped rather than aborting the batch --
  this closes a gap flagged in Task 9 review, where the durability harness
  had no such guard.
- `evaluate.py` -- LLM-judge re-scoring of `root_cause_match` and
  `remediation_match` (judge-scored 0..1) plus a deterministic
  `action_correct` check, against `rubric.yaml` (weights 0.5/0.3/0.2, pass at
  0.6, matching `metrics._PASS`), N judge passes to bound variance. Folds the
  result back into `results.json` and regenerates `RESULTS.md`.

## Determinism

Models run at temperature 0, but local-model output is not perfectly
deterministic across hardware and quantization. The committed transcripts and
per-run judge scores make the reported numbers inspectable; re-running may
vary slightly.
