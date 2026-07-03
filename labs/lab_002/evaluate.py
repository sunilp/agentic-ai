"""Re-score recorded findings with an LLM judge and fold the result into
results.json + RESULTS.md.

Usage:
    python -m labs.lab_002.evaluate                  # 3 judge passes, qwen2.5:14b
    python -m labs.lab_002.evaluate --runs 1         # quick pass
    python -m labs.lab_002.evaluate --judge-model qwen2.5:14b

Reads results.json (written by run.py), which already carries a cheap
heuristic success rate (keyword overlap, metrics.score_finding). This stage
re-scores each recorded finding's root cause and remediation against the
incident's ground truth with an LLM judge, averaging over repeated passes to
bound judge variance, exactly mirroring Lab-001's judge-prompt shape. The
third rubric criterion, action_correct, is a deterministic exact-match check
(no judge call needed: it either names the sanctioned action or it doesn't).
The numeric pass threshold matches `metrics._PASS` (0.6).

Writes the judge scores back into results.json under a new "judge" key and
regenerates RESULTS.md so it reflects both the run.py operational numbers
(success rate, cost/latency multiples, durability savings) and this judge
cross-check side by side.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import statistics
import time
from pathlib import Path

import yaml

from labs.lab_002 import dataset
from labs.lab_002 import metrics as lab_metrics
from src.shared.model_client import create_client
from src.shared.types import CompletionRequest, Message, Role

HERE = Path(__file__).parent
SYSTEMS = ["baseline", "contender"]

_JUDGE_SYSTEM = (
    "You are a strict evaluation judge for incident-response findings. Score the "
    "finding on two criteria, each from 0.0 to 1.0:\n"
    "- root_cause_match: does the stated root cause correctly identify the actual "
    "ground-truth root cause?\n"
    "- remediation_match: does the proposed remediation correctly address the "
    "ground-truth remediation?\n"
    'Reply with strict JSON only: {"root_cause_match": x, "remediation_match": x}.'
)


def _clamp(x: float) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except (TypeError, ValueError):
        return 0.0


def _parse_scores(content: str) -> dict[str, float]:
    match = re.search(r"\{.*\}", content or "", re.DOTALL)
    if not match:
        return {"root_cause_match": 0.0, "remediation_match": 0.0}
    try:
        raw = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"root_cause_match": 0.0, "remediation_match": 0.0}
    return {k: _clamp(raw.get(k, 0.0)) for k in ("root_cause_match", "remediation_match")}


async def _judge_once(client, incident, finding: dict) -> dict[str, float]:
    user = (
        f"Ground truth root cause: {incident.ground_truth_root_cause}\n"
        f"Ground truth remediation: {incident.ground_truth_remediation}\n\n"
        f"Finding root cause: {finding.get('root_cause', '') or '(empty)'}\n"
        f"Finding remediation: {finding.get('proposed_remediation', '') or '(empty)'}"
    )
    resp = await client.complete(
        CompletionRequest(
            messages=[
                Message(role=Role.SYSTEM, content=_JUDGE_SYSTEM),
                Message(role=Role.USER, content=user),
            ],
            temperature=0.0,
            max_tokens=100,
            response_format={"type": "json_object"},
        )
    )
    return _parse_scores(resp.content or "")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Lab-002 evaluate: LLM-judge scoring")
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--runs", type=int, default=3, help="judge passes per finding")
    parser.add_argument("--base-url", default="http://localhost:11434/v1")
    args = parser.parse_args()

    rubric = yaml.safe_load((HERE / "rubric.yaml").read_text())
    weights = rubric["weights"]
    threshold = rubric.get("pass_threshold", lab_metrics._PASS)
    judge_cfg = rubric.get("judge", {})
    judge_model = args.judge_model or judge_cfg.get("model", "qwen2.5:14b")
    judge_provider = judge_cfg.get("provider", "local")

    results_path = HERE / "results.json"
    if not results_path.exists():
        raise SystemExit(
            "results.json not found -- run `python -m labs.lab_002.run` first"
        )
    results = json.loads(results_path.read_text())

    incidents_by_id = {i.id: i for i in dataset.load()}
    judge = create_client(judge_provider, model_name=judge_model, base_url=args.base_url)

    started = time.time()
    judge_summary: dict[str, dict] = {}

    for system in SYSTEMS:
        sys_records = results["systems"][system]["records"]
        scored = []
        for rec in sys_records:
            finding = rec.get("finding")
            incident = incidents_by_id.get(rec["incident_id"])
            if finding is None or incident is None:
                scored.append(
                    {
                        "incident_id": rec["incident_id"],
                        "judge_passed": False,
                        "judge_weighted": 0.0,
                        "judge_scores": {
                            "root_cause_match": 0.0,
                            "remediation_match": 0.0,
                            "action_correct": 0.0,
                        },
                        "run_weighted": [],
                    }
                )
                continue

            action_correct = (
                1.0 if finding.get("proposed_action") == incident.irreversible_action else 0.0
            )
            run_scores = []
            run_weighted = []
            for _ in range(args.runs):
                s = await _judge_once(judge, incident, finding)
                s["action_correct"] = action_correct
                run_scores.append(s)
                run_weighted.append(sum(s[k] * weights[k] for k in weights))
            avg_scores = {
                k: statistics.mean(rs[k] for rs in run_scores)
                for k in ("root_cause_match", "remediation_match", "action_correct")
            }
            mean_weighted = statistics.mean(run_weighted)
            scored.append(
                {
                    "incident_id": rec["incident_id"],
                    "judge_passed": mean_weighted >= threshold,
                    "judge_weighted": round(mean_weighted, 4),
                    "judge_scores": {k: round(v, 4) for k, v in avg_scores.items()},
                    "run_weighted": [round(x, 4) for x in run_weighted],
                }
            )
            print(
                f"  [{system}] {rec['incident_id']} judge_weighted={mean_weighted:.2f} "
                f"pass={mean_weighted >= threshold}"
            )

        n = len(scored)
        passed = sum(1 for s in scored if s["judge_passed"])
        variance = (
            statistics.mean(
                statistics.pstdev(s["run_weighted"]) if len(s["run_weighted"]) > 1 else 0.0
                for s in scored
            )
            if scored
            else 0.0
        )
        judge_summary[system] = {
            "n": n,
            "accuracy": round(passed / n, 4) if n else 0.0,
            "avg_weighted": round(statistics.mean(s["judge_weighted"] for s in scored), 4)
            if n
            else 0.0,
            "judge_variance": round(variance, 4),
            "records": scored,
        }

    results["judge"] = {
        "model": judge_model,
        "runs": args.runs,
        "pass_threshold": threshold,
        "weights": weights,
        "duration_s": round(time.time() - started, 1),
        "systems": judge_summary,
    }
    results_path.write_text(json.dumps(results, indent=2))
    (HERE / "RESULTS.md").write_text(_render_markdown(results))
    print(
        f"[evaluate] wrote results.json (judge section) and RESULTS.md "
        f"({results['judge']['duration_s']}s)"
    )


def _render_markdown(r: dict) -> str:
    base = r["systems"]["baseline"]
    cont = r["systems"]["contender"]
    dur = r["durability"]
    judge = r["judge"]
    jbase = judge["systems"]["baseline"]
    jcont = judge["systems"]["contender"]
    limit_note = f" (limited to first {r['limit']})" if r.get("limit") else ""

    lines = [
        "# Lab-002 (local reproduction): static baseline vs durable contender",
        "",
        f"Agent model: `{r['agent_model']}`. {r['n_incidents']} incidents{limit_note}, "
        f"{r['errors']} errors during the main run.",
        "",
        "## Results",
        "",
        "| Metric | Baseline | Contender |",
        "|--------|----------|-----------|",
        f"| Success rate (heuristic keyword overlap) | {base['success_rate']:.1%} | {cont['success_rate']:.1%} |",
        f"| Success rate (LLM judge, `{judge['model']}`) | {jbase['accuracy']:.1%} | {jcont['accuracy']:.1%} |",
        f"| Avg judge weighted score | {jbase['avg_weighted']:.3f} | {jcont['avg_weighted']:.3f} |",
        f"| Judge variance (mean stdev) | {jbase['judge_variance']:.3f} | {jcont['judge_variance']:.3f} |",
        f"| Avg total tokens / incident | {base['avg_total_tokens']} | {cont['avg_total_tokens']} |",
        f"| Avg model calls | {base['avg_model_calls']} | {cont['avg_model_calls']} |",
        f"| p50 latency (ms) | {base['p50_latency_ms']} | {cont['p50_latency_ms']} |",
        f"| Remediation applied rate | {base['remediation_rate']:.1%} | {cont['remediation_rate']:.1%} |",
        "",
        f"**Cost multiple (contender / baseline avg tokens):** {r['cost_multiple']}x. "
        f"**Latency multiple (contender / baseline p50):** {r['latency_multiple']}x.",
        "",
        "## Durability (crash + resume over a fixed subset)",
        "",
        f"{dur['n']} of {len(r['durability_subset'])} incidents in the subset reached "
        f"the human gate and were crash-tested ({r['durability_skipped']} skipped: no "
        "finding reached the gate, or the resume errored).",
        "",
    ]
    if dur["n"]:
        lines += [
            "| Metric | Value |",
            "|--------|-------|",
            f"| Avg tokens saved on resume | {dur['avg_tokens_saved']} |",
            f"| Avg model calls saved on resume | {dur['avg_model_calls_saved']} |",
            f"| Avg latency (ms) saved on resume | {dur['avg_latency_ms_saved']} |",
            f"| Avg frontier-only calls after resume | {dur['avg_frontier_calls']} |",
            "",
        ]
    else:
        lines += [
            "No incidents in the durability subset reached the gate; no savings computed.",
            "",
        ]
    lines += [
        "## LLM judge cross-check",
        "",
        f"Judge: `{judge['model']}`, {judge['runs']} passes per finding, weights "
        f"{judge['weights']}, pass threshold {judge['pass_threshold']}. "
        "`root_cause_match` and `remediation_match` are judge-scored 0..1; "
        "`action_correct` is a deterministic exact match against the incident's "
        "sanctioned action (no judge call needed for that one).",
        "",
        "This is the honesty check on the cheap heuristic above: keyword overlap can "
        "both over- and under-credit a finding relative to what an independent reader "
        "would say root-caused the incident.",
        "",
        "## Read this before quoting the numbers",
        "",
        "1. Local open models only (agent above, judge above). No Gemini key is "
        "configured in this environment, so `LAB002_MODEL=gemini-2.0-flash` is an "
        "untested path here, not a claim made by this run.",
        "2. Local inference has no dollar cost. The cost axis is tokens and model "
        "calls per incident, not dollars.",
        "3. Judge scoring carries local-model nondeterminism even at temperature 0; "
        "per-pass scores are in results.json so the reported averages are inspectable.",
        "",
        f"Run duration (main): {r['duration_s']}s. Run duration (judging): "
        f"{judge['duration_s']}s. Per-incident transcripts are under `runs/`; full "
        "per-incident detail, including every judge pass, is in results.json.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    asyncio.run(main())
