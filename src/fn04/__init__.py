"""FN-004: prompted-stop vs enforced-stop agent loops.

Companion code for the Field Note "Loop engineering is a 30-year-old loop
with a new hashtag." The same scripted agent runs two ways. One trusts the
agent's own claim of completion and lets it call a destructive tool; the
other puts three external fences around the loop, an iteration cap, a
no-progress detector, and a capability gate on destructive actions, so the
agent cannot delete the database on a hallucinated "done."
"""

from src.fn04.loop import (
    ApprovalGate,
    Database,
    Done,
    LoopResult,
    StopReason,
    Tool,
    ToolCall,
    run_enforced,
    run_prompted,
)

__all__ = [
    "ApprovalGate",
    "Database",
    "Done",
    "LoopResult",
    "StopReason",
    "Tool",
    "ToolCall",
    "run_enforced",
    "run_prompted",
]
