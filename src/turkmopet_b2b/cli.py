from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import build_reports, load_accounts, write_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="b2b-score",
        description="Score wholesale accounts from CSV and export recommended sales actions.",
    )
    parser.add_argument("--input", required=True, type=Path, help="Source account CSV")
    parser.add_argument("--output", required=True, type=Path, help="Destination report CSV")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        reports = build_reports(load_accounts(args.input))
        write_reports(args.output, reports)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"scored {len(reports)} accounts -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
