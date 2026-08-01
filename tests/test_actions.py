import csv
import tempfile
import unittest
from pathlib import Path

from turkmopet_b2b.actions import build_sales_actions, write_sales_actions
from turkmopet_b2b.history import ScoreMovement, ScoreTrend


class SalesActionTests(unittest.TestCase):
    def test_build_actions_prioritizes_lost_and_sharply_declining_accounts(self) -> None:
        trends = [
            ScoreTrend("stable", 50, 50, 0, "growth", "growth", ScoreMovement.STABLE),
            ScoreTrend("decline-small", 70, 65, -5, "growth", "growth", ScoreMovement.DECLINED),
            ScoreTrend("decline-large", 80, 60, -20, "pro", "growth", ScoreMovement.DECLINED),
            ScoreTrend("missing", 55, None, None, "growth", None, ScoreMovement.MISSING),
            ScoreTrend("improved", 40, 65, 25, "starter", "growth", ScoreMovement.IMPROVED),
            ScoreTrend("new", None, 45, None, None, "starter", ScoreMovement.NEW),
        ]

        actions = build_sales_actions(trends)

        self.assertEqual(
            [action.account_id for action in actions],
            ["decline-large", "missing", "decline-small", "improved", "new"],
        )
        self.assertEqual(actions[0].action_type, "win_back")
        self.assertEqual(actions[0].priority, 1)
        self.assertEqual(actions[1].action_type, "inactive_check")
        self.assertEqual(actions[2].priority, 2)
        self.assertEqual(actions[3].action_type, "upsell")
        self.assertNotIn("stable", {action.account_id for action in actions})

    def test_tier_drop_is_priority_one_even_for_small_score_change(self) -> None:
        trend = ScoreTrend("A", 76, 74, -2, "pro", "growth", ScoreMovement.DECLINED)
        action = build_sales_actions([trend])[0]
        self.assertEqual(action.priority, 1)

    def test_write_actions_is_excel_compatible_and_atomic(self) -> None:
        trend = ScoreTrend("A", 80, 60, -20, "pro", "growth", ScoreMovement.DECLINED)
        actions = build_sales_actions([trend])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "reports" / "actions.csv"
            output.parent.mkdir(parents=True)
            output.write_text("old", encoding="utf-8")

            write_sales_actions(output, actions)

            with output.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["account_id"], "A")
            self.assertEqual(rows[0]["priority"], "1")
            self.assertEqual(rows[0]["action_type"], "win_back")
            self.assertEqual(list(output.parent.glob(f".{output.name}.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
