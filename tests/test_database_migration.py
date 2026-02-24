import unittest
import os
import json
import sqlite3
import shutil
from src.data.database import Database

class TestDatabaseMigration(unittest.TestCase):
    TEST_DB_DIR = "assets/data_test"

    def setUp(self):
        # Setup temporary directory for test
        self.original_db_dir = Database.DB_DIR
        Database.DB_DIR = self.TEST_DB_DIR
        Database.DB_NAME = "test_triphub.db"

        if os.path.exists(self.TEST_DB_DIR):
            shutil.rmtree(self.TEST_DB_DIR)
        os.makedirs(self.TEST_DB_DIR)

    def tearDown(self):
        # Cleanup
        if os.path.exists(self.TEST_DB_DIR):
            shutil.rmtree(self.TEST_DB_DIR)
        Database.DB_DIR = self.original_db_dir
        Database.DB_NAME = "triphub.db"

    def test_migration_users(self):
        # Create dummy profiles.json
        users = [{
            "id": "u1", "name": "User 1", "role": "USER", "pin": "1234",
            "privacy": {"medical": True}, "contact": {}, "medical": {},
            "last_location": {"lat": 0, "lon": 0}
        }]
        with open(os.path.join(self.TEST_DB_DIR, "profiles.json"), "w") as f:
            json.dump(users, f)

        # Run initialization
        Database.initialize()

        # Check SQLite
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id='u1'")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "User 1")
        self.assertEqual(row["privacy"], '{"medical": true}')

        # Check file renamed
        self.assertFalse(os.path.exists(os.path.join(self.TEST_DB_DIR, "profiles.json")))
        self.assertTrue(os.path.exists(os.path.join(self.TEST_DB_DIR, "profiles.json.bak")))

    def test_migration_banner(self):
        # Create dummy banner_config.json
        config = {"mode": "manual", "theme": "Dark", "alert_target": 5.5}
        with open(os.path.join(self.TEST_DB_DIR, "banner_config.json"), "w") as f:
            json.dump(config, f)

        Database.initialize()

        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM banner_config")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["mode"], "manual")
        self.assertEqual(row["alert_target"], 5.5)

    def test_migration_checklists(self):
        # Create dummy checklists.json
        data = {"u1": [{"text": "Item 1", "checked": False}]}
        with open(os.path.join(self.TEST_DB_DIR, "checklists.json"), "w") as f:
            json.dump(data, f)

        Database.initialize()

        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM checklists WHERE user_id='u1'")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertIn("Item 1", row["items"])

if __name__ == '__main__':
    unittest.main()
