import pytest

from labs.lab_002 import tools
from labs.lab_002.dataset import generate
from labs.lab_002.gate import ApprovalError, ApprovalToken


def _incident():
    return generate(4, seed=42)[0]


def test_read_tools_return_text():
    inc = _incident()
    assert isinstance(tools.log_search(inc, "error"), str)
    assert isinstance(tools.metric_query(inc, "err_rate"), str)
    assert isinstance(tools.config_read(inc), str)
    assert isinstance(tools.diff_read(inc), str)


def test_apply_remediation_blocked_without_token():
    with pytest.raises(ApprovalError):
        tools.apply_remediation("rollback_deploy:svc@v1", None)


def test_apply_remediation_runs_with_matching_token():
    tok = ApprovalToken(action="rollback_deploy:svc@v1", approver="sre")
    assert "applied" in tools.apply_remediation("rollback_deploy:svc@v1", tok).lower()
