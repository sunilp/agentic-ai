# Lab-002 (local reproduction): static baseline vs durable contender

Agent model: `ollama_chat/llama3.2:3b`. 30 incidents, 0 errors during the main run.

## Results

| Metric | Baseline | Contender |
|--------|----------|-----------|
| Success rate (heuristic keyword overlap) | 20.0% | 10.0% |
| Success rate (LLM judge, `qwen2.5:14b`) | 16.7% | 10.0% |
| Avg judge weighted score | 0.273 | 0.326 |
| Judge variance (mean stdev) | 0.000 | 0.000 |
| Avg total tokens / incident | 290.2 | 6256 |
| Avg model calls | 1 | 16.93 |
| p50 latency (ms) | 2552.4 | 48106.0 |
| Remediation applied rate | 3.3% | 100.0% |

**Cost multiple (contender / baseline avg tokens):** 21.56x. **Latency multiple (contender / baseline p50):** 18.85x.

## Durability (crash + resume over a fixed subset)

5 of 5 incidents in the subset reached the human gate and were crash-tested (0 skipped: no finding reached the gate, or the resume errored).

| Metric | Value |
|--------|-------|
| Avg tokens saved on resume | 6265.0 |
| Avg model calls saved on resume | 17.0 |
| Avg latency (ms) saved on resume | 48590.3 |
| Avg frontier-only calls after resume | 0.0 |

## LLM judge cross-check

Judge: `qwen2.5:14b`, 3 passes per finding, weights {'root_cause_match': 0.5, 'remediation_match': 0.3, 'action_correct': 0.2}, pass threshold 0.6. `root_cause_match` and `remediation_match` are judge-scored 0..1; `action_correct` is a deterministic exact match against the incident's sanctioned action (no judge call needed for that one).

This is the honesty check on the cheap heuristic above: keyword overlap can both over- and under-credit a finding relative to what an independent reader would say root-caused the incident.

## Read this before quoting the numbers

1. Local open models only (agent above, judge above). No Gemini key is configured in this environment, so `LAB002_MODEL=gemini-2.0-flash` is an untested path here, not a claim made by this run.
2. Local inference has no dollar cost. The cost axis is tokens and model calls per incident, not dollars.
3. Judge scoring carries local-model nondeterminism even at temperature 0; per-pass scores are in results.json so the reported averages are inspectable.

Run duration (main): 4830.7s. Run duration (judging): 294.9s. Per-incident transcripts are under `runs/`; full per-incident detail, including every judge pass, is in results.json.