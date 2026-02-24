import unittest
import asyncio
import os
import sqlite3
import json
from src.logic.place_service import PlaceService
from src.data.database import Database

class TestPhase8(unittest.TestCase):
    def setUp(self):
        Database.DB_DIR = "assets/data_test_phase8"
        Database.DB_NAME = "test_phase8.db"
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
            data = {"country": "br", "category": "test", "name": "Place", "extra": "123", "price": "10"}
            await PlaceService.add_place(data)

            places = await PlaceService.get_places("br", "test")
            p = places[0]
            self.assertEqual(p["extra"], "123")
            self.assertEqual(p["price"], "10")

        asyncio.run(run())

if __name__ == '__main__':
    unittest.main()
