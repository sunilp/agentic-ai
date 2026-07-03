def test_package_imports():
    import labs.lab_002  # noqa: F401


from labs.lab_002.schema import (
    Finding, Incident, IncidentBundle, FaultFamily, RunRecord,
)


def test_incident_roundtrips():
    inc = Incident(
        id="inc-001",
        fault_family=FaultFamily.BAD_DEPLOY,
        bundle=IncidentBundle(logs=["boom"], metrics={"err_rate": 0.9},
                              config={"replicas": "3"}, diff="- old\n+ new"),
        ground_truth_root_cause="bad deploy of svc-checkout v1.4.2",
        ground_truth_remediation="rollback svc-checkout to v1.4.1",
        irreversible_action="rollback_deploy:svc-checkout@v1.4.1",
    )
    assert Incident.model_validate_json(inc.model_dump_json()) == inc


def test_runrecord_defaults_are_zero():
    r = RunRecord(system="baseline", incident_id="inc-001")
    assert r.model_calls == 0 and r.remediation_applied is False


def test_finding_carries_proposed_action():
    f = Finding(incident_id="inc-001", root_cause="x",
                proposed_remediation="y", proposed_action="rollback_deploy:z")
    assert f.proposed_action == "rollback_deploy:z"
