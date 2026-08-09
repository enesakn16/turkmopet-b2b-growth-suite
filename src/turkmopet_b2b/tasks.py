from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from .actions import SalesAction

TASK_STATUSES = ("OPEN", "IN_PROGRESS", "RESOLVED")


@dataclass(frozen=True, slots=True)
class TaskSyncResult:
    created: int
    refreshed: int


@dataclass(frozen=True, slots=True)
class SalesTask:
    task_key: str
    account_id: str
    priority: int
    action_type: str
    recommended_action: str
    reason: str
    status: str
    assignee: str
    resolution_note: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class TaskEvent:
    event_id: int
    task_key: str
    event_type: str
    note: str
    previous_resolution: str
    reopen_reason: str
    created_at: str


def sync_sales_tasks(database: str | Path, actions: Iterable[SalesAction]) -> TaskSyncResult:
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    created = 0
    refreshed = 0
    now = _now()

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


def list_sales_tasks(
    database: str | Path,
    *,
    status: str | None = None,
    assignee: str | None = None,
) -> list[SalesTask]:
    normalized_status = _normalize_status(status) if status is not None else None
    clauses: list[str] = []
    parameters: list[str] = []
    if normalized_status is not None:
        clauses.append("status = ?")
        parameters.append(normalized_status)
    if assignee is not None:
        clauses.append("assignee = ?")
        parameters.append(assignee.strip())

    query = "SELECT * FROM sales_tasks"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY status != 'OPEN', priority, account_id, action_type"

    with _connect_existing(database) as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [SalesTask(*row) for row in rows]


def list_task_events(database: str | Path, task_key: str) -> list[TaskEvent]:
    with _connect_existing(database) as connection:
        _fetch_task(connection, task_key)
        rows = connection.execute(
            """
            SELECT event_id, task_key, event_type, note,
                   previous_resolution, reopen_reason, created_at
            FROM sales_task_events
            WHERE task_key = ?
            ORDER BY event_id
            """,
            (task_key,),
        ).fetchall()
    return [TaskEvent(*row) for row in rows]


def assign_sales_task(database: str | Path, task_key: str, assignee: str) -> SalesTask:
    normalized_assignee = assignee.strip()
    if not normalized_assignee:
        raise ValueError("assignee cannot be empty")
    return _update_task(
        database,
        task_key,
        "assignee = ?, updated_at = ?",
        (normalized_assignee, _now()),
    )


def start_sales_task(database: str | Path, task_key: str) -> SalesTask:
    with _connect_existing(database) as connection:
        current = _fetch_task(connection, task_key)
        if current.status == "RESOLVED":
            raise ValueError(f"resolved task cannot be started: {task_key}")
        connection.execute(
            "UPDATE sales_tasks SET status = 'IN_PROGRESS', updated_at = ? WHERE task_key = ?",
            (_now(), task_key),
        )
        connection.commit()
        return _fetch_task(connection, task_key)


def resolve_sales_task(database: str | Path, task_key: str, resolution_note: str) -> SalesTask:
    note = resolution_note.strip()
    if not note:
        raise ValueError("resolution note cannot be empty")

    with _connect_existing(database) as connection:
        current = _fetch_task(connection, task_key)
        if current.status == "RESOLVED":
            raise ValueError(f"task is already resolved; reopen it before resolving again: {task_key}")
        connection.execute(
            """
            UPDATE sales_tasks
            SET status = 'RESOLVED', resolution_note = ?, updated_at = ?
            WHERE task_key = ?
            """,
            (note, _now(), task_key),
        )
        connection.commit()
        return _fetch_task(connection, task_key)


def reopen_sales_task(database: str | Path, task_key: str, reason: str) -> SalesTask:
    normalized_reason = reason.strip()
    if not normalized_reason:
        raise ValueError("reopen reason cannot be empty")

    with _connect_existing(database) as connection:
        current = _fetch_task(connection, task_key)
        if current.status != "RESOLVED":
            raise ValueError(f"only resolved tasks can be reopened: {task_key}")

        now = _now()
        audit_note = f"previous resolution: {current.resolution_note}\nreopen reason: {normalized_reason}"
        connection.execute(
            """
            INSERT INTO sales_task_events (
                task_key, event_type, note, previous_resolution, reopen_reason, created_at
            ) VALUES (?, 'REOPENED', ?, ?, ?, ?)
            """,
            (task_key, audit_note, current.resolution_note, normalized_reason, now),
        )
        connection.execute(
            """
            UPDATE sales_tasks
            SET status = 'OPEN', resolution_note = '', updated_at = ?
            WHERE task_key = ?
            """,
            (now, task_key),
        )
        connection.commit()
        return _fetch_task(connection, task_key)


def _update_task(
    database: str | Path,
    task_key: str,
    assignment_sql: str,
    parameters: tuple[str, ...],
) -> SalesTask:
    with _connect_existing(database) as connection:
        _fetch_task(connection, task_key)
        connection.execute(
            f"UPDATE sales_tasks SET {assignment_sql} WHERE task_key = ?",
            (*parameters, task_key),
        )
        connection.commit()
        return _fetch_task(connection, task_key)


def _connect_existing(database: str | Path) -> sqlite3.Connection:
    path = Path(database)
    if not path.is_file():
        raise ValueError(f"task database does not exist: {path}")
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    _ensure_schema(connection)
    return connection


def _fetch_task(connection: sqlite3.Connection, task_key: str) -> SalesTask:
    row = connection.execute(
        "SELECT * FROM sales_tasks WHERE task_key = ?",
        (task_key,),
    ).fetchone()
    if row is None:
        raise ValueError(f"sales task not found: {task_key}")
    return SalesTask(*row)


def _normalize_status(status: str) -> str:
    normalized = status.strip().upper()
    if normalized not in TASK_STATUSES:
        raise ValueError(f"invalid task status: {status}")
    return normalized


def _now() -> str:
    return datetime.now(UTC).isoformat()


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
        """
        CREATE TABLE IF NOT EXISTS sales_task_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_key TEXT NOT NULL,
            event_type TEXT NOT NULL CHECK (event_type IN ('REOPENED')),
            note TEXT NOT NULL,
            previous_resolution TEXT NOT NULL DEFAULT '',
            reopen_reason TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (task_key) REFERENCES sales_tasks(task_key) ON DELETE CASCADE
        )
        """
    )
    _ensure_event_columns(connection)
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_sales_tasks_queue ON sales_tasks(status, priority, account_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_sales_task_events_task ON sales_task_events(task_key, event_id)"
    )


def _ensure_event_columns(connection: sqlite3.Connection) -> None:
    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(sales_task_events)").fetchall()
    }
    if "previous_resolution" not in columns:
        connection.execute(
            "ALTER TABLE sales_task_events ADD COLUMN previous_resolution TEXT NOT NULL DEFAULT ''"
        )
    if "reopen_reason" not in columns:
        connection.execute(
            "ALTER TABLE sales_task_events ADD COLUMN reopen_reason TEXT NOT NULL DEFAULT ''"
        )
