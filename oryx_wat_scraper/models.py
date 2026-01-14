"""
Data models for Oryx scraper.
"""

from dataclasses import asdict, dataclass


@dataclass
class EquipmentEntry:
    """Individual equipment entry with status."""

    country: str
    equipment_type: str
    status: str  # destroyed, captured, abandoned, damaged
    url: str | None = None
    date_recorded: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary, filtering None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SystemEntry:
    """Individual system entry with status."""

    country: str
    origin: str
    system: str
    status: str  # destroyed, captured, abandoned, damaged
    url: str | None = None
    date_recorded: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary, filtering None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}
