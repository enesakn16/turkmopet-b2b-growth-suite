from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .scoring import AccountTier, ScoreBreakdown, WholesaleAccount, score_account


REQUIRED_COLUMNS = {
    "account_id",
    "monthly_order_value",
    "active_months",
    "payment_delay_days",
    "return_rate",
    "has_tax_certificate",
}


@dataclass(frozen=True, slots=True)
class AccountReport:
    account_id: str
    score: int
    tier: AccountTier
    recommended_action: str
    reasons: tuple[str, ...]


def load_accounts(path: str | Path) -> list[tuple[str, WholesaleAccount]]:
    source = Path(path)
    try:
        handle = source.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise ValueError(f"cannot open CSV file: {source}") from exc

    with handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or ())
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"missing CSV columns: {', '.join(sorted(missing))}")

        accounts: list[tuple[str, WholesaleAccount]] = []
        seen_ids: set[str] = set()
        for line_number, row in enumerate(reader, start=2):
            account_id = (row.get("account_id") or "").strip()
            if not account_id:
                raise ValueError(f"line {line_number}: account_id is required")
            if account_id in seen_ids:
                raise ValueError(f"line {line_number}: duplicate account_id '{account_id}'")

            try:
                account = WholesaleAccount(
                    monthly_order_value=float(row["monthly_order_value"]),
                    active_months=int(row["active_months"]),
                    payment_delay_days=int(row["payment_delay_days"]),
                    return_rate=float(row["return_rate"]),
                    has_tax_certificate=_parse_bool(row["has_tax_certificate"]),
                )
                score_account(account)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"line {line_number}: invalid account data: {exc}") from exc

            seen_ids.add(account_id)
            accounts.append((account_id, account))

    return accounts


def build_reports(accounts: Iterable[tuple[str, WholesaleAccount]]) -> list[AccountReport]:
    reports = [
        _to_report(account_id, score_account(account))
        for account_id, account in accounts
    ]
    return sorted(reports, key=lambda item: (-item.score, item.account_id))


def write_reports(path: str | Path, reports: Iterable[AccountReport]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["account_id", "score", "tier", "recommended_action", "reasons"],
        )
        writer.writeheader()
        for report in reports:
            writer.writerow(
                {
                    "account_id": report.account_id,
                    "score": report.score,
                    "tier": report.tier.value,
                    "recommended_action": report.recommended_action,
                    "reasons": "|".join(report.reasons),
                }
            )


def _to_report(account_id: str, result: ScoreBreakdown) -> AccountReport:
    return AccountReport(
        account_id=account_id,
        score=result.total,
        tier=result.tier,
        recommended_action=_recommend_action(result),
        reasons=result.reasons,
    )


def _recommend_action(result: ScoreBreakdown) -> str:
    reasons = set(result.reasons)
    if "payment-risk" in reasons:
        return "review-payment-risk"
    if "high-return-rate" in reasons:
        return "review-return-pattern"
    if result.tier is AccountTier.PRO:
        return "offer-key-account-plan"
    if result.tier is AccountTier.GROWTH:
        return "schedule-growth-call"
    if "verified-business" not in reasons:
        return "request-tax-certificate"
    return "nurture-account"


def _parse_bool(value: str) -> bool:
    normalized = value.strip().casefold()
    if normalized in {"1", "true", "yes", "evet"}:
        return True
    if normalized in {"0", "false", "no", "hayir", "hayır"}:
        return False
    raise ValueError("has_tax_certificate must be a boolean value")
