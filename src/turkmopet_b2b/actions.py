from __future__ import annotations

import csv
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .history import ScoreMovement, ScoreTrend


@dataclass(frozen=True, slots=True)
class SalesAction:
    account_id: str
    priority: int
    action_type: str
    recommended_action: str
    reason: str


def build_sales_actions(trends: Iterable[ScoreTrend]) -> list[SalesAction]:
    actions: list[SalesAction] = []
    for trend in trends:
        action = _action_for_trend(trend)
        if action is not None:
            actions.append(action)
    return sorted(actions, key=lambda item: (item.priority, item.account_id))


def write_sales_actions(path: str | Path, actions: Iterable[SalesAction]) -> None:
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
                fieldnames=["account_id", "priority", "action_type", "recommended_action", "reason"],
            )
            writer.writeheader()
            for action in actions:
                writer.writerow(
                    {
                        "account_id": action.account_id,
                        "priority": action.priority,
                        "action_type": action.action_type,
                        "recommended_action": action.recommended_action,
                        "reason": action.reason,
                    }
                )
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, target)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _action_for_trend(trend: ScoreTrend) -> SalesAction | None:
    if trend.movement is ScoreMovement.DECLINED:
        delta = abs(trend.score_delta or 0)
        priority = 1 if delta >= 15 or trend.current_tier != trend.previous_tier else 2
        return SalesAction(
            trend.account_id,
            priority,
            "win_back",
            "Müşteriyi 1 iş günü içinde ara; skor düşüşünün nedenini doğrula ve geri kazanım teklifi hazırla.",
            f"Skor {delta} puan düştü ({trend.previous_tier} -> {trend.current_tier}).",
        )
    if trend.movement is ScoreMovement.MISSING:
        return SalesAction(
            trend.account_id,
            1,
            "inactive_check",
            "Hesabın neden güncel raporda olmadığını kontrol et; veri sorunu yoksa pasif müşteri araması aç.",
            "Müşteri önceki dönemde vardı ancak güncel raporda bulunmuyor.",
        )
    if trend.movement is ScoreMovement.IMPROVED:
        return SalesAction(
            trend.account_id,
            3,
            "upsell",
            "Müşterinin yeni segmentine uygun iskonto, ürün grubu veya hacim teklifi hazırla.",
            f"Skor {trend.score_delta} puan yükseldi ({trend.previous_tier} -> {trend.current_tier}).",
        )
    if trend.movement is ScoreMovement.NEW:
        return SalesAction(
            trend.account_id,
            3,
            "onboarding",
            "İlk sipariş ve B2B kullanım adımlarını içeren onboarding teması oluştur.",
            "Müşteri güncel rapora yeni girdi.",
        )
    return None
