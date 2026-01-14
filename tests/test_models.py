"""Tests for data models."""

from oryx_wat_scraper.models import EquipmentEntry, SystemEntry


def test_equipment_entry():
    """Test EquipmentEntry model."""
    entry = EquipmentEntry(
        country="russia",
        equipment_type="T-62M",
        status="destroyed",
        url="https://example.com",
        date_recorded="2024-01-15",
    )

    assert entry.country == "russia"
    assert entry.equipment_type == "T-62M"
    assert entry.status == "destroyed"
    assert entry.url == "https://example.com"
    assert entry.date_recorded == "2024-01-15"

    # Test to_dict
    data = entry.to_dict()
    assert data["country"] == "russia"
    assert data["equipment_type"] == "T-62M"
    assert "url" in data
    assert "date_recorded" in data


def test_equipment_entry_without_optional():
    """Test EquipmentEntry without optional fields."""
    entry = EquipmentEntry(
        country="ukraine",
        equipment_type="T-72",
        status="captured",
    )

    data = entry.to_dict()
    assert "url" not in data or data.get("url") is None
    assert "date_recorded" not in data or data.get("date_recorded") is None


def test_system_entry():
    """Test SystemEntry model."""
    entry = SystemEntry(
        country="russia",
        origin="Russia",
        system="S-400",
        status="destroyed",
        url="https://example.com",
        date_recorded="2024-01-15",
    )

    assert entry.country == "russia"
    assert entry.origin == "Russia"
    assert entry.system == "S-400"
    assert entry.status == "destroyed"

    data = entry.to_dict()
    assert data["country"] == "russia"
    assert data["system"] == "S-400"
