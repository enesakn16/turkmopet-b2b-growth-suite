import csv
import tempfile
import unittest
from pathlib import Path

from turkmopet_b2b.history import (
    ScoreMovement,
    compare_score_snapshots,
    load_score_snapshot,
    write_score_trends,
)
from turkmopet_b2b.history_cli import main


class ScoreHistoryTests(unittest.TestCase):
    def test_compare_prioritizes_declines_and_tracks_account_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = root / "previous.csv"
            current = root / "current.csv"
            previous.write_text(
                "account_id,score,tier\nA,80,pro\nB,60,growth\nC,40,starter\nD,55,growth\n",
                encoding="utf-8",
            )
            current.write_text(
                "account_id,score,tier\nA,65,growth\nB,75,pro\nC,40,starter\nE,50,growth\n",
                encoding="utf-8",
            )

            trends = compare_score_snapshots(load_score_snapshot(previous), load_score_snapshot(current))

            self.assertEqual([trend.account_id for trend in trends], ["A", "D", "B", "E", "C"])
            self.assertEqual(trends[0].movement, ScoreMovement.DECLINED)
            self.assertEqual(trends[0].score_delta, -15)
            self.assertEqual(trends[1].movement, ScoreMovement.MISSING)
            self.assertEqual(trends[2].movement, ScoreMovement.IMPROVED)
            self.assertEqual(trends[3].movement, ScoreMovement.NEW)
            self.assertEqual(trends[4].movement, ScoreMovement.STABLE)

    def test_write_trends_creates_excel_compatible_report_without_temp_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = root / "previous.csv"
            current = root / "current.csv"
            output = root / "reports" / "trend.csv"
            previous.write_text("account_id,score,tier\nA,80,pro\n", encoding="utf-8")
            current.write_text("account_id,score,tier\nA,60,growth\n", encoding="utf-8")

            trends = compare_score_snapshots(load_score_snapshot(previous), load_score_snapshot(current))
            write_score_trends(output, trends)

            with output.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["score_delta"], "-20")
            self.assertEqual(rows[0]["movement"], "declined")
            self.assertEqual(list(output.parent.glob(f".{output.name}.*.tmp")), [])

    def test_invalid_score_is_rejected_with_line_number(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.csv"
            report.write_text("account_id,score,tier\nA,101,pro\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "line 2: score must be between 0 and 100"):
                load_score_snapshot(report)

    def test_cli_writes_report_and_summarizes_declines_and_missing_accounts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = root / "previous.csv"
            current = root / "current.csv"
            output = root / "trend.csv"
            previous.write_text("account_id,score,tier\nA,80,pro\nB,50,growth\n", encoding="utf-8")
            current.write_text("account_id,score,tier\nA,70,growth\n", encoding="utf-8")

            result = main(["--previous", str(previous), "--current", str(current), "--output", str(output)])

            self.assertEqual(result, 0)
            self.assertTrue(output.exists())

    def test_cli_can_generate_trends_and_prioritized_actions_in_one_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = root / "previous.csv"
            current = root / "current.csv"
            trends_output = root / "reports" / "trend.csv"
            actions_output = root / "reports" / "actions.csv"
            previous.write_text(
                "account_id,score,tier\nA,80,pro\nB,50,growth\nC,40,starter\n",
                encoding="utf-8",
            )
            current.write_text(
                "account_id,score,tier\nA,60,growth\nC,40,starter\nD,55,growth\n",
                encoding="utf-8",
            )

            result = main(
                [
                    "--previous",
                    str(previous),
                    "--current",
                    str(current),
                    "--output",
                    str(trends_output),
                    "--actions-output",
                    str(actions_output),
                ]
            )

            self.assertEqual(result, 0)
            self.assertTrue(trends_output.exists())
            with actions_output.open("r", encoding="utf-8-sig", newline="") as handle:
                actions = list(csv.DictReader(handle))
            self.assertEqual([row["account_id"] for row in actions], ["A", "B", "D"])
            self.assertEqual([row["action_type"] for row in actions], ["win_back", "inactive_check", "onboarding"])
            self.assertEqual([row["priority"] for row in actions], ["1", "1", "3"])
            self.assertEqual(list(actions_output.parent.glob(f".{actions_output.name}.*.tmp")), [])

    def test_cli_keeps_actions_output_optional_for_backward_compatibility(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = root / "previous.csv"
            current = root / "current.csv"
            output = root / "trend.csv"
            previous.write_text("account_id,score,tier\nA,80,pro\n", encoding="utf-8")
            current.write_text("account_id,score,tier\nA,70,growth\n", encoding="utf-8")

            result = main(["--previous", str(previous), "--current", str(current), "--output", str(output)])

            self.assertEqual(result, 0)
            self.assertTrue(output.exists())
            self.assertFalse((root / "actions.csv").exists())


if __name__ == "__main__":
    unittest.main()
