import unittest
import asyncio
import os
import sqlite3
import json
from src.logic.auth_service import AuthService
from src.data.database import Database

class TestAuthServiceSQLite(unittest.TestCase):
    def setUp(self):
        # Setup temporary DB
        Database.DB_DIR = "assets/data_test_auth"
        Database.DB_NAME = "test_auth.db"
        if not os.path.exists(Database.DB_DIR):
            os.makedirs(Database.DB_DIR)

        db = Database()
        db.initialize()

    def tearDown(self):
        import shutil
        if os.path.exists(Database.DB_DIR):
            shutil.rmtree(Database.DB_DIR)

    def test_create_and_login(self):
        async def run_test():
            # Create
            success = await AuthService.create_profile("Test User", "1234")
            self.assertTrue(success)

            # Login
            profiles = await AuthService.get_profiles()
            self.assertEqual(len(profiles), 1)
            user_id = profiles[0]["id"]

            user = await AuthService.login(user_id, "1234")
            self.assertIsNotNone(user)
            self.assertEqual(user["name"], "Test User")

            # Verify JSON fields
            self.assertTrue(isinstance(user["privacy"], dict))
            self.assertTrue(user["privacy"]["medical"])

            # Update
            await AuthService.update_profile_general(user_id, {"name": "Updated User", "privacy": {"medical": False}})
            user = await AuthService.get_user_by_id(user_id)
            self.assertEqual(user["name"], "Updated User")
            self.assertFalse(user["privacy"]["medical"])

            # Delete
            await AuthService.delete_profile(user_id)
            user = await AuthService.get_user_by_id(user_id)
            self.assertIsNone(user)

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
