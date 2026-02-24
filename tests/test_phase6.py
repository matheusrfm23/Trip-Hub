import unittest
import asyncio
import os
import sqlite3
import json
from src.logic.checklist_service import ChecklistService
from src.logic.protocol_service import ProtocolService
from src.data.database import Database

class TestPhase6(unittest.TestCase):
    def setUp(self):
        Database.DB_DIR = "assets/data_test_phase6"
        Database.DB_NAME = "test_phase6.db"
        if not os.path.exists(Database.DB_DIR):
            os.makedirs(Database.DB_DIR)

        db = Database()
        db.initialize()

    def tearDown(self):
        import shutil
        if os.path.exists(Database.DB_DIR):
            shutil.rmtree(Database.DB_DIR)

    def test_services_async_compliance(self):
        async def run():
            # Checklist
            items = [{"text": "i1", "checked": False}]
            await ChecklistService.save_checklist("u1", items)
            res = await ChecklistService.get_checklist("u1")
            self.assertEqual(res[0]["text"], "i1")

            # Protocol
            await ProtocolService.mark_as_read("u1")
            status = await ProtocolService.has_read("u1")
            self.assertTrue(status)

        asyncio.run(run())

if __name__ == '__main__':
    unittest.main()
