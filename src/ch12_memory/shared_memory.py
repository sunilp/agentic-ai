"""SQLite-backed shared memory with scoped keys, optimistic concurrency, and atomic claims."""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any

from src.ch12_memory.types import ScopeType, SharedEntry


class VersionConflictError(Exception):
    """Raised when an optimistic-concurrency version check fails."""

    def __init__(self, key: str, expected: int, actual: int) -> None:
        self.key = key
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Version conflict on '{key}': expected {expected}, actual {actual}"
        )


class SharedMemory:
    """Scoped key-value store with optimistic concurrency and atomic claims.

    Each entry is identified by a (scope, key) pair.  Writes use an optional
    ``expected_version`` parameter for compare-and-swap semantics; claims
    provide a simple atomic "first writer wins" primitive.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_table()

    # ── Schema ────────────────────────────────────────────────────────────

    def _create_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shared_entries (
                scope       TEXT    NOT NULL,
                key         TEXT    NOT NULL,
                value       TEXT,
                version     INTEGER NOT NULL DEFAULT 1,
                agent_id    TEXT,
                timestamp   REAL,
                reason      TEXT,
                PRIMARY KEY (scope, key)
            )
            """
        )
        self._conn.commit()

    # ── Write ─────────────────────────────────────────────────────────────

    def write(
        self,
        scope: ScopeType,
        key: str,
        value: Any,
        agent_id: str = "",
        expected_version: int | None = None,
        reason: str = "",
    ) -> int:
        """Write a value, returning the new version number.

        If *expected_version* is given and does not match the current version,
        a :class:`VersionConflictError` is raised.  Non-string values are
        serialised with ``json.dumps``.
        """
        if not isinstance(value, str):
            value = json.dumps(value)

        now = time.time()

        # Check whether the key already exists.
        cur = self._conn.execute(
            "SELECT version FROM shared_entries WHERE scope = ? AND key = ?",
            (scope.value, key),
        )
        row = cur.fetchone()

        if row is None:
            # New entry — insert with version 1.
            self._conn.execute(
                """
                INSERT INTO shared_entries (scope, key, value, version, agent_id, timestamp, reason)
                VALUES (?, ?, ?, 1, ?, ?, ?)
                """,
                (scope.value, key, value, agent_id, now, reason),
            )
            self._conn.commit()
            return 1

        current_version = row["version"]

        if expected_version is not None and current_version != expected_version:
            raise VersionConflictError(key, expected_version, current_version)

        new_version = current_version + 1
        self._conn.execute(
            """
            UPDATE shared_entries
               SET value     = ?,
                   version   = ?,
                   agent_id  = ?,
                   timestamp = ?,
                   reason    = ?
             WHERE scope = ? AND key = ?
            """,
            (value, new_version, agent_id, now, reason, scope.value, key),
        )
        self._conn.commit()
        return new_version

    # ── Read ──────────────────────────────────────────────────────────────

    def read(self, scope: ScopeType, key: str) -> Any | None:
        """Return the stored value, or ``None`` if the key does not exist."""
        cur = self._conn.execute(
            "SELECT value FROM shared_entries WHERE scope = ? AND key = ?",
            (scope.value, key),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return row["value"]

    def read_entry(self, scope: ScopeType, key: str) -> SharedEntry | None:
        """Return the full :class:`SharedEntry`, or ``None`` if missing."""
        cur = self._conn.execute(
            "SELECT * FROM shared_entries WHERE scope = ? AND key = ?",
            (scope.value, key),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return SharedEntry(
            scope=ScopeType(row["scope"]),
            key=row["key"],
            value=row["value"],
            version=row["version"],
            agent_id=row["agent_id"] or "",
            timestamp=row["timestamp"],
            reason=row["reason"] or "",
        )

    # ── Claim ─────────────────────────────────────────────────────────────

    def claim(self, scope: ScopeType, key: str, agent_id: str) -> str:
        """Atomically claim *key* for *agent_id*.

        If the key is unclaimed (does not exist), the agent becomes the owner.
        If already claimed, the existing owner's id is returned unchanged.
        """
        cur = self._conn.execute(
            "SELECT value FROM shared_entries WHERE scope = ? AND key = ?",
            (scope.value, key),
        )
        row = cur.fetchone()
        if row is not None:
            return row["value"]

        # Not yet claimed — write the agent_id as the value.
        self.write(scope, key, agent_id, agent_id=agent_id)
        return agent_id

    # ── List ──────────────────────────────────────────────────────────────

    def list_keys(self, scope: ScopeType) -> list[str]:
        """Return all keys stored under *scope*."""
        cur = self._conn.execute(
            "SELECT key FROM shared_entries WHERE scope = ?",
            (scope.value,),
        )
        return [row["key"] for row in cur.fetchall()]

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the underlying database connection."""
        self._conn.close()
