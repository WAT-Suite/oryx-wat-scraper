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


def test_get_daily_counts(sample_html):
    """Test public API: get_daily_counts."""
    scraper = OryxScraper()

    # Mock at the IO boundary so the real parsing path is exercised.
    with patch.object(scraper, "_fetch_page", return_value=sample_html):
        daily_counts = scraper.get_daily_counts(countries=["russia"])

    assert {row["country"] for row in daily_counts} == {"russia"}

    t62m = next(row for row in daily_counts if row["equipment_type"] == "T-62M")
    assert t62m["destroyed"] == 2
    assert t62m["captured"] == 1
    assert t62m["type_total"] == 3
    assert t62m["date_recorded"] == scraper.current_date

    scraper.close()


def test_get_totals_by_type(sample_html):
    """Test public API: get_totals_by_type."""
    scraper = OryxScraper()

    with patch.object(scraper, "_fetch_page", return_value=sample_html):
        totals = scraper.get_totals_by_type(countries=["russia"])

    assert {row["country"] for row in totals} == {"russia"}

    t62m = next(row for row in totals if row["type"] == "T-62M")
    assert t62m["destroyed"] == 2
    assert t62m["captured"] == 1
    assert t62m["total"] == 3

    scraper.close()


def test_get_category_totals(sample_html):
    """Category-level totals are what the API's EquipmentType filter matches on."""
    scraper = OryxScraper()

    with patch.object(scraper, "_fetch_page", return_value=sample_html):
        totals = scraper.get_category_totals()

    by_key = {(row["country"], row["category"]): row for row in totals}
    assert by_key[("russia", "Tanks")]["total"] == 4
    assert by_key[("russia", "Aircraft")]["damaged"] == 1
    assert by_key[("ukraine", "Tanks")]["captured"] == 1

    scraper.close()


def test_get_system_entries(sample_html):
    """System-level entries are the model-level detail behind each category."""
    scraper = OryxScraper()

    with patch.object(scraper, "_fetch_page", return_value=sample_html):
        systems = scraper.get_system_entries(countries=["ukraine"])

    assert {s.country for s in systems} == {"ukraine"}
    assert {s.system for s in systems} == {"T-72AV"}
    assert sorted(s.status for s in systems) == ["abandoned", "captured"]

    scraper.close()


def test_scrape_fetches_page_once(sample_html):
    """All four aggregates come from a single fetch, not one per country."""
    scraper = OryxScraper()

    with patch.object(scraper, "_fetch_page", return_value=sample_html) as mock_fetch:
        data = scraper.scrape()

    mock_fetch.assert_called_once()
    assert data["total_entries"] == 8
    assert {"daily_count", "totals_by_type", "category_daily_count", "category_totals"} <= set(data)

    scraper.close()
