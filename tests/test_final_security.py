import unittest
import asyncio
import os
import sqlite3
import json
from src.logic.auth_service import AuthService
from src.data.database import Database

class TestFinalSecurity(unittest.TestCase):
    def setUp(self):
        Database.DB_DIR = "assets/data_test_final_sec"
        Database.DB_NAME = "test_final_sec.db"
        if not os.path.exists(Database.DB_DIR):
            os.makedirs(Database.DB_DIR)
        db = Database()
        db.initialize()

    def tearDown(self):
        import shutil
        if os.path.exists(Database.DB_DIR):
            shutil.rmtree(Database.DB_DIR)

    def test_delete_profile(self):
        async def run():
            # Create
            await AuthService.create_profile("User", "1234")
            profiles = await AuthService.get_profiles()
            uid = profiles[0]["id"]

            # Delete
            await AuthService.delete_profile(uid)

            # Verify gone
            profiles = await AuthService.get_profiles()
            self.assertEqual(len(profiles), 0)

        asyncio.run(run())

if __name__ == '__main__':
    unittest.main()
