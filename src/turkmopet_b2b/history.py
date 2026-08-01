from __future__ import annotations

import csv
import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


class ScoreMovement(str, Enum):
    DECLINED = "declined"
    MISSING = "missing"
    IMPROVED = "improved"
    NEW = "new"
    STABLE = "stable"


@dataclass(frozen=True, slots=True)
class ScoreSnapshot:
    account_id: str
    score: int
    tier: str


@dataclass(frozen=True, slots=True)
class ScoreTrend:
    account_id: str
    previous_score: int | None
    current_score: int | None
    score_delta: int | None
    previous_tier: str | None
    current_tier: str | None
    movement: ScoreMovement


def load_score_snapshot(path: str | Path) -> dict[str, ScoreSnapshot]:
    source = Path(path)
    try:
        handle = source.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise ValueError(f"cannot open score report: {source}") from exc

    with handle:
        reader = csv.DictReader(handle)
        required = {"account_id", "score", "tier"}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"missing score report columns: {', '.join(sorted(missing))}")

        snapshots: dict[str, ScoreSnapshot] = {}
        for line_number, row in enumerate(reader, start=2):
            account_id = (row.get("account_id") or "").strip()
            if not account_id:
                raise ValueError(f"line {line_number}: account_id is required")
            if account_id in snapshots:
                raise ValueError(f"line {line_number}: duplicate account_id '{account_id}'")
            try:
                score = int(row["score"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"line {line_number}: score must be an integer") from exc
            if not 0 <= score <= 100:
                raise ValueError(f"line {line_number}: score must be between 0 and 100")
            tier = (row.get("tier") or "").strip()
            if not tier:
                raise ValueError(f"line {line_number}: tier is required")
            snapshots[account_id] = ScoreSnapshot(account_id, score, tier)

    return snapshots


def compare_score_snapshots(
    previous: dict[str, ScoreSnapshot],
    current: dict[str, ScoreSnapshot],
) -> list[ScoreTrend]:
    trends = [_build_trend(account_id, previous.get(account_id), current.get(account_id)) for account_id in previous.keys() | current.keys()]
    priority = {
        ScoreMovement.DECLINED: 0,
        ScoreMovement.MISSING: 1,
        ScoreMovement.IMPROVED: 2,
        ScoreMovement.NEW: 3,
        ScoreMovement.STABLE: 4,
    }
    return sorted(
        trends,
        key=lambda item: (
            priority[item.movement],
            item.score_delta if item.score_delta is not None else 0,
            item.account_id,
        ),
    )


def write_score_trends(path: str | Path, trends: Iterable[ScoreTrend]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "account_id",
                    "previous_score",
                    "current_score",
                    "score_delta",
                    "previous_tier",
                    "current_tier",
                    "movement",
                ],
            )
            writer.writeheader()
            for trend in trends:
                writer.writerow(
                    {
                        "account_id": trend.account_id,
                        "previous_score": _csv_value(trend.previous_score),
                        "current_score": _csv_value(trend.current_score),
                        "score_delta": _csv_value(trend.score_delta),
                        "previous_tier": trend.previous_tier or "",
                        "current_tier": trend.current_tier or "",
                        "movement": trend.movement.value,
                    }
                )
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, target)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _build_trend(account_id: str, previous: ScoreSnapshot | None, current: ScoreSnapshot | None) -> ScoreTrend:
    if previous is None and current is not None:
        return ScoreTrend(account_id, None, current.score, None, None, current.tier, ScoreMovement.NEW)
    if previous is not None and current is None:
        return ScoreTrend(account_id, previous.score, None, None, previous.tier, None, ScoreMovement.MISSING)
    assert previous is not None and current is not None
    delta = current.score - previous.score
    movement = ScoreMovement.IMPROVED if delta > 0 else ScoreMovement.DECLINED if delta < 0 else ScoreMovement.STABLE
    return ScoreTrend(account_id, previous.score, current.score, delta, previous.tier, current.tier, movement)


def _csv_value(value: int | None) -> int | str:
    return "" if value is None else value
