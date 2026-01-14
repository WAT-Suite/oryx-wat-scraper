"""Tests for the OryxScraper client."""

from unittest.mock import Mock, patch

import pytest

from oryx_wat_scraper import OryxScraper
from oryx_wat_scraper.exceptions import OryxScraperNetworkError


def test_scraper_initialization():
    """Test scraper initialization."""
    scraper = OryxScraper(timeout=10.0)
    assert scraper.timeout == 10.0
    assert (
        scraper.BASE_URL
        == "https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html"
    )
    scraper.close()


def test_scraper_context_manager():
    """Test scraper as context manager."""
    with OryxScraper() as scraper:
        assert scraper is not None
    # Should be closed after context exit
    assert scraper.client.is_closed


@patch("oryx_wat_scraper.client.httpx.Client")
def test_fetch_page_success(mock_client_class):
    """Test successful page fetch (internal method)."""
    mock_response = Mock()
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.raise_for_status = Mock()

    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_client.is_closed = False
    mock_client_class.return_value = mock_client

    scraper = OryxScraper()
    html = scraper._fetch_page()

    assert html == "<html><body>Test</body></html>"
    mock_client.get.assert_called_once_with(scraper.BASE_URL)
    scraper.close()


@patch("oryx_wat_scraper.client.httpx.Client")
def test_fetch_page_network_error(mock_client_class):
    """Test network error handling (internal method)."""
    mock_client = Mock()
    mock_client.get.side_effect = Exception("Network error")
    mock_client.is_closed = False
    mock_client_class.return_value = mock_client

    scraper = OryxScraper()

    with pytest.raises(OryxScraperNetworkError):
        scraper._fetch_page()

    scraper.close()


def test_parse_equipment_line():
    """Test equipment line parsing (internal method)."""
    scraper = OryxScraper()

    # Test with HTML links
    html_line = '154 T-62M: <a href="https://example.com/1">(1, destroyed)</a> <a href="https://example.com/2">(2, captured)</a>'
    entries = scraper._parse_equipment_line(
        "154 T-62M: (1, destroyed) (2, captured)", "russia", "Tanks", html_line
    )

    assert len(entries) == 2
    assert entries[0].equipment_type == "T-62M"
    assert entries[0].status == "destroyed"
    assert entries[1].status == "captured"

    scraper.close()


def test_generate_daily_count_csv():
    """Test daily count CSV generation (internal method)."""
    from oryx_wat_scraper.models import EquipmentEntry

    scraper = OryxScraper()

    entries = [
        EquipmentEntry("russia", "T-62M", "destroyed", date_recorded="2024-01-15"),
        EquipmentEntry("russia", "T-62M", "destroyed", date_recorded="2024-01-15"),
        EquipmentEntry("russia", "T-62M", "captured", date_recorded="2024-01-15"),
    ]

    csv_data = scraper._generate_daily_count_csv(entries)

    assert len(csv_data) == 1
    assert csv_data[0]["country"] == "russia"
    assert csv_data[0]["equipment_type"] == "T-62M"
    assert csv_data[0]["destroyed"] == 2
    assert csv_data[0]["captured"] == 1
    assert csv_data[0]["type_total"] == 3

    scraper.close()


def test_generate_totals_by_type_csv():
    """Test totals by type CSV generation (internal method)."""
    from oryx_wat_scraper.models import EquipmentEntry

    scraper = OryxScraper()

    entries = [
        EquipmentEntry("russia", "T-62M", "destroyed"),
        EquipmentEntry("russia", "T-62M", "destroyed"),
        EquipmentEntry("russia", "T-72", "captured"),
    ]

    csv_data = scraper._generate_totals_by_type_csv(entries)

    assert len(csv_data) == 2
    assert csv_data[0]["country"] == "russia"
    assert csv_data[0]["type"] == "T-62M"
    assert csv_data[0]["destroyed"] == 2
    assert csv_data[0]["total"] == 2

    scraper.close()


def test_get_equipment_data():
    """Test public API: get_equipment_data."""
    from oryx_wat_scraper.models import EquipmentEntry

    scraper = OryxScraper()

    # Mock the internal method
    with patch.object(scraper, "_scrape_equipment_entries") as mock_scrape:
        mock_scrape.return_value = [
            EquipmentEntry("russia", "T-62M", "destroyed"),
            EquipmentEntry("russia", "T-72", "captured"),
        ]

        entries = scraper.get_equipment_data(country="russia")

        assert len(entries) == 2
        assert entries[0].equipment_type == "T-62M"
        mock_scrape.assert_called_once_with("russia")

    scraper.close()


def test_get_daily_counts():
    """Test public API: get_daily_counts."""
    from oryx_wat_scraper.models import EquipmentEntry

    scraper = OryxScraper()

    # Mock the internal method
    with patch.object(scraper, "_scrape_equipment_entries") as mock_scrape:
        mock_scrape.return_value = [
            EquipmentEntry("russia", "T-62M", "destroyed", date_recorded="2024-01-15"),
            EquipmentEntry("russia", "T-62M", "destroyed", date_recorded="2024-01-15"),
        ]

        daily_counts = scraper.get_daily_counts(countries=["russia"])

        assert len(daily_counts) == 1
        assert daily_counts[0]["country"] == "russia"
        assert daily_counts[0]["equipment_type"] == "T-62M"
        assert daily_counts[0]["destroyed"] == 2

    scraper.close()


def test_get_totals_by_type():
    """Test public API: get_totals_by_type."""
    from oryx_wat_scraper.models import EquipmentEntry

    scraper = OryxScraper()

    # Mock the internal method
    with patch.object(scraper, "_scrape_equipment_entries") as mock_scrape:
        mock_scrape.return_value = [
            EquipmentEntry("russia", "T-62M", "destroyed"),
            EquipmentEntry("russia", "T-62M", "destroyed"),
        ]

        totals = scraper.get_totals_by_type(countries=["russia"])

        assert len(totals) == 1
        assert totals[0]["country"] == "russia"
        assert totals[0]["type"] == "T-62M"
        assert totals[0]["destroyed"] == 2
        assert totals[0]["total"] == 2

    scraper.close()
