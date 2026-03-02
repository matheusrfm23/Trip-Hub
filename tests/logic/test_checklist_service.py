import pytest
import os
import json
from unittest.mock import patch, mock_open
from src.logic.checklist_service import ChecklistService, logger

class TestChecklistService:

    def setup_method(self):
        # We backup the original filepath to restore later
        self.original_file_path = ChecklistService.FILE_PATH
        ChecklistService.FILE_PATH = "test_checklists.json"

    def teardown_method(self):
        # Clean up any test file that was created
        if os.path.exists(ChecklistService.FILE_PATH):
            os.remove(ChecklistService.FILE_PATH)
        ChecklistService.FILE_PATH = self.original_file_path

    @patch('src.logic.checklist_service.ChecklistService._ensure_file_exists')
    def test_get_checklist_file_not_found(self, mock_ensure):
        """
        Scenario 1: File does not exist.
        Should return [] without error in the log.
        We mock _ensure_file_exists so it doesn't create the file, triggering FileNotFoundError.
        """
        # Ensure the file doesn't exist
        if os.path.exists(ChecklistService.FILE_PATH):
            os.remove(ChecklistService.FILE_PATH)

        result = ChecklistService.get_checklist("123")
        assert result == []

    @patch('src.logic.checklist_service.logger.critical')
    def test_get_checklist_invalid_json(self, mock_logger_critical):
        """
        Scenario 2: File contains invalid JSON.
        Should return [] and generate a critical log entry.
        """
        # Create a file with invalid JSON
        with open(ChecklistService.FILE_PATH, "w") as f:
            f.write("{ invalid json")

        result = ChecklistService.get_checklist("123")

        # Verify it returns []
        assert result == []

        # Verify the critical log was called
        mock_logger_critical.assert_called_once()
        args = mock_logger_critical.call_args[0][0]
        assert "Arquivo de checklist corrompido:" in args
