import pytest

from labs.lab_002.gate import ApprovalError, ApprovalToken, require_approval


def test_no_token_blocks():
    with pytest.raises(ApprovalError):
        require_approval("rollback_deploy:svc@v1", None)


def test_mismatched_action_blocks():
    tok = ApprovalToken(action="rollback_deploy:other@v9", approver="sre")
    with pytest.raises(ApprovalError):
        require_approval("rollback_deploy:svc@v1", tok)


def test_matching_token_allows():
    tok = ApprovalToken(action="rollback_deploy:svc@v1", approver="sre")
    require_approval("rollback_deploy:svc@v1", tok)  # no raise
