import contextlib
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path

from turkmopet_b2b.actions import SalesAction
from turkmopet_b2b.task_cli import main
from turkmopet_b2b.tasks import sync_sales_tasks


class SalesTaskCliTests(unittest.TestCase):
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

    def test_assign_start_and_resolve_task(self) -> None:
        self.assertEqual(
            main(["--database", str(self.database), "assign", "B2B-001:win_back", "enes"]),
            0,
        )
        self.assertEqual(
            main(["--database", str(self.database), "start", "B2B-001:win_back"]),
            0,
        )
        self.assertEqual(
            main(
                [
                    "--database",
                    str(self.database),
                    "resolve",
                    "B2B-001:win_back",
                    "--note",
                    "Müşteriyle görüşüldü",
                ]
            ),
            0,
        )

        with sqlite3.connect(self.database) as connection:
            row = connection.execute(
                "SELECT status, assignee, resolution_note FROM sales_tasks WHERE task_key = ?",
                ("B2B-001:win_back",),
            ).fetchone()
        self.assertEqual(row, ("RESOLVED", "enes", "Müşteriyle görüşüldü"))

    def test_resolve_requires_non_empty_note(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main(
                [
                    "--database",
                    str(self.database),
                    "resolve",
                    "B2B-001:win_back",
                    "--note",
                    "   ",
                ]
            )
        self.assertEqual(result, 2)
        self.assertIn("resolution note cannot be empty", stderr.getvalue())

    def test_resolved_task_cannot_be_started_again(self) -> None:
        main(
            [
                "--database",
                str(self.database),
                "resolve",
                "B2B-001:win_back",
                "--note",
                "Tamamlandı",
            ]
        )
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main(["--database", str(self.database), "start", "B2B-001:win_back"])
        self.assertEqual(result, 2)
        self.assertIn("resolved task cannot be started", stderr.getvalue())

    def test_list_filters_and_writes_excel_compatible_csv(self) -> None:
        main(["--database", str(self.database), "assign", "B2B-001:win_back", "enes"])
        output = Path(self.directory.name) / "tasks.csv"

        result = main(
            [
                "--database",
                str(self.database),
                "list",
                "--status",
                "OPEN",
                "--assignee",
                "enes",
                "--output",
                str(output),
            ]
        )

        self.assertEqual(result, 0)
        self.assertTrue(output.read_bytes().startswith(b"\xef\xbb\xbf"))
        content = output.read_text(encoding="utf-8-sig")
        self.assertIn("B2B-001:win_back", content)
        self.assertNotIn("B2B-002:upsell", content)

    def test_missing_database_returns_controlled_error(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main(
                [
                    "--database",
                    str(Path(self.directory.name) / "missing.db"),
                    "list",
                ]
            )
        self.assertEqual(result, 2)
        self.assertIn("task database does not exist", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
