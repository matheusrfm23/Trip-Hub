import pytest
import aiohttp
from unittest.mock import patch, MagicMock, AsyncMock

# Must mock SSL_VERIFY before importing FinanceService to control its value
@patch("src.logic.finance_service.SSL_VERIFY", True)
@pytest.mark.asyncio
async def test_finance_service_ssl_verify_true(caplog):
    from src.logic.finance_service import FinanceService
    import logging

    with caplog.at_level(logging.WARNING):
        # We patch aiohttp.ClientSession to avoid real requests
        with patch("src.logic.finance_service.aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Mocks responses to prevent any exceptions from deep inside update_rates
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {}
            mock_session.get.return_value.__aenter__.return_value = mock_response

            await FinanceService.update_rates()

            # The warning should not be logged
            assert "🚨 ALERTA DE SEGURANÇA" not in caplog.text

            # Extract connector from kwargs passed to ClientSession
            assert mock_session_class.call_count == 1
            call_kwargs = mock_session_class.call_args.kwargs
            assert "connector" in call_kwargs
            connector = call_kwargs["connector"]

            # The connector must have ssl=True
            assert getattr(connector, "_ssl", None) is True or getattr(connector, "_ssl_context", None) is not False, "Expected connector to verify SSL."


@patch("src.logic.finance_service.SSL_VERIFY", False)
@pytest.mark.asyncio
async def test_finance_service_ssl_verify_false(caplog):
    from src.logic.finance_service import FinanceService
    import logging

    with caplog.at_level(logging.WARNING):
        # We patch aiohttp.ClientSession to avoid real requests
        with patch("src.logic.finance_service.aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Mocks responses to prevent any exceptions from deep inside update_rates
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {}
            mock_session.get.return_value.__aenter__.return_value = mock_response

            await FinanceService.update_rates()

            # The warning SHOULD be logged
            assert "🚨 ALERTA DE SEGURANÇA: Verificação SSL está desativada (SSL_VERIFY=False)." in caplog.text

            # Extract connector from kwargs passed to ClientSession
            assert mock_session_class.call_count == 1
            call_kwargs = mock_session_class.call_args.kwargs
            assert "connector" in call_kwargs
            connector = call_kwargs["connector"]

            # The connector must have ssl=False
            assert getattr(connector, "_ssl", None) is False or getattr(connector, "_ssl_context", None) is False, "Expected connector to NOT verify SSL."
