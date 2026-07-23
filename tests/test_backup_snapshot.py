import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.verify_backup_restore import sha256, snapshot_sqlite


class BackupSnapshotTests(unittest.TestCase):
    def test_sqlite_snapshot_is_consistent(self):
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            source = temp / "source.db"
            snapshot = temp / "snapshot.db"

            connection = sqlite3.connect(source)
            connection.execute(
                "CREATE TABLE example (id INTEGER PRIMARY KEY, value TEXT)"
            )
            connection.execute(
                "INSERT INTO example(value) VALUES (?)",
                ("test",),
            )
            connection.commit()
            connection.close()

            snapshot_sqlite(source, snapshot)

            restored = sqlite3.connect(snapshot)
            count = restored.execute(
                "SELECT COUNT(*) FROM example"
            ).fetchone()[0]
            restored.close()

            self.assertEqual(count, 1)
            self.assertTrue(snapshot.is_file())
            self.assertTrue(sha256(snapshot))


if __name__ == "__main__":
    unittest.main()
