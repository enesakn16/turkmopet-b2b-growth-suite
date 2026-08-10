import sqlite3
import tempfile
import unittest
from pathlib import Path

from turkmopet_b2b.actions import SalesAction
from turkmopet_b2b.tasks import start_sales_task, sync_sales_tasks


class SalesTaskStartTransitionTests(unittest.TestCase):
    def test_start_is_single_open_to_in_progress_transition(self) -> None:
        action = SalesAction("B2B-001", 1, "win_back", "Ara", "Skor düştü")
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "sales.db"
            sync_sales_tasks(database, [action])

            started = start_sales_task(database, "B2B-001:win_back")
            first_updated_at = started.updated_at

            with self.assertRaisesRegex(ValueError, "only be started from OPEN"):
                start_sales_task(database, "B2B-001:win_back")

            with sqlite3.connect(database) as connection:
                row = connection.execute(
                    "SELECT status, updated_at FROM sales_tasks WHERE task_key = ?",
                    ("B2B-001:win_back",),
                ).fetchone()

            self.assertEqual(row, ("IN_PROGRESS", first_updated_at))


if __name__ == "__main__":
    unittest.main()
