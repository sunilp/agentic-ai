"""Deterministic mock tools for the support-triage agents.

The experiment isolates agent architecture, not tool backends, so the tools
return fixed, canned data. This keeps the run self-contained and reproducible:
no external services, no network, identical results on every machine.

Three tools mirror the original Lab-001 description:
- kb_lookup: search a small canned knowledge base by category.
- account_lookup: return a fixed account record for an account id.
- create_ticket: "open" a ticket and return a deterministic ticket id.
"""

from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable

from src.shared.types import ToolParameter, ToolResult, ToolSchema

# --- Canned knowledge base, keyed by router category ---

_KB: dict[str, str] = {
    "billing": (
        "Billing policy: invoices are issued monthly. Refunds are processed to the "
        "original payment method within 5 to 7 business days. Cancellation fees apply "
        "only to annual plans cancelled within the first 30 days."
    ),
    "technical": (
        "Technical support: standard delivery is 3 to 5 business days. Tracking is "
        "available from the Orders page once an item ships. Address changes are only "
        "possible before an order enters the shipped state."
    ),
    "account": (
        "Account help: profile, password, newsletter, and subscription settings live "
        "under Account Settings. Newsletter preferences update immediately. Closing an "
        "account is permanent and removes saved data after 30 days."
    ),
    "escalation": (
        "Escalation policy: complaints, disputed charges, and unresolved issues are "
        "routed to a human specialist. Provide the customer a ticket reference and a "
        "24 hour response window."
    ),
}

_ACCOUNT_RECORD = (
    "Account status: active. Plan: standard monthly. Last invoice: paid. "
    "Open tickets: none."
)


def _kb_lookup(args: dict) -> str:
    category = str(args.get("category", "")).lower().strip()
    return _KB.get(category, _KB["account"])


def _account_lookup(args: dict) -> str:
    account_id = str(args.get("account_id", "unknown"))
    return f"Account {account_id}: {_ACCOUNT_RECORD}"


def _create_ticket(args: dict) -> str:
    summary = str(args.get("summary", "support request"))
    # Deterministic ticket id derived from the summary, so re-runs are identical.
    digest = hashlib.sha256(summary.encode("utf-8")).hexdigest()[:8].upper()
    return f"Ticket TIC-{digest} created for: {summary}. SLA: 24 hours."


TOOL_SCHEMAS: list[ToolSchema] = [
    ToolSchema(
        name="kb_lookup",
        description="Look up the knowledge base for a support category.",
        parameters=[
            ToolParameter(
                name="category",
                type="string",
                description="One of: billing, technical, account, escalation.",
                enum=["billing", "technical", "account", "escalation"],
            )
        ],
    ),
    ToolSchema(
        name="account_lookup",
        description="Look up the customer's account record by account id.",
        parameters=[
            ToolParameter(
                name="account_id",
                type="string",
                description="The customer's account identifier.",
            )
        ],
    ),
    ToolSchema(
        name="create_ticket",
        description="Open a support ticket for issues that need a human specialist.",
        parameters=[
            ToolParameter(
                name="summary",
                type="string",
                description="A one-line summary of the issue.",
            )
        ],
    ),
]

_HANDLERS: dict[str, Callable[[dict], str]] = {
    "kb_lookup": _kb_lookup,
    "account_lookup": _account_lookup,
    "create_ticket": _create_ticket,
}


class ToolRegistry:
    """Minimal, deterministic tool registry for the lab."""

    def __init__(self) -> None:
        self.schemas = TOOL_SCHEMAS
        self.call_count = 0

    async def execute(self, name: str, arguments: dict, call_id: str) -> ToolResult:
        self.call_count += 1
        handler = _HANDLERS.get(name)
        if handler is None:
            return ToolResult(
                tool_call_id=call_id,
                name=name,
                content="",
                success=False,
                error=f"unknown tool: {name}",
            )
        try:
            content = handler(arguments or {})
            return ToolResult(tool_call_id=call_id, name=name, content=content, success=True)
        except Exception as exc:  # defensive: a bad arg should not crash the run
            return ToolResult(
                tool_call_id=call_id, name=name, content="", success=False, error=str(exc)
            )


# Typed alias for the run-loop callers.
ToolExecutor = Callable[[str, dict, str], Awaitable[ToolResult]]
