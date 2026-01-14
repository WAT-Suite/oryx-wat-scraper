"""
Data models for Oryx scraper.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Optional


@dataclass
class EquipmentEntry:
    """Individual equipment entry with status."""

    country: str
    equipment_type: str
    status: str  # destroyed, captured, abandoned, damaged
    url: Optional[str] = None
    date_recorded: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary, filtering None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SystemEntry:
    """Individual system entry with status."""

    country: str
    origin: str
    system: str
    status: str  # destroyed, captured, abandoned, damaged
    url: Optional[str] = None
    date_recorded: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary, filtering None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}
