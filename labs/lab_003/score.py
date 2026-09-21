"""Lab-003: outcome versus trajectory, scored over Lab-002's recorded runs.

Runs no models. Reads the 60 run records Lab-002 already committed, scores each one
twice, and reports how often the two scores disagree.

    python -m labs.lab_003.score            # writes RESULTS.md and results.json
    python -m labs.lab_003.score --print    # to stdout only
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from labs.lab_003.assertions import (
    ASSERTIONS_RECORD_ONLY,
    ASSERTIONS_WITH_INCIDENT,
    Verdict,
    effort_within_family_norm,
)

LAB2 = Path(__file__).resolve().parent.parent / "lab_002"
HERE = Path(__file__).resolve().parent

# Lab-002's own outcome threshold, reused unchanged so the two scores are comparable.
OUTCOME_PASS = 0.6


def load() -> tuple[dict, dict]:
    results = json.loads((LAB2 / "results.json").read_text())
    incidents = {i["id"]: i for i in json.loads((LAB2 / "incidents.json").read_text())}
    return results, incidents


def family_medians(records: list[dict], incidents: dict) -> dict[str, float]:
    by_family: dict[str, list[int]] = defaultdict(list)
    for r in records:
        inc = incidents.get(r["incident_id"])
        if inc:
            by_family[inc["fault_family"]].append(r.get("model_calls") or 0)
    return {f: statistics.median(v) for f, v in by_family.items() if v}


def grade(record: dict, incident: dict, med: float) -> list[Verdict]:
    out = [a(record) for a in ASSERTIONS_RECORD_ONLY]
    out += [a(record, incident) for a in ASSERTIONS_WITH_INCIDENT]
    out.append(effort_within_family_norm(record, med))
    return out


def score_system(name: str, records: list[dict], incidents: dict) -> dict:
    meds = family_medians(records, incidents)
    rows, tally = [], defaultdict(lambda: {"pass": 0, "fail": 0, "n/a": 0})
    for r in records:
        inc = incidents.get(r["incident_id"])
        if inc is None:
            continue
        fam = inc["fault_family"]
        verdicts = grade(r, inc, meds.get(fam, 0.0))
        for v in verdicts:
            key = "n/a" if v.passed is None else ("pass" if v.passed else "fail")
            tally[v.assertion][key] += 1
        applicable = [v for v in verdicts if v.passed is not None]
        traj_pass = all(v.passed for v in applicable) if applicable else None
        outcome_pass = (r.get("heuristic_score") or 0.0) >= OUTCOME_PASS
        rows.append({
            "incident_id": r["incident_id"],
            "fault_family": fam,
            "outcome_score": round(r.get("heuristic_score") or 0.0, 3),
            "outcome_pass": outcome_pass,
            "trajectory_pass": traj_pass,
            "failed_assertions": [v.assertion for v in applicable if not v.passed],
            "detail": {v.assertion: v.detail for v in applicable if not v.passed},
        })

    graded = [r for r in rows if r["trajectory_pass"] is not None]
    both = [r for r in graded if r["outcome_pass"] and r["trajectory_pass"]]
    illusion = [r for r in graded if r["outcome_pass"] and not r["trajectory_pass"]]
    harsh = [r for r in graded if not r["outcome_pass"] and r["trajectory_pass"]]
    neither = [r for r in graded if not r["outcome_pass"] and not r["trajectory_pass"]]
    return {
        "system": name,
        "n": len(rows),
        "n_gradeable": len(graded),
        "outcome_pass_rate": round(sum(r["outcome_pass"] for r in rows) / len(rows), 4) if rows else 0,
        "trajectory_pass_rate": round(len([r for r in graded if r["trajectory_pass"]]) / len(graded), 4) if graded else 0,
        "both_pass": len(both),
        "outcome_pass_trajectory_fail": len(illusion),
        "outcome_fail_trajectory_pass": len(harsh),
        "both_fail": len(neither),
        "assertions": {k: dict(v) for k, v in tally.items()},
        "rows": rows,
    }


def render(report: dict) -> str:
    L = ["# Lab-003: outcome versus trajectory", "",
         "Scores Lab-002's committed run records twice: once on the outcome (did it reach",
         "the right answer) and once on the trajectory (was the path defensible). Runs no",
         "models; every assertion is deterministic and computed from the recorded run.", "",
         f"Source: `labs/lab_002/results.json`, run of {report['source_run']}.",
         f"Outcome threshold reused from Lab-002 unchanged: {OUTCOME_PASS}.", "",
         "## Headline", ""]
    L += ["| System | n | Outcome pass | Trajectory pass | **Outcome pass, trajectory fail** |",
          "| --- | ---: | ---: | ---: | ---: |"]
    for s in report["systems"]:
        L.append(f"| {s['system']} | {s['n']} | {s['outcome_pass_rate']:.1%} | "
                 f"{s['trajectory_pass_rate']:.1%} | **{s['outcome_pass_trajectory_fail']}** |")
    L += ["", "## Agreement between the two scores", "",
          "| System | Both pass | Outcome pass / trajectory fail | Outcome fail / trajectory pass | Both fail |",
          "| --- | ---: | ---: | ---: | ---: |"]
    for s in report["systems"]:
        L.append(f"| {s['system']} | {s['both_pass']} | {s['outcome_pass_trajectory_fail']} | "
                 f"{s['outcome_fail_trajectory_pass']} | {s['both_fail']} |")
    L += ["", "## Per-assertion results", ""]
    for s in report["systems"]:
        L += [f"### {s['system']}", "",
              "| Assertion | Pass | Fail | Not applicable |", "| --- | ---: | ---: | ---: |"]
        for name, t in sorted(s["assertions"].items()):
            L.append(f"| `{name}` | {t['pass']} | {t['fail']} | {t['n/a']} |")
        L.append("")
    L += ["## Runs that passed on outcome and failed on trajectory", "",
          "These are the runs an outcome metric reports as successes.", ""]
    for s in report["systems"]:
        ill = [r for r in s["rows"] if r["outcome_pass"] and r["trajectory_pass"] is False]
        if not ill:
            continue
        L += [f"### {s['system']}", ""]
        for r in ill:
            L.append(f"- **{r['incident_id']}** ({r['fault_family']}), outcome "
                     f"{r['outcome_score']:.2f}: {', '.join(r['failed_assertions'])}")
            for k, v in r["detail"].items():
                L.append(f"  - `{k}`: {v}")
        L.append("")
    L += ["## Scope and limits", "",
          "- The trajectory assertions here are **deterministic checks on a recorded run**, not a",
          "  general trajectory-evaluation method. They cover authorization, internal coherence,",
          "  action correctness and effort. They do not cover reasoning quality.",
          "- The source runs used one small local model on 30 seeded synthetic incidents. The",
          "  defect rates below are properties of that run, not of agents in general.",
          "- The outcome score is Lab-002's keyword-overlap heuristic. A stronger outcome scorer",
          "  would change the disagreement count, and the direction of the argument does not",
          "  depend on which outcome scorer is used: it depends on the two scores measuring",
          "  different things.",
          "- Lab-002's generator writes the version at issue on the `-` line of the diff and uses",
          "  it as both the ground-truth cause and the ground-truth action target, with the `+`",
          "  line carrying an unrelated random version. That is not the usual diff convention.",
          "  These assertions therefore compare against the ground-truth fields directly and never",
          "  infer rollback direction from the diff.",
          "- `action_is_machine_executable` and `action_targets_correct_resource` are scored",
          "  separately on purpose. A semantically correct action in an undispatchable format and",
          "  a wrong action need different fixes, and collapsing them hides which one you have.", ""]
    return "\n".join(L)


def main() -> int:
    results, incidents = load()
    report = {
        "source_run": results.get("finished", "unknown"),
        "agent_model": results.get("agent_model"),
        "outcome_threshold": OUTCOME_PASS,
        "systems": [score_system(name, results["systems"][name]["records"], incidents)
                    for name in ("baseline", "contender") if name in results["systems"]],
    }
    md = render(report)
    if "--print" in sys.argv:
        print(md)
        return 0
    (HERE / "results.json").write_text(json.dumps(report, indent=1))
    (HERE / "RESULTS.md").write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
