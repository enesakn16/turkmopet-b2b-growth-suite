from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from .actions import SalesAction


@dataclass(frozen=True, slots=True)
class TaskSyncResult:
    created: int
    refreshed: int


def sync_sales_tasks(database: str | Path, actions: Iterable[SalesAction]) -> TaskSyncResult:
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    created = 0
    refreshed = 0
    now = datetime.now(UTC).isoformat()

    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _ensure_schema(connection)
        for action in actions:
            task_key = f"{action.account_id}:{action.action_type}"
            existing = connection.execute(
                "SELECT 1 FROM sales_tasks WHERE task_key = ?",
                (task_key,),
            ).fetchone()
            if existing is None:
                connection.execute(
                    """
                    INSERT INTO sales_tasks (
                        task_key, account_id, priority, action_type,
                        recommended_action, reason, status, assignee,
                        resolution_note, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 'OPEN', '', '', ?, ?)
                    """,
                    (
                        task_key,
                        action.account_id,
                        action.priority,
                        action.action_type,
                        action.recommended_action,
                        action.reason,
                        now,
                        now,
                    ),
                )
                created += 1
            else:
                connection.execute(
                    """
                    UPDATE sales_tasks
                    SET priority = ?, recommended_action = ?, reason = ?, updated_at = ?
                    WHERE task_key = ?
                    """,
                    (
                        action.priority,
                        action.recommended_action,
                        action.reason,
                        now,
                        task_key,
                    ),
                )
                refreshed += 1
        connection.commit()

    return TaskSyncResult(created=created, refreshed=refreshed)


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS sales_tasks (
            task_key TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 3),
            action_type TEXT NOT NULL,
            recommended_action TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN'
                CHECK (status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED')),
            assignee TEXT NOT NULL DEFAULT '',
            resolution_note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_sales_tasks_queue ON sales_tasks(status, priority, account_id)"
    )
