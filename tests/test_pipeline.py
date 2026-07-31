import csv
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from turkmopet_b2b import AccountTier
from turkmopet_b2b.pipeline import AccountReport, build_reports, load_accounts, write_reports


class AccountPipelineTests(unittest.TestCase):
    def test_load_score_and_export_accounts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "accounts.csv"
            output = root / "reports" / "scored.csv"
            source.write_text(
                "account_id,monthly_order_value,active_months,payment_delay_days,return_rate,has_tax_certificate\n"
                "B2B-002,120000,18,0,0.01,evet\n"
                "B2B-001,35000,6,20,0.20,true\n",
                encoding="utf-8",
            )

            reports = build_reports(load_accounts(source))
            write_reports(output, reports)

            self.assertEqual([report.account_id for report in reports], ["B2B-002", "B2B-001"])
            self.assertEqual(reports[0].recommended_action, "offer-key-account-plan")
            self.assertEqual(reports[1].recommended_action, "review-payment-risk")

            with output.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["tier"], "pro")
            self.assertEqual(rows[1]["recommended_action"], "review-payment-risk")
            self.assertEqual(list(output.parent.glob(f".{output.name}.*.tmp")), [])

    def test_existing_report_is_replaced_completely(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "scored.csv"
            output.write_text("stale,partial,data\n", encoding="utf-8")
            report = AccountReport(
                account_id="B2B-001",
                score=80,
                tier=AccountTier.PRO,
                recommended_action="offer-key-account-plan",
                reasons=("verified-business", "high-volume"),
            )

            write_reports(output, [report])

            content = output.read_text(encoding="utf-8-sig")
            self.assertNotIn("stale,partial,data", content)
            self.assertIn("B2B-001,80,pro,offer-key-account-plan", content)

    def test_failed_replace_preserves_existing_report_and_cleans_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "scored.csv"
            output.write_text("trusted-report\n", encoding="utf-8")
            report = AccountReport(
                account_id="B2B-001",
                score=80,
                tier=AccountTier.PRO,
                recommended_action="offer-key-account-plan",
                reasons=("verified-business",),
            )

            with mock.patch("turkmopet_b2b.pipeline.os.replace", side_effect=OSError("disk failure")):
                with self.assertRaisesRegex(OSError, "disk failure"):
                    write_reports(output, [report])

            self.assertEqual(output.read_text(encoding="utf-8"), "trusted-report\n")
            self.assertEqual(list(output.parent.glob(f".{output.name}.*.tmp")), [])

    def test_duplicate_account_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "accounts.csv"
            source.write_text(
                "account_id,monthly_order_value,active_months,payment_delay_days,return_rate,has_tax_certificate\n"
                "B2B-001,10000,3,0,0.01,true\n"
                "B2B-001,20000,6,0,0.01,true\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate account_id"):
                load_accounts(source)

    def test_missing_columns_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "accounts.csv"
            source.write_text("account_id,monthly_order_value\nB2B-001,10000\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing CSV columns"):
                load_accounts(source)


if __name__ == "__main__":
    unittest.main()
