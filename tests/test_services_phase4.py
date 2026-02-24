import unittest
import asyncio
import os
import sqlite3
import json
from src.logic.flight_service import FlightService
from src.logic.notification_service import NotificationService
from src.data.database import Database

class TestServicesPhase4(unittest.TestCase):
    def setUp(self):
        Database.DB_DIR = "assets/data_test_phase4"
        Database.DB_NAME = "test_phase4.db"
        if not os.path.exists(Database.DB_DIR):
            os.makedirs(Database.DB_DIR)

        db = Database()
        db.initialize()

    def tearDown(self):
        import shutil
        if os.path.exists(Database.DB_DIR):
            shutil.rmtree(Database.DB_DIR)

    def test_flight_crud(self):
        async def run():
            # Add
            f = {"locator": "ABC", "user_id": "u1", "passenger": "P1", "gate": "10"}
            await FlightService.add_flight(f)

            # Get
            flights = await FlightService.get_flights()
            self.assertEqual(len(flights), 1)
            self.assertEqual(flights[0]["gate"], "10") # Check JSON detail
            fid = flights[0]["id"]

            # Update
            await FlightService.update_flight(fid, {"gate": "12"})
            flights = await FlightService.get_flights()
            self.assertEqual(flights[0]["gate"], "12")

            # Delete
            await FlightService.delete_flight(fid)
            flights = await FlightService.get_flights()
            self.assertEqual(len(flights), 0)

        asyncio.run(run())

    def test_notification_crud(self):
        async def run():
            # Send
            await NotificationService.send_notification("System", "u1", "Title", "Msg")

            # Get
            notifs = await NotificationService.get_notifications("u1")
            self.assertEqual(len(notifs), 1)
            nid = notifs[0]["id"]

            # Mark Read
            await NotificationService.mark_as_read(nid, "u1")
            notifs = await NotificationService.get_notifications("u1")
            self.assertIn("u1", notifs[0]["read_by"])

            # Delete
            await NotificationService.delete_notification(nid)
            notifs = await NotificationService.get_notifications("u1")
            self.assertEqual(len(notifs), 0)

        asyncio.run(run())

if __name__ == '__main__':
    unittest.main()
