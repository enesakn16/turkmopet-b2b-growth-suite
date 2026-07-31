from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .history import compare_score_snapshots, load_score_snapshot, write_score_trends


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="b2b-trend",
        description="Compare two B2B score reports and export account score movements.",
    )
    parser.add_argument("--previous", required=True, type=Path, help="Previous scored account CSV")
    parser.add_argument("--current", required=True, type=Path, help="Current scored account CSV")
    parser.add_argument("--output", required=True, type=Path, help="Destination trend CSV")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        trends = compare_score_snapshots(
            load_score_snapshot(args.previous),
            load_score_snapshot(args.current),
        )
        write_score_trends(args.output, trends)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    declined = sum(trend.movement.value == "declined" for trend in trends)
    missing = sum(trend.movement.value == "missing" for trend in trends)
    print(f"compared {len(trends)} accounts -> {args.output} ({declined} declined, {missing} missing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
