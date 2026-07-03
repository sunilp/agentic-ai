from labs.lab_002.dataset import generate
from labs.lab_002.metrics import durability_savings, score_finding, success_rate
from labs.lab_002.schema import Finding, RunRecord


def test_score_rewards_ground_truth_overlap():
    inc = generate(4, seed=42)[0]
    good = Finding(incident_id=inc.id, root_cause=inc.ground_truth_root_cause,
                   proposed_remediation=inc.ground_truth_remediation,
                   proposed_action=inc.irreversible_action)
    bad = Finding(incident_id=inc.id, root_cause="the moon",
                  proposed_remediation="reboot everything", proposed_action="x")
    assert score_finding(good, inc) > score_finding(bad, inc)
    assert score_finding(None, inc) == 0.0


def test_success_rate_counts_passing():
    incs = {i.id: i for i in generate(4, seed=42)}
    rec = RunRecord(system="c", incident_id="inc-000",
                    finding=Finding(incident_id="inc-000",
                                    root_cause=incs["inc-000"].ground_truth_root_cause,
                                    proposed_remediation=incs["inc-000"].ground_truth_remediation,
                                    proposed_action="x"))
    assert success_rate([rec], incs) == 1.0


def test_durability_savings_is_pre_interrupt_work():
    pre = RunRecord(system="c", incident_id="i", prompt_tokens=800,
                    completion_tokens=200, model_calls=6, latency_ms=5000)
    post = RunRecord(system="c", incident_id="i", prompt_tokens=100,
                     completion_tokens=50, model_calls=1, latency_ms=700)
    s = durability_savings(pre, post)
    assert s["tokens_saved"] == 1000
    assert s["model_calls_saved"] == 6
    assert s["latency_ms_saved"] == 5000
    assert s["frontier_calls"] == 1  # post-resume ran only the frontier
