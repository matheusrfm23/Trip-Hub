import pytest
import asyncio
from unittest.mock import patch, MagicMock
import aiohttp

# Patching config.SSL_VERIFY BEFORE importing FinanceService
import sys

def mock_get_response():
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = MagicMock()
    mock_resp.__aenter__.return_value = mock_resp
    return mock_resp

@pytest.fixture(autouse=True)
def clean_sys_modules():
    """Fixture to ensure clean sys.modules for each test and after tests."""
    if "src.logic.finance_service" in sys.modules:
        del sys.modules["src.logic.finance_service"]
    yield
    if "src.logic.finance_service" in sys.modules:
        del sys.modules["src.logic.finance_service"]

@patch("src.core.config.SSL_VERIFY", True)
def test_finance_service_ssl_verify_true():
    from src.logic.finance_service import FinanceService

    with patch("aiohttp.TCPConnector") as mock_tcp_connector, \
         patch("aiohttp.ClientSession") as mock_client_session:

        # Setup mock session to return an async context manager
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_session_instance.get.return_value = mock_get_response()
        mock_client_session.return_value = mock_session_instance

        # Run the async method
        asyncio.run(FinanceService.update_rates())

        # Verify TCPConnector was called with ssl=True
        mock_tcp_connector.assert_called_once_with(ssl=True)


@patch("src.core.config.SSL_VERIFY", False)
def test_finance_service_ssl_verify_false():
    from src.logic.finance_service import FinanceService

    with patch("aiohttp.TCPConnector") as mock_tcp_connector, \
         patch("aiohttp.ClientSession") as mock_client_session:

        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_session_instance.get.return_value = mock_get_response()
        mock_client_session.return_value = mock_session_instance

        asyncio.run(FinanceService.update_rates())

        mock_tcp_connector.assert_called_once_with(ssl=False)
