"""
Data models for Oryx scraper.
"""

from dataclasses import asdict, dataclass


@dataclass
class EquipmentEntry:
    """
    Individual equipment loss entry.

    Oryx lists losses as ``<category> -> <model> -> <individual entry>``, e.g.
    ``Tanks`` -> ``T-62M`` -> ``(1, destroyed)``. Both levels matter to
    consumers, so both are kept:

    - ``equipment_type`` is the specific model (``"T-62M"``).
    - ``category`` is the Oryx section heading (``"Tanks"``).
    """

    country: str
    equipment_type: str
    status: str  # destroyed, captured, abandoned, damaged
    category: str = ""
    url: str | None = None
    date_recorded: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary, filtering None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SystemEntry:
    """
    Individual system entry with status.

    A "system" is a specific equipment model (``"T-62M"``) as opposed to the
    broader category (``"Tanks"``). ``origin`` is the country of origin of the
    system; Oryx does not publish it, so it is empty unless a caller supplies
    it from another source.
    """

    country: str
    system: str
    status: str  # destroyed, captured, abandoned, damaged
    origin: str = ""
    category: str = ""
    url: str | None = None
    date_recorded: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary, filtering None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}
