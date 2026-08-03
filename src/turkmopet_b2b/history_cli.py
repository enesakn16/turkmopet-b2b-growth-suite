from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .actions import build_sales_actions, write_sales_actions
from .history import compare_score_snapshots, load_score_snapshot, write_score_trends
from .tasks import sync_sales_tasks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="b2b-trend",
        description="Compare two B2B score reports and export account score movements.",
    )
    parser.add_argument("--previous", required=True, type=Path, help="Previous scored account CSV")
    parser.add_argument("--current", required=True, type=Path, help="Current scored account CSV")
    parser.add_argument("--output", required=True, type=Path, help="Destination trend CSV")
    parser.add_argument(
        "--actions-output",
        type=Path,
        help="Optional destination for prioritized sales actions generated from the same comparison",
    )
    parser.add_argument(
        "--task-database",
        type=Path,
        help="Optional SQLite database that keeps sales tasks and their workflow state",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        trends = compare_score_snapshots(
            load_score_snapshot(args.previous),
            load_score_snapshot(args.current),
        )
        write_score_trends(args.output, trends)
        should_build_actions = args.actions_output is not None or args.task_database is not None
        actions = build_sales_actions(trends) if should_build_actions else []
        if args.actions_output is not None:
            write_sales_actions(args.actions_output, actions)
        task_sync = sync_sales_tasks(args.task_database, actions) if args.task_database is not None else None
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    declined = sum(trend.movement.value == "declined" for trend in trends)
    missing = sum(trend.movement.value == "missing" for trend in trends)
    summary = f"compared {len(trends)} accounts -> {args.output} ({declined} declined, {missing} missing)"
    if args.actions_output is not None:
        summary += f"; wrote {len(actions)} sales actions -> {args.actions_output}"
    if task_sync is not None:
        summary += (
            f"; synchronized tasks -> {args.task_database} "
            f"({task_sync.created} created, {task_sync.refreshed} refreshed)"
        )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
