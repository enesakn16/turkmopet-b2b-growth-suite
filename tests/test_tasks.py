import sqlite3
import tempfile
import unittest
from pathlib import Path

from turkmopet_b2b.actions import SalesAction
from turkmopet_b2b.tasks import sync_sales_tasks


class SalesTaskTests(unittest.TestCase):
    def test_sync_creates_prioritized_open_tasks(self) -> None:
        actions = [
            SalesAction("B2B-001", 1, "win_back", "Ara", "Skor düştü"),
            SalesAction("B2B-002", 3, "upsell", "Teklif hazırla", "Skor yükseldi"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "sales.db"

            result = sync_sales_tasks(database, actions)

            self.assertEqual((result.created, result.refreshed), (2, 0))
            with sqlite3.connect(database) as connection:
                rows = connection.execute(
                    "SELECT task_key, priority, status FROM sales_tasks ORDER BY priority, account_id"
                ).fetchall()
            self.assertEqual(rows, [("B2B-001:win_back", 1, "OPEN"), ("B2B-002:upsell", 3, "OPEN")])

    def test_resync_preserves_manual_workflow_state(self) -> None:
        initial = SalesAction("B2B-001", 2, "win_back", "İlk öneri", "İlk neden")
        refreshed = SalesAction("B2B-001", 1, "win_back", "Yeni öneri", "Yeni neden")
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "sales.db"
            sync_sales_tasks(database, [initial])
            with sqlite3.connect(database) as connection:
                connection.execute(
                    """
                    UPDATE sales_tasks
                    SET status = 'IN_PROGRESS', assignee = 'enes', resolution_note = 'Arama planlandı'
                    WHERE task_key = 'B2B-001:win_back'
                    """
                )
                connection.commit()

            result = sync_sales_tasks(database, [refreshed])

            self.assertEqual((result.created, result.refreshed), (0, 1))
            with sqlite3.connect(database) as connection:
                row = connection.execute(
                    """
                    SELECT priority, recommended_action, reason, status, assignee, resolution_note
                    FROM sales_tasks WHERE task_key = 'B2B-001:win_back'
                    """
                ).fetchone()
            self.assertEqual(
                row,
                (1, "Yeni öneri", "Yeni neden", "IN_PROGRESS", "enes", "Arama planlandı"),
            )

    def test_same_account_can_have_distinct_action_types(self) -> None:
        actions = [
            SalesAction("B2B-001", 1, "win_back", "Ara", "Düşüş"),
            SalesAction("B2B-001", 3, "upsell", "Teklif", "Büyüme"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "sales.db"

            sync_sales_tasks(database, actions)

            with sqlite3.connect(database) as connection:
                count = connection.execute("SELECT COUNT(*) FROM sales_tasks").fetchone()[0]
            self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
