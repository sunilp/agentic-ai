"""SQLite-backed memory store with vector similarity search."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

import numpy as np

from src.ch12_memory.types import MemoryCategory, MemoryRecord, MemoryStoreStats


class MemoryStore:
    """Persistent memory store backed by SQLite with numpy cosine similarity.

    Embeddings are stored as numpy float32 arrays serialised to bytes in a
    BLOB column.  Similarity search loads all embeddings into Python and
    computes cosine similarity via numpy -- practical for the tens-of-thousands
    scale typical of per-agent episodic memory.
    """

    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_table()

    # ── Schema ───────────────────────────────────────────────────────────

    def _create_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id              TEXT PRIMARY KEY,
                query           TEXT NOT NULL,
                context         TEXT NOT NULL,
                outcome         TEXT NOT NULL,
                correction      TEXT,
                category        TEXT NOT NULL,
                timestamp       TEXT NOT NULL,
                access_count    INTEGER NOT NULL DEFAULT 0,
                usefulness_score REAL NOT NULL DEFAULT 0.0,
                embedding       BLOB
            )
            """
        )
        self._conn.commit()

    # ── CRUD ─────────────────────────────────────────────────────────────

    def store(self, record: MemoryRecord) -> str:
        """Persist a memory record and return its assigned ID."""
        record_id = str(uuid.uuid4())
        embedding_blob = self._encode_embedding(record.embedding) if record.embedding else None
        self._conn.execute(
            """
            INSERT INTO memories
                (id, query, context, outcome, correction, category,
                 timestamp, access_count, usefulness_score, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                record.query,
                record.context,
                record.outcome,
                record.correction,
                record.category.value,
                record.timestamp.isoformat(),
                record.access_count,
                record.usefulness_score,
                embedding_blob,
            ),
        )
        self._conn.commit()
        return record_id

    def get(self, record_id: str) -> MemoryRecord | None:
        """Retrieve a single record by ID, or None if not found."""
        cur = self._conn.execute("SELECT * FROM memories WHERE id = ?", (record_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def forget(self, record_id: str) -> bool:
        """Delete a record. Returns True if a row was actually removed."""
        cur = self._conn.execute("DELETE FROM memories WHERE id = ?", (record_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def record_access(self, record_id: str, usefulness_delta: float = 0.0) -> None:
        """Increment access_count by 1 and add *usefulness_delta* to the score."""
        self._conn.execute(
            """
            UPDATE memories
               SET access_count    = access_count + 1,
                   usefulness_score = usefulness_score + ?
             WHERE id = ?
            """,
            (usefulness_delta, record_id),
        )
        self._conn.commit()

    # ── Vector similarity ────────────────────────────────────────────────

    def retrieve_similar(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[MemoryRecord]:
        """Return the *top_k* records most similar to *query_embedding* by cosine similarity."""
        query_vec = np.asarray(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []

        cur = self._conn.execute("SELECT * FROM memories WHERE embedding IS NOT NULL")
        scored: list[tuple[float, sqlite3.Row]] = []
        for row in cur.fetchall():
            emb = self._decode_embedding(row["embedding"])
            if emb is None:
                continue
            emb_norm = np.linalg.norm(emb)
            if emb_norm == 0:
                continue
            similarity = float(np.dot(query_vec, emb) / (query_norm * emb_norm))
            scored.append((similarity, row))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [self._row_to_record(row) for _, row in scored[:top_k]]

    # ── Maintenance ──────────────────────────────────────────────────────

    def find_stale(self, max_age_days: int = 30) -> list[MemoryRecord]:
        """Return records with zero accesses older than *max_age_days*."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
        cur = self._conn.execute(
            """
            SELECT * FROM memories
             WHERE access_count = 0
               AND timestamp < ?
            """,
            (cutoff,),
        )
        return [self._row_to_record(row) for row in cur.fetchall()]

    def stats(self) -> MemoryStoreStats:
        """Return aggregate statistics about the store."""
        cur = self._conn.execute(
            """
            SELECT
                COUNT(*),
                SUM(CASE WHEN access_count = 0 THEN 1 ELSE 0 END),
                AVG(usefulness_score),
                AVG(access_count)
            FROM memories
            """
        )
        row = cur.fetchone()
        total = row[0] or 0
        return MemoryStoreStats(
            total_records=total,
            stale_records=row[1] or 0,
            avg_usefulness=row[2] or 0.0,
            avg_access_count=row[3] or 0.0,
        )

    def close(self) -> None:
        """Close the underlying database connection."""
        self._conn.close()

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _encode_embedding(embedding: list[float]) -> bytes:
        return np.asarray(embedding, dtype=np.float32).tobytes()

    @staticmethod
    def _decode_embedding(blob: bytes | None) -> np.ndarray | None:
        if blob is None:
            return None
        return np.frombuffer(blob, dtype=np.float32)

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> MemoryRecord:
        embedding = MemoryStore._decode_embedding(row["embedding"])
        return MemoryRecord(
            id=row["id"],
            query=row["query"],
            context=row["context"],
            outcome=row["outcome"],
            correction=row["correction"],
            category=MemoryCategory(row["category"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            access_count=row["access_count"],
            usefulness_score=row["usefulness_score"],
            embedding=embedding.tolist() if embedding is not None else [],
        )
