import unittest
import asyncio
import os
import sqlite3
import json
from src.logic.checklist_service import ChecklistService
from src.logic.protocol_service import ProtocolService
from src.logic.chat_service import ChatService
from src.data.database import Database

class TestServicesPhase5(unittest.TestCase):
    def setUp(self):
        Database.DB_DIR = "assets/data_test_phase5"
        Database.DB_NAME = "test_phase5.db"
        if not os.path.exists(Database.DB_DIR):
            os.makedirs(Database.DB_DIR)

        db = Database()
        db.initialize()

    def tearDown(self):
        import shutil
        if os.path.exists(Database.DB_DIR):
            shutil.rmtree(Database.DB_DIR)

    def test_checklist(self):
        async def run():
            items = [{"text": "Item 1", "checked": True}]
            await ChecklistService.save_checklist("u1", items)

            loaded = await ChecklistService.get_checklist("u1")
            self.assertEqual(len(loaded), 1)
            self.assertTrue(loaded[0]["checked"])

            await ChecklistService.reset_checks("u1")
            loaded = await ChecklistService.get_checklist("u1")
            self.assertFalse(loaded[0]["checked"])
        asyncio.run(run())

    def test_protocol(self):
        async def run():
            self.assertFalse(await ProtocolService.has_read("u1"))
            await ProtocolService.mark_as_read("u1")
            self.assertTrue(await ProtocolService.has_read("u1"))
        asyncio.run(run())

    def test_chat(self):
        async def run():
            await ChatService.send_message("u1", "u2", "Hello")
            msgs = await ChatService.get_conversation("u1", "u2")
            self.assertEqual(len(msgs), 1)
            self.assertEqual(msgs[0]["content"], "Hello")

            unread = await ChatService.get_unread_from("u2", "u1")
            self.assertEqual(unread, 1)

            await ChatService.mark_conversation_as_read("u2", "u1")
            unread = await ChatService.get_unread_from("u2", "u1")
            self.assertEqual(unread, 0)
        asyncio.run(run())

if __name__ == '__main__':
    unittest.main()
