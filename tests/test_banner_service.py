import unittest
import asyncio
import os
import sqlite3
import json
from src.logic.banner_service import BannerService
from src.data.database import Database

class TestBannerServiceSQLite(unittest.TestCase):
    def setUp(self):
        Database.DB_DIR = "assets/data_test_banner"
        Database.DB_NAME = "test_banner.db"
        if not os.path.exists(Database.DB_DIR):
            os.makedirs(Database.DB_DIR)

        db = Database()
        db.initialize()

    def tearDown(self):
        import shutil
        if os.path.exists(Database.DB_DIR):
            shutil.rmtree(Database.DB_DIR)

    def test_get_and_save_config(self):
        async def run():
            # Initial config (default)
            cfg = await BannerService.get_config()
            self.assertEqual(cfg["mode"], "auto")

            # Save new config
            new_cfg = {"mode": "manual", "manual_text": "TEST"}
            await BannerService.save_config(new_cfg)

            # Verify persistence
            loaded_cfg = await BannerService.get_config()
            self.assertEqual(loaded_cfg["mode"], "manual")
            self.assertEqual(loaded_cfg["manual_text"], "TEST")
            self.assertTrue(isinstance(loaded_cfg["target_location"], dict)) # Check JSON

        asyncio.run(run())

    def test_schedule_check(self):
        async def run():
            # Mock schedule data directly in DB
            conn = Database.get_connection()
            conn.execute("CREATE TABLE IF NOT EXISTS schedule (id TEXT, title TEXT, start TEXT, end TEXT, description TEXT, type TEXT)")

            # Add an active event
            from datetime import datetime, timedelta
            now = datetime.now()
            start = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
            end = (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")

            conn.execute("INSERT INTO schedule VALUES (?, ?, ?, ?, ?, ?)", ("1", "Event", start, end, "Desc", "type"))
            conn.commit()
            conn.close()

            # Check service detection
            # Note: _check_schedule is internal, but get_oracle_data calls it.
            # We can test _check_schedule directly since it is a class method.
            event = await BannerService._check_schedule()
            self.assertIsNotNone(event)
            self.assertEqual(event["title"], "Event")

        asyncio.run(run())

if __name__ == '__main__':
    unittest.main()
