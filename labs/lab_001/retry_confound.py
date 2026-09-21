"""Lab-001 follow-up: how much of the hierarchy's advantage is the extra attempt?

The original run compared a rule-based router against a three-agent hierarchy. The
hierarchy's verifier can trigger a re-answer round; the router has no equivalent. So
the two systems differ in topology AND in how many attempts they get at the answer,
and the headline pass-rate gap cannot be attributed to either on its own.

This script does not re-run anything. It reads the committed records and bounds the
confound from the `verifier_retried` flag that the original run already recorded.

    python -m labs.lab_001.retry_confound
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def rate(rs: list[dict]) -> float:
    return sum(r["passed"] for r in rs) / len(rs) if rs else 0.0


def main() -> int:
    d = json.loads((HERE / "results.json").read_text())
    R, H = d["systems"]["router"], d["systems"]["hierarchy"]
    rr, hr = R["records"], H["records"]

    retried = [r for r in hr if r["flags"].get("verifier_retried")]
    once = [r for r in hr if not r["flags"].get("verifier_retried")]
    gap = rate(hr) - rate(rr)
    # Upper bound on what the extra attempt can explain: assume every retried run that
    # passed would have failed on its first attempt.
    ub = sum(r["passed"] for r in retried) / len(hr)

    L = ["# Lab-001 follow-up: the retry confound, bounded", "",
         "The original comparison gave the hierarchy a verifier that can trigger a re-answer",
         "round and gave the router one attempt. This bounds how much of the pass-rate gap",
         "that difference could account for, using only the records the original run",
         "committed. **No models were run.**", "",
         "| | n | Pass rate | Mean model calls |", "| --- | ---: | ---: | ---: |",
         f"| router | {len(rr)} | {rate(rr):.1%} | {R['avg_model_calls']} |",
         f"| hierarchy, all | {len(hr)} | {rate(hr):.1%} | {H['avg_model_calls']} |",
         f"| hierarchy, verifier retried | {len(retried)} | {rate(retried):.1%} | |",
         f"| hierarchy, answered once | {len(once)} | {rate(once):.1%} | |", "",
         "## What this shows", "",
         f"**The verifier rejected the first answer in {len(retried)} of {len(hr)} runs.** The hierarchy",
         "is therefore not a system that occasionally retries. It is a system that almost always",
         "takes two attempts, and the single-attempt case is the rare one.", "",
         f"**The {len(once)} runs that answered once passed at {rate(once):.1%},** against the router's",
         f"{rate(rr):.1%}. That subset is tiny and it is not a random sample, since a run reaches it",
         "only by satisfying the verifier first time, so it cannot carry much weight in either",
         "direction. It does not support the hierarchy.", "",
         f"**The gap to explain is {gap:.1%}.** If every retried run that passed owed its pass entirely",
         f"to the second attempt, the retry would account for {ub:.1%} of all hierarchy runs, which",
         "exceeds the gap. The extra attempt is sufficient on its own to explain the whole",
         "difference. It is an upper bound and not an estimate, and the point is that the",
         "original data cannot rule the explanation out.", "",
         f"**Routing got worse, not better.** The hierarchy's LLM classifier misrouted",
         f"{H['misroute_rate']:.0%} of queries against {R['misroute_rate']:.0%} for the rule-based",
         "switch. So the hierarchy scored higher while being worse at the one thing the extra",
         "agents were added to do, which points further at the answer attempts rather than the",
         "topology.", "",
         "## What would settle it", "",
         "A third arm: the router given the same number of answer attempts, with no verifier.",
         "If it matches the hierarchy, the topology bought nothing on this task. If the",
         "hierarchy still leads, the verification is doing work. That arm has not been run, and",
         "until it is, the honest reading of the original result is that a difference in attempt",
         "budget is at least as plausible an explanation as the architecture.", ""]
    out = "\n".join(L)
    (HERE / "RETRY-CONFOUND.md").write_text(out)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
