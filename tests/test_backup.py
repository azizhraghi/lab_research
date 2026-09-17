from pathlib import Path
import sqlite3
import tempfile
import unittest
from scripts.backup_sqlite import snapshot
from contextlib import closing

class BackupTests(unittest.TestCase):
    def test_snapshot_restore_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.db';backup=Path(folder)/'backup.db';restored=Path(folder)/'restored.db'
            with closing(sqlite3.connect(source)) as db:
                db.execute('CREATE TABLE evidence (id INTEGER PRIMARY KEY, body TEXT)')
                db.execute('INSERT INTO evidence VALUES (?,?)',(1,'Unicode evidence: qualité'))
                db.commit()
            report=snapshot(source,backup)
            self.assertEqual(report['table_counts'],{'evidence':1})
            snapshot(backup,restored)
            with closing(sqlite3.connect(restored)) as db:
                self.assertEqual(db.execute('SELECT body FROM evidence').fetchone()[0],'Unicode evidence: qualité')
            with self.assertRaises(FileExistsError):snapshot(source,backup)
            with self.assertRaises(ValueError):snapshot(source,source)
