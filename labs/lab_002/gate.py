from __future__ import annotations

from dataclasses import dataclass


class ApprovalError(RuntimeError):
    """Raised when an irreversible action is attempted without valid approval."""


@dataclass(frozen=True)
class ApprovalToken:
    action: str
    approver: str


def require_approval(action: str, token: ApprovalToken | None) -> None:
    """Raise unless `token` authorizes exactly `action`.

    This is the enforced stop from FN-004: the gate is a capability check
    outside the model, not a prompt the model can talk past.
    """
    if token is None:
        raise ApprovalError(f"no approval token for irreversible action: {action}")
    if token.action != action:
        raise ApprovalError(f"token authorizes '{token.action}', not '{action}'")
