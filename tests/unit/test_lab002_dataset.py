from labs.lab_002.dataset import generate
from labs.lab_002.schema import FaultFamily


def test_generation_is_deterministic():
    a = generate(20, seed=42)
    b = generate(20, seed=42)
    assert [i.model_dump() for i in a] == [i.model_dump() for i in b]


def test_seed_changes_output():
    assert generate(20, seed=1)[0].id == generate(20, seed=2)[0].id  # ids stable
    assert generate(20, seed=1)[0].bundle != generate(20, seed=2)[0].bundle


def test_families_are_balanced():
    items = generate(20, seed=42)
    counts = {f: 0 for f in FaultFamily}
    for i in items:
        counts[i.fault_family] += 1
    assert all(c == 5 for c in counts.values())  # 20 / 4 families


def test_every_incident_has_ground_truth_and_gated_action():
    for i in generate(12, seed=42):
        assert i.ground_truth_root_cause
        assert i.irreversible_action.startswith(("rollback_deploy:", "revert_config:",
                                                 "restart_service:", "purge_cache:"))
