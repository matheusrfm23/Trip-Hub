import sys
from unittest.mock import MagicMock

# Mock dependencies that are not installed or cause issues in the test environment
mock_flet = MagicMock()
mock_aiohttp = MagicMock()
sys.modules["flet"] = mock_flet
sys.modules["aiohttp"] = mock_aiohttp

import pytest
from src.core.utils import format_size

def test_format_size_bytes():
    assert format_size(500) == "500.0 B"
    assert format_size(1023) == "1023.0 B"

def test_format_size_kilobytes():
    assert format_size(1024) == "1.0 KB"
    assert format_size(1024 * 1.5) == "1.5 KB"
    # 1024**2 - 1 = 1048575
    # 1048575 / 1024 = 1023.9990234375
    # format_size will return "1024.0 KB" due to .1f formatting
    assert format_size(1024**2 - 1) == "1024.0 KB"

def test_format_size_megabytes():
    assert format_size(1024**2) == "1.0 MB"
    assert format_size(1024**2 * 5.5) == "5.5 MB"

def test_format_size_gigabytes():
    assert format_size(1024**3) == "1.0 GB"
    assert format_size(1024**3 * 2.2) == "2.2 GB"

def test_format_size_terabytes():
    assert format_size(1024**4) == "1.0 TB"
    assert format_size(1024**4 * 10) == "10.0 TB"

def test_format_size_zero():
    assert format_size(0) == "0.0 B"

def test_format_size_boundary():
    # Exactly 1023.9 should stay in B
    assert format_size(1023.9) == "1023.9 B"
    # Exactly 1024 should go to KB
    assert format_size(1024) == "1.0 KB"
