"""Run the same agent two ways and watch the difference.

    python -m src.fn04.run

The agent script is identical in both runs: call the destructive tool, then
claim the task is done. The prompted loop believes it and the database is
gone. The enforced loop refuses the destructive call because no approval was
granted out of band, and the database survives.
"""

from __future__ import annotations

from src.fn04.loop import (
    ApprovalGate,
    Database,
    Done,
    Step,
    Tool,
    ToolCall,
    run_enforced,
    run_prompted,
)


def _script() -> list[Step]:
    # A coding agent hits a snag, decides to "clean up", and reports success.
    return [ToolCall("delete_all"), Done()]


def _tools(db: Database) -> dict[str, Tool]:
    return {
        "read_rows": Tool("read_rows", lambda: list(db.rows)),
        "delete_all": Tool("delete_all", db.delete_all, destructive=True),
    }


def main() -> None:
    db1 = Database()
    r1 = run_prompted(iter(_script()), _tools(db1), db1)
    print("prompted-stop loop")
    print(f"  stop reason : {r1.stop_reason.value}")
    print(f"  database    : {'DELETED' if db1.deleted else 'intact'}")

    print()

    db2 = Database()
    r2 = run_enforced(iter(_script()), _tools(db2), db2, approval=ApprovalGate())
    print("enforced-stop loop")
    print(f"  stop reason : {r2.stop_reason.value}")
    print(f"  blocked     : {[c.name for c in r2.blocked_calls]}")
    print(f"  database    : {'DELETED' if db2.deleted else 'intact'}")


if __name__ == "__main__":
    main()
