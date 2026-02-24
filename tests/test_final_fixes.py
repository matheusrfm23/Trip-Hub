import unittest
import asyncio
import os
import sqlite3
import json
from src.logic.place_service import PlaceService
from src.data.database import Database

class TestFinalFixes(unittest.TestCase):
    def setUp(self):
        Database.DB_DIR = "assets/data_test_final"
        Database.DB_NAME = "test_final.db"
        if not os.path.exists(Database.DB_DIR):
            os.makedirs(Database.DB_DIR)
        db = Database()
        db.initialize()

    def tearDown(self):
        import shutil
        if os.path.exists(Database.DB_DIR):
            shutil.rmtree(Database.DB_DIR)

    def test_place_flattening(self):
        async def run():
            # Add place with extra data
            data = {
                "country": "br", "category": "hotel", "name": "H1",
                "price": "100", "wifi": True, "pool": False
            }
            await PlaceService.add_place(data)

            # Retrieve
            places = await PlaceService.get_places("br", "hotel")
            p = places[0]

            # Verify flattening
            self.assertEqual(p["price"], "100")
            self.assertTrue(p["wifi"])
            self.assertFalse(p["pool"])
            self.assertNotIn("extra_data", p) # Should be removed

        asyncio.run(run())

if __name__ == '__main__':
    unittest.main()
