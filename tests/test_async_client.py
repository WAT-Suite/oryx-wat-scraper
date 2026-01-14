"""Tests for the AsyncOryxScraper client."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from oryx_wat_scraper import AsyncOryxScraper
from oryx_wat_scraper.exceptions import OryxScraperNetworkError
from oryx_wat_scraper.models import EquipmentEntry


@pytest.mark.asyncio
async def test_async_scraper_initialization():
    """Test async scraper initialization."""
    async with AsyncOryxScraper(timeout=10.0) as scraper:
        assert scraper.timeout == 10.0
        assert (
            scraper.BASE_URL
            == "https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html"
        )


@pytest.mark.asyncio
async def test_async_scraper_context_manager():
    """Test async scraper as context manager."""
    async with AsyncOryxScraper() as scraper:
        assert scraper is not None
        assert scraper._client is not None
    # Should be closed after context exit
    assert scraper._client is None or scraper._client.is_closed


@pytest.mark.asyncio
@patch("oryx_wat_scraper.async_client.httpx.AsyncClient")
async def test_async_fetch_page_success(mock_client_class):
    """Test successful async page fetch."""
    mock_response = Mock()
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.is_closed = False
    mock_client.aclose = AsyncMock()
    mock_client_class.return_value = mock_client

    async with AsyncOryxScraper() as scraper:
        html = await scraper._fetch_page()

        assert html == "<html><body>Test</body></html>"
        mock_client.get.assert_called_once_with(scraper.BASE_URL)


@pytest.mark.asyncio
@patch("oryx_wat_scraper.async_client.httpx.AsyncClient")
async def test_async_fetch_page_network_error(mock_client_class):
    """Test async network error handling."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=Exception("Network error"))
    mock_client.is_closed = False
    mock_client.aclose = AsyncMock()
    mock_client_class.return_value = mock_client

    async with AsyncOryxScraper() as scraper:
        with pytest.raises(OryxScraperNetworkError):
            await scraper._fetch_page()


@pytest.mark.asyncio
async def test_async_get_equipment_data():
    """Test public API: async get_equipment_data."""
    async with AsyncOryxScraper() as scraper:
        # Mock the internal method
        with patch.object(scraper, "_scrape_equipment_entries") as mock_scrape:
            mock_scrape.return_value = [
                EquipmentEntry("russia", "T-62M", "destroyed"),
                EquipmentEntry("russia", "T-72", "captured"),
            ]

            entries = await scraper.get_equipment_data(country="russia")

            assert len(entries) == 2
            assert entries[0].equipment_type == "T-62M"
            mock_scrape.assert_called_once_with("russia")


@pytest.mark.asyncio
async def test_async_get_daily_counts():
    """Test public API: async get_daily_counts."""
    async with AsyncOryxScraper() as scraper:
        # Mock the internal method
        with patch.object(scraper, "_scrape_equipment_entries") as mock_scrape:
            mock_scrape.return_value = [
                EquipmentEntry("russia", "T-62M", "destroyed", date_recorded="2024-01-15"),
                EquipmentEntry("russia", "T-62M", "destroyed", date_recorded="2024-01-15"),
            ]

            daily_counts = await scraper.get_daily_counts(countries=["russia"])

            assert len(daily_counts) == 1
            assert daily_counts[0]["country"] == "russia"
            assert daily_counts[0]["equipment_type"] == "T-62M"
            assert daily_counts[0]["destroyed"] == 2


@pytest.mark.asyncio
async def test_async_get_totals_by_type():
    """Test public API: async get_totals_by_type."""
    async with AsyncOryxScraper() as scraper:
        # Mock the internal method
        with patch.object(scraper, "_scrape_equipment_entries") as mock_scrape:
            mock_scrape.return_value = [
                EquipmentEntry("russia", "T-62M", "destroyed"),
                EquipmentEntry("russia", "T-62M", "destroyed"),
            ]

            totals = await scraper.get_totals_by_type(countries=["russia"])

            assert len(totals) == 1
            assert totals[0]["country"] == "russia"
            assert totals[0]["type"] == "T-62M"
            assert totals[0]["destroyed"] == 2
            assert totals[0]["total"] == 2
