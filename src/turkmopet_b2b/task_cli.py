from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from .tasks import (
    TASK_STATUSES,
    assign_sales_task,
    list_sales_tasks,
    reopen_sales_task,
    resolve_sales_task,
    start_sales_task,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage persistent B2B sales tasks")
    parser.add_argument("--database", type=Path, required=True, help="SQLite sales task database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List tasks in priority order")
    list_parser.add_argument("--status", choices=TASK_STATUSES)
    list_parser.add_argument("--assignee")
    list_parser.add_argument("--output", type=Path, help="Optional Excel-compatible CSV output")

    assign_parser = subparsers.add_parser("assign", help="Assign a task")
    assign_parser.add_argument("task_key")
    assign_parser.add_argument("assignee")

    start_parser = subparsers.add_parser("start", help="Mark a task as in progress")
    start_parser.add_argument("task_key")

    resolve_parser = subparsers.add_parser("resolve", help="Resolve a task with a mandatory note")
    resolve_parser.add_argument("task_key")
    resolve_parser.add_argument("--note", required=True)

    reopen_parser = subparsers.add_parser(
        "reopen",
        help="Reopen a resolved task while preserving its previous resolution in the audit log",
    )
    reopen_parser.add_argument("task_key")
    reopen_parser.add_argument("--reason", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "list":
            tasks = list_sales_tasks(args.database, status=args.status, assignee=args.assignee)
            if args.output is not None:
                _write_tasks(args.output, tasks)
                print(f"wrote {len(tasks)} sales tasks -> {args.output}")
            else:
                _print_tasks(tasks)
            return 0

        if args.command == "assign":
            task = assign_sales_task(args.database, args.task_key, args.assignee)
            print(f"assigned {task.task_key} -> {task.assignee}")
            return 0

        if args.command == "start":
            task = start_sales_task(args.database, args.task_key)
            print(f"started {task.task_key}")
            return 0

        if args.command == "resolve":
            task = resolve_sales_task(args.database, args.task_key, args.note)
            print(f"resolved {task.task_key}")
            return 0

        task = reopen_sales_task(args.database, args.task_key, args.reason)
        print(f"reopened {task.task_key}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _print_tasks(tasks: list[object]) -> None:
    if not tasks:
        print("no sales tasks found")
        return
    for task in tasks:
        assignee = task.assignee or "unassigned"
        print(
            f"P{task.priority} {task.status:<11} {task.task_key} "
            f"[{assignee}] {task.recommended_action}"
        )


def _write_tasks(path: Path, tasks: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "task_key",
        "account_id",
        "priority",
        "action_type",
        "recommended_action",
        "reason",
        "status",
        "assignee",
        "resolution_note",
        "created_at",
        "updated_at",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for task in tasks:
            writer.writerow({field: getattr(task, field) for field in fields})


if __name__ == "__main__":
    raise SystemExit(main())
