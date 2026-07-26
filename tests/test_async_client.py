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
async def test_async_get_daily_counts(sample_html):
    """Test public API: async get_daily_counts."""
    async with AsyncOryxScraper() as scraper:
        # Mock at the IO boundary so the real parsing path is exercised.
        with patch.object(scraper, "_fetch_page", AsyncMock(return_value=sample_html)):
            daily_counts = await scraper.get_daily_counts(countries=["russia"])

        assert {row["country"] for row in daily_counts} == {"russia"}

        t62m = next(row for row in daily_counts if row["equipment_type"] == "T-62M")
        assert t62m["destroyed"] == 2
        assert t62m["captured"] == 1
        assert t62m["type_total"] == 3


@pytest.mark.asyncio
async def test_async_get_totals_by_type(sample_html):
    """Test public API: async get_totals_by_type."""
    async with AsyncOryxScraper() as scraper:
        with patch.object(scraper, "_fetch_page", AsyncMock(return_value=sample_html)):
            totals = await scraper.get_totals_by_type(countries=["russia"])

        t62m = next(row for row in totals if row["type"] == "T-62M")
        assert t62m["country"] == "russia"
        assert t62m["destroyed"] == 2
        assert t62m["total"] == 3


@pytest.mark.asyncio
async def test_async_get_category_totals(sample_html):
    """Async client must produce the same category aggregates as the sync one."""
    async with AsyncOryxScraper() as scraper:
        with patch.object(scraper, "_fetch_page", AsyncMock(return_value=sample_html)):
            totals = await scraper.get_category_totals()

    by_key = {(row["country"], row["category"]): row for row in totals}
    assert by_key[("russia", "Tanks")]["total"] == 4
    assert by_key[("ukraine", "Tanks")]["abandoned"] == 1


@pytest.mark.asyncio
async def test_async_get_system_entries(sample_html):
    """Async client must produce system-level entries too."""
    async with AsyncOryxScraper() as scraper:
        with patch.object(scraper, "_fetch_page", AsyncMock(return_value=sample_html)):
            systems = await scraper.get_system_entries(countries=["russia"])

    assert {s.system for s in systems} == {"T-62M", "T-54-3M", "Su-34"}
    assert all(s.origin == "" for s in systems)
