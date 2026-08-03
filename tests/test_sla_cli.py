import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from turkmopet_b2b.actions import SalesAction
from turkmopet_b2b.sla import overdue_tasks, task_due_at, task_sla_status
from turkmopet_b2b.sla_cli import main
from turkmopet_b2b.tasks import list_sales_tasks, sync_sales_tasks


class SalesTaskSlaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.database = Path(self.directory.name) / "sales.db"
        sync_sales_tasks(
            self.database,
            [
                SalesAction("B2B-001", 1, "win_back", "Ara", "Skor düştü"),
                SalesAction("B2B-002", 3, "upsell", "Teklif hazırla", "Skor yükseldi"),
            ],
        )

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_priority_one_task_is_overdue_after_24_hours(self) -> None:
        task = list_sales_tasks(self.database)[0]
        now = datetime.fromisoformat(task.created_at) + timedelta(hours=25)
        self.assertEqual(task_sla_status(task, now=now), "OVERDUE")
        self.assertEqual(task_due_at(task), datetime.fromisoformat(task.created_at) + timedelta(hours=24))

    def test_resolved_task_is_never_reported_overdue(self) -> None:
        with sqlite3.connect(self.database) as connection:
            connection.execute(
                "UPDATE sales_tasks SET status = 'RESOLVED', created_at = ? WHERE task_key = ?",
                ((datetime.now(UTC) - timedelta(days=10)).isoformat(), "B2B-001:win_back"),
            )
            connection.commit()
        tasks = list_sales_tasks(self.database)
        self.assertEqual(overdue_tasks(tasks), [])

    def test_cli_exports_only_overdue_tasks_and_returns_warning_code(self) -> None:
        old = (datetime.now(UTC) - timedelta(days=8)).isoformat()
        with sqlite3.connect(self.database) as connection:
            connection.execute("UPDATE sales_tasks SET created_at = ?", (old,))
            connection.commit()
        output = Path(self.directory.name) / "overdue.csv"
        result = main(["--database", str(self.database), "--output", str(output)])
        self.assertEqual(result, 1)
        self.assertTrue(output.read_bytes().startswith(b"\xef\xbb\xbf"))
        content = output.read_text(encoding="utf-8-sig")
        self.assertIn("B2B-001:win_back", content)
        self.assertIn("B2B-002:upsell", content)
        self.assertIn("due_at", content)


if __name__ == "__main__":
    unittest.main()
