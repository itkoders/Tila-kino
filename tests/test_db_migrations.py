import os
import sqlite3
import tempfile
import unittest

import db


class DatabaseMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "legacy.sqlite3")
        conn = sqlite3.connect(self.db_path)
        # Sxema avvalgi versiyadan: joined_at va bir nechta yangi ustunlar yo'q.
        conn.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, first_name TEXT, created_at BIGINT)"
        )
        conn.execute(
            "INSERT INTO users(id, first_name, created_at) VALUES(123, 'Legacy', 1700000000)"
        )
        conn.execute(
            "CREATE TABLE movies (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, title TEXT, created_at BIGINT)"
        )
        conn.commit()
        conn.close()
        db.init("sqlite:///" + self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_legacy_schema_migrates_and_preserves_data(self):
        db.init_schema()
        user = db.one("SELECT * FROM users WHERE id=?", (123,))
        movie_cols = {r["name"] for r in db.q("PRAGMA table_info(movies)")}
        self.assertEqual(user["first_name"], "Legacy")
        self.assertEqual(user["joined_at"], 1700000000)
        self.assertEqual(user["created_at"], 1700000000)
        self.assertIn("kind", movie_cols)
        self.assertIn("published", movie_cols)
        self.assertIn("created_at", movie_cols)

    def test_migration_is_idempotent(self):
        db.init_schema()
        db.init_schema()
        self.assertEqual(db.one("SELECT COUNT(*) AS c FROM users")["c"], 1)
        self.assertEqual(db.one("SELECT value FROM settings WHERE key='schema_version'")["value"], str(db.SCHEMA_VERSION))


if __name__ == "__main__":
    unittest.main()
