from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from .sla import overdue_tasks, task_due_at
from .tasks import list_sales_tasks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export overdue B2B sales tasks")
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assignee")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        tasks = overdue_tasks(list_sales_tasks(args.database, assignee=args.assignee))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["task_key", "account_id", "priority", "assignee", "status", "due_at", "recommended_action", "reason"],
            )
            writer.writeheader()
            for task in tasks:
                writer.writerow(
                    {
                        "task_key": task.task_key,
                        "account_id": task.account_id,
                        "priority": task.priority,
                        "assignee": task.assignee,
                        "status": task.status,
                        "due_at": task_due_at(task).isoformat(),
                        "recommended_action": task.recommended_action,
                        "reason": task.reason,
                    }
                )
        print(f"wrote {len(tasks)} overdue sales tasks -> {args.output}")
        return 1 if tasks else 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
