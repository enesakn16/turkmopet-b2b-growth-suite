from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .tasks import SalesTask

SLA_HOURS_BY_PRIORITY = {1: 24, 2: 72, 3: 168}


def task_due_at(task: SalesTask) -> datetime:
    created_at = datetime.fromisoformat(task.created_at)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return created_at + timedelta(hours=SLA_HOURS_BY_PRIORITY[task.priority])


def task_sla_status(task: SalesTask, *, now: datetime | None = None) -> str:
    if task.status == "RESOLVED":
        return "RESOLVED"
    reference = now or datetime.now(UTC)
    return "OVERDUE" if reference > task_due_at(task) else "ON_TIME"


def overdue_tasks(tasks: list[SalesTask], *, now: datetime | None = None) -> list[SalesTask]:
    return [task for task in tasks if task_sla_status(task, now=now) == "OVERDUE"]
