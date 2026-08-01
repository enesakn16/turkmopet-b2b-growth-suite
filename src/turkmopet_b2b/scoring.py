from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class AccountTier(str, Enum):
    STARTER = "starter"
    GROWTH = "growth"
    PRO = "pro"


@dataclass(frozen=True, slots=True)
class WholesaleAccount:
    monthly_order_value: float
    active_months: int
    payment_delay_days: int = 0
    return_rate: float = 0.0
    has_tax_certificate: bool = False


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    total: int
    tier: AccountTier
    reasons: tuple[str, ...]


def score_account(account: WholesaleAccount) -> ScoreBreakdown:
    _validate(account)
    score = 0
    reasons: list[str] = []

    if account.has_tax_certificate:
        score += 20
        reasons.append("verified-business")

    if account.monthly_order_value >= 100_000:
        score += 40
        reasons.append("high-volume")
    elif account.monthly_order_value >= 30_000:
        score += 25
        reasons.append("mid-volume")
    elif account.monthly_order_value >= 10_000:
        score += 10
        reasons.append("developing-volume")

    if account.active_months >= 12:
        score += 20
        reasons.append("long-term")
    elif account.active_months >= 3:
        score += 10
        reasons.append("established")

    if account.payment_delay_days == 0:
        score += 15
        reasons.append("on-time-payment")
    elif account.payment_delay_days <= 7:
        score += 5
        reasons.append("minor-payment-delay")
    else:
        score -= 20
        reasons.append("payment-risk")

    if account.return_rate <= 0.02:
        score += 5
        reasons.append("low-return-rate")
    elif account.return_rate > 0.10:
        score -= 15
        reasons.append("high-return-rate")

    total = max(0, min(score, 100))
    return ScoreBreakdown(total=total, tier=_tier_for(total), reasons=tuple(reasons))


def rank_accounts(accounts: Iterable[WholesaleAccount]) -> list[ScoreBreakdown]:
    return sorted((score_account(account) for account in accounts), key=lambda item: item.total, reverse=True)


def _tier_for(score: int) -> AccountTier:
    if score >= 75:
        return AccountTier.PRO
    if score >= 45:
        return AccountTier.GROWTH
    return AccountTier.STARTER


def _validate(account: WholesaleAccount) -> None:
    if account.monthly_order_value < 0:
        raise ValueError("monthly_order_value cannot be negative")
    if account.active_months < 0:
        raise ValueError("active_months cannot be negative")
    if account.payment_delay_days < 0:
        raise ValueError("payment_delay_days cannot be negative")
    if not 0 <= account.return_rate <= 1:
        raise ValueError("return_rate must be between 0 and 1")
