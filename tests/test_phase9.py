import unittest
import asyncio
import os
import sqlite3
import json
from src.logic.place_service import PlaceService
from src.data.database import Database

class TestPhase9(unittest.TestCase):
    def setUp(self):
        Database.DB_DIR = "assets/data_test_phase9"
        Database.DB_NAME = "test_phase9.db"
        if not os.path.exists(Database.DB_DIR):
            os.makedirs(Database.DB_DIR)
        db = Database()
        db.initialize()

    def tearDown(self):
        import shutil
        if os.path.exists(Database.DB_DIR):
            shutil.rmtree(Database.DB_DIR)

    def test_extra_data_flattening(self):
        async def run():
            # Add place with nested extra data
            data = {"country": "br", "category": "test", "name": "Place", "price": "99", "wifi": True}
            await PlaceService.add_place(data)

            # Retrieve
            places = await PlaceService.get_places("br", "test")
            p = places[0]

            # Check if fields are at root level
            self.assertEqual(p["price"], "99")
            self.assertEqual(p["wifi"], True)
            self.assertNotIn("extra_data", p)

        asyncio.run(run())

if __name__ == '__main__':
    unittest.main()
