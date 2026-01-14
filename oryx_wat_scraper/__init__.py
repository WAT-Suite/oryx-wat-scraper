"""
Oryx scraper for War Track - Python package for scraping Oryx equipment loss data.

Based on the R script approach from: https://github.com/scarnecchia/scrape_oryx
"""

from oryx_wat_scraper.async_client import AsyncOryxScraper
from oryx_wat_scraper.client import OryxScraper
from oryx_wat_scraper.exceptions import (
    OryxScraperError,
    OryxScraperNetworkError,
    OryxScraperParseError,
    OryxScraperValidationError,
)
from oryx_wat_scraper.models import EquipmentEntry, SystemEntry

__version__ = "0.1.0"

__all__ = [
    "OryxScraper",
    "AsyncOryxScraper",
    "EquipmentEntry",
    "SystemEntry",
    "OryxScraperError",
    "OryxScraperNetworkError",
    "OryxScraperParseError",
    "OryxScraperValidationError",
]
