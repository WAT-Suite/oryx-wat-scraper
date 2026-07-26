"""
Async client class for scraping Oryx equipment loss data.

Based on the R script approach from: https://github.com/scarnecchia/scrape_oryx
"""

import csv
import json
import os
from datetime import datetime
from typing import Any

import httpx

from oryx_wat_scraper import parsing
from oryx_wat_scraper.client import DAILY_COUNT_FIELDS, TOTALS_BY_TYPE_FIELDS
from oryx_wat_scraper.exceptions import OryxScraperNetworkError
from oryx_wat_scraper.models import EquipmentEntry, SystemEntry


class AsyncOryxScraper:
    """
    Async scraper for Oryx equipment loss data, matching the R script approach.

    The async counterpart of :class:`~oryx_wat_scraper.client.OryxScraper`, with
    the same data model: losses are exposed both at the Oryx category level
    ("Tanks") and the model/system level ("T-62M").

    Example:
        ```python
        import asyncio
        from oryx_wat_scraper import AsyncOryxScraper

        async def main():
            async with AsyncOryxScraper() as scraper:
                entries = await scraper.get_equipment_data(country="russia")
                totals = await scraper.get_category_totals()

        asyncio.run(main())
        ```
    """

    BASE_URL = "https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html"

    def __init__(self, timeout: float = 30.0):
        """
        Initialize the async scraper.

        Args:
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self.current_date = datetime.now().strftime("%Y-%m-%d")

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()

    async def aclose(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()

    async def _fetch_page(self) -> str:
        """Fetch the HTML content from the Oryx page (internal method)."""
        if not self._client:
            raise RuntimeError(
                "Client not initialized. Use async with AsyncOryxScraper() as scraper:"
            )

        try:
            response = await self._client.get(self.BASE_URL)
            response.raise_for_status()
            return response.text
        except httpx.RequestError as e:
            raise OryxScraperNetworkError(f"Failed to fetch page: {e}") from e
        except httpx.HTTPStatusError as e:
            raise OryxScraperNetworkError(
                f"HTTP error {e.response.status_code}: {e}", status_code=e.response.status_code
            ) from e
        except Exception as e:
            raise OryxScraperNetworkError(f"Failed to fetch page: {e}") from e

    def _parse_equipment_line(
        self, line: str, country: str, category: str, html_line: str | None = None
    ) -> list[EquipmentEntry]:
        """Parse a single loss line into one entry per loss (internal method)."""
        return parsing.parse_equipment_line(line, country, category, html_line, self.current_date)

    def _generate_daily_count_csv(self, entries: list[EquipmentEntry]) -> list[dict[str, Any]]:
        """Aggregate by country, model and date (internal method)."""
        return parsing.generate_daily_count(entries, self.current_date)

    def _generate_totals_by_type_csv(self, entries: list[EquipmentEntry]) -> list[dict[str, Any]]:
        """Aggregate by country and model (internal method)."""
        return parsing.generate_totals_by_type(entries)

    async def _scrape_equipment_entries(self, country: str = "russia") -> list[EquipmentEntry]:
        """Scrape all equipment entries for a single country (internal method)."""
        country_lower = country.lower()
        entries = parsing.parse_entries(await self._fetch_page(), self.current_date)
        return [entry for entry in entries if entry.country == country_lower]

    async def _collect_entries(self, countries: list[str] | None) -> list[EquipmentEntry]:
        """
        Scrape entries for every requested country (internal method).

        The page carries all countries, so it is fetched and parsed once and the
        result filtered, rather than re-fetching per country.
        """
        if countries is None:
            countries = ["russia", "ukraine"]

        wanted = {country.lower() for country in countries}
        entries = parsing.parse_entries(await self._fetch_page(), self.current_date)
        return [entry for entry in entries if entry.country in wanted]

    async def get_equipment_data(self, country: str = "russia") -> list[EquipmentEntry]:
        """
        Get equipment entries for a specific country.

        Args:
            country: Country to scrape ('russia' or 'ukraine', default: 'russia')

        Returns:
            List of EquipmentEntry objects
        """
        return await self._scrape_equipment_entries(country)

    async def get_daily_counts(self, countries: list[str] | None = None) -> list[dict[str, Any]]:
        """
        Get daily count data aggregated by country, model and date.

        Matches the ``oryx_data`` ``daily_count.csv`` format. For the broader
        category level, see :meth:`get_category_daily_counts`.

        Args:
            countries: List of countries to scrape (default: ['russia', 'ukraine'])

        Returns:
            List of dictionaries with keys: country, equipment_type, destroyed,
            abandoned, captured, damaged, type_total, date_recorded
        """
        entries = await self._collect_entries(countries)
        return parsing.generate_daily_count(entries, self.current_date)

    async def get_totals_by_type(self, countries: list[str] | None = None) -> list[dict[str, Any]]:
        """
        Get total counts aggregated by country and model.

        Matches the ``oryx_data`` ``totals_by_type.csv`` format.

        Args:
            countries: List of countries to scrape (default: ['russia', 'ukraine'])

        Returns:
            List of dictionaries with keys: country, type, destroyed, abandoned,
            captured, damaged, total
        """
        return parsing.generate_totals_by_type(await self._collect_entries(countries))

    async def get_category_daily_counts(
        self, countries: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Get daily counts aggregated by country, Oryx category and date.

        Args:
            countries: List of countries to scrape (default: ['russia', 'ukraine'])

        Returns:
            List of dictionaries with keys: country, category, destroyed,
            abandoned, captured, damaged, category_total, date_recorded
        """
        entries = await self._collect_entries(countries)
        return parsing.generate_category_daily_count(entries, self.current_date)

    async def get_category_totals(self, countries: list[str] | None = None) -> list[dict[str, Any]]:
        """
        Get total counts aggregated by country and Oryx category.

        Args:
            countries: List of countries to scrape (default: ['russia', 'ukraine'])

        Returns:
            List of dictionaries with keys: country, category, destroyed,
            abandoned, captured, damaged, total
        """
        return parsing.generate_category_totals(await self._collect_entries(countries))

    async def get_system_entries(self, countries: list[str] | None = None) -> list[SystemEntry]:
        """
        Get individual system-level loss entries.

        ``origin`` is left empty: Oryx does not publish a country of origin per
        system, so it is the caller's job to enrich it from another source.

        Args:
            countries: List of countries to scrape (default: ['russia', 'ukraine'])

        Returns:
            List of SystemEntry objects
        """
        entries = await self._collect_entries(countries)
        return parsing.to_system_entries(entries, self.current_date)

    async def get_totals_by_system(
        self, countries: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Get total counts aggregated by country and system (model).

        Args:
            countries: List of countries to scrape (default: ['russia', 'ukraine'])

        Returns:
            List of dictionaries with keys: country, system, destroyed,
            abandoned, captured, damaged, total
        """
        return parsing.generate_totals_by_system(await self._collect_entries(countries))

    async def scrape(self, countries: list[str] | None = None) -> dict[str, Any]:
        """
        Main scraping method. Scrapes data for specified countries and generates
        CSV-compatible data structures matching the R script output.

        Args:
            countries: List of countries to scrape (default: ['russia', 'ukraine'])

        Returns:
            Dictionary with scraped data and CSV-ready structures
        """
        all_entries = await self._collect_entries(countries)

        return {
            "url": self.BASE_URL,
            "date_scraped": self.current_date,
            "total_entries": len(all_entries),
            "daily_count": parsing.generate_daily_count(all_entries, self.current_date),
            "totals_by_type": parsing.generate_totals_by_type(all_entries),
            "category_daily_count": parsing.generate_category_daily_count(
                all_entries, self.current_date
            ),
            "category_totals": parsing.generate_category_totals(all_entries),
        }

    def _save_csv(self, data: list[dict], filename: str, fieldnames: list[str]):
        """Save data to CSV file (internal method)."""
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    async def scrape_to_csv(self, output_dir: str = "outputfiles") -> dict[str, Any]:
        """
        Scrape and save to CSV files matching oryx_data format.

        Args:
            output_dir: Directory to save CSV files (default: 'outputfiles')

        Returns:
            Dictionary with scraped data
        """
        os.makedirs(output_dir, exist_ok=True)

        data = await self.scrape()

        self._save_csv(
            data["daily_count"],
            os.path.join(output_dir, "daily_count.csv"),
            DAILY_COUNT_FIELDS,
        )
        self._save_csv(
            data["totals_by_type"],
            os.path.join(output_dir, "totals_by_type.csv"),
            TOTALS_BY_TYPE_FIELDS,
        )

        return data

    async def scrape_to_json(self, output_file: str | None = None, indent: int = 2) -> str:
        """
        Scrape and return/save as JSON.

        Args:
            output_file: Optional file path to save JSON
            indent: JSON indentation (default: 2)

        Returns:
            JSON string
        """
        data = await self.scrape()
        json_str = json.dumps(data, indent=indent, ensure_ascii=False)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_str)

        return json_str
