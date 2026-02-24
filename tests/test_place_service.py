import unittest
import asyncio
import os
import sqlite3
import json
from src.logic.place_service import PlaceService
from src.data.database import Database

class TestPlaceServiceSQLite(unittest.TestCase):
    def setUp(self):
        Database.DB_DIR = "assets/data_test_place"
        Database.DB_NAME = "test_place.db"
        if not os.path.exists(Database.DB_DIR):
            os.makedirs(Database.DB_DIR)

        db = Database()
        db.initialize()

    def tearDown(self):
        import shutil
        if os.path.exists(Database.DB_DIR):
            shutil.rmtree(Database.DB_DIR)

    def test_crud_places(self):
        async def run_test():
            # Add
            new_place = {
                "country": "br", "category": "hotel", "name": "Hotel Test",
                "description": "Desc", "lat": -23.0, "lon": -46.0,
                "maps_link": "http://maps", "added_by": "tester"
            }
            success = await PlaceService.add_place(new_place)
            self.assertTrue(success)

            # Read
            places = await PlaceService.get_places("br", "hotel")
            self.assertEqual(len(places), 1)
            self.assertEqual(places[0]["name"], "Hotel Test")
            place_id = places[0]["id"]

            # Update
            await PlaceService.update_place(place_id, {"description": "New Desc"})
            places = await PlaceService.get_places("br", "hotel")
            self.assertEqual(places[0]["description"], "New Desc")

            # Toggle Vote
            await PlaceService.toggle_vote(place_id, "br", "hotel", "user1")
            places = await PlaceService.get_places("br", "hotel")
            self.assertIn("user1", places[0]["votes"])

            await PlaceService.toggle_vote(place_id, "br", "hotel", "user1")
            places = await PlaceService.get_places("br", "hotel")
            self.assertNotIn("user1", places[0]["votes"])

            # Delete
            await PlaceService.delete_place(place_id, "br", "hotel")
            places = await PlaceService.get_places("br", "hotel")
            self.assertEqual(len(places), 0)

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
