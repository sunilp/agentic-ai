from __future__ import annotations

import re

from labs.lab_002.schema import Finding, Incident, RunRecord

_PASS = 0.6


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9.@]+", text.lower()))


def score_finding(finding: Finding | None, incident: Incident) -> float:
    """Keyword-overlap match of root cause + remediation against ground truth."""
    if finding is None:
        return 0.0
    truth = _tokens(incident.ground_truth_root_cause) | _tokens(
        incident.ground_truth_remediation)
    got = _tokens(finding.root_cause) | _tokens(finding.proposed_remediation)
    if not truth:
        return 0.0
    return len(truth & got) / len(truth)


def success_rate(records: list[RunRecord], incidents: dict[str, Incident]) -> float:
    if not records:
        return 0.0
    passed = sum(
        1 for r in records
        if score_finding(r.finding, incidents[r.incident_id]) >= _PASS
    )
    return passed / len(records)


def durability_savings(
    pre_interrupt: RunRecord, post_resume: RunRecord
) -> dict[str, float]:
    """Work a naive re-run repeats but ADK's dedup skips on resume.

    Under a naive harness a crash at the gate forces re-running all
    pre-interrupt work; ADK replays it from the event log for free and runs
    only the post-resume frontier. So the saved work equals the pre-interrupt
    totals, and `frontier_calls` reports how little actually re-ran, which is
    the evidence dedup worked.
    """
    return {
        "tokens_saved": float(
            pre_interrupt.prompt_tokens + pre_interrupt.completion_tokens
        ),
        "model_calls_saved": float(pre_interrupt.model_calls),
        "latency_ms_saved": float(pre_interrupt.latency_ms),
        "frontier_calls": float(post_resume.model_calls),
    }
