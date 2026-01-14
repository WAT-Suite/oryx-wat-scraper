"""
Async client class for scraping Oryx equipment loss data.
"""

import csv
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from oryx_wat_scraper.exceptions import (
    OryxScraperNetworkError,
    OryxScraperParseError,
)
from oryx_wat_scraper.models import EquipmentEntry, SystemEntry


class AsyncOryxScraper:
    """
    Async scraper for Oryx equipment loss data, matching the R script approach.

    Example:
        ```python
        import asyncio
        from oryx_wat_scraper import AsyncOryxScraper

        async def main():
            async with AsyncOryxScraper() as scraper:
                entries = await scraper.get_equipment_data(country="russia")
                daily_counts = await scraper.get_daily_counts(countries=["russia", "ukraine"])
                totals = await scraper.get_totals_by_type(country="russia")

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
        self, line: str, country: str, category: str, html_line: Optional[str] = None
    ) -> List[EquipmentEntry]:
        """
        Parse an equipment line (internal method).
        '154 T-62M: (1, destroyed) (2, destroyed) ... (1, captured)'

        The R script extracts individual numbered entries from HTML links.
        Each numbered link represents one piece of equipment with a status.

        Returns list of EquipmentEntry objects.
        """
        entries = []

        # Extract equipment name and total count
        match = re.match(r"^(\d+)\s+(.+?)\s*:", line.strip())
        if not match:
            return entries

        total_count = int(match.group(1))
        equipment_name = match.group(2).strip()

        # If we have HTML, parse the links to get individual entries
        if html_line:
            link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>\((\d+),\s*(destroyed|captured|abandoned|damaged)\)</a>'
            link_matches = re.finditer(link_pattern, html_line, re.IGNORECASE)

            for link_match in link_matches:
                url = link_match.group(1)
                entry_num = int(link_match.group(2))
                status = link_match.group(3).lower()

                entries.append(
                    EquipmentEntry(
                        country=country.lower(),
                        equipment_type=equipment_name,
                        status=status,
                        url=url if url.startswith("http") else None,
                        date_recorded=self.current_date,
                    )
                )

        # Fallback: parse from text if no HTML
        if not entries:
            status_pattern = (
                r"\((\d+(?:\s*,\s*\d+)*)\s*,\s*(destroyed|captured|abandoned|damaged)\)"
            )
            status_matches = re.finditer(status_pattern, line, re.IGNORECASE)

            for status_match in status_matches:
                numbers_str = status_match.group(1)
                status = status_match.group(2).lower()

                numbers = re.findall(r"\d+", numbers_str)
                count = len(numbers)

                for _ in range(count):
                    entries.append(
                        EquipmentEntry(
                            country=country.lower(),
                            equipment_type=equipment_name,
                            status=status,
                            date_recorded=self.current_date,
                        )
                    )

        # If still no entries but we have a count, assume all destroyed
        if not entries and total_count > 0:
            for _ in range(total_count):
                entries.append(
                    EquipmentEntry(
                        country=country.lower(),
                        equipment_type=equipment_name,
                        status="destroyed",
                        date_recorded=self.current_date,
                    )
                )

        return entries

    async def _scrape_equipment_entries(self, country: str = "russia") -> List[EquipmentEntry]:
        """
        Scrape all equipment entries for a country (internal method).
        The R script uses rvest to parse HTML structure and extract individual entries.
        """
        html_content = await self._fetch_page()
        soup = BeautifulSoup(html_content, "html.parser")

        # Find the main content (Blogger/Blogspot structure)
        content = (
            soup.find("div", class_="post-body")
            or soup.find("div", class_="post")
            or soup.find("article")
            or soup.find("body")
        )

        if not content:
            raise OryxScraperParseError("Could not find content area in HTML")

        entries = []
        current_category = None
        in_country_section = False
        country_lower = country.lower()

        # Find all elements that might contain equipment data
        for element in content.find_all(["p", "li", "div"]):
            text = element.get_text(strip=True)
            html_str = str(element)

            if not text:
                continue

            # Detect country section header
            if country_lower in text.lower() and any(
                word in text.lower() for word in ["total", "losses"]
            ):
                in_country_section = True
                continue

            # Check if we've moved to another country section
            if in_country_section:
                if "ukraine" in text.lower() and country_lower == "russia":
                    break
                if "russia" in text.lower() and country_lower == "ukraine":
                    break

            # Detect category headers
            category_match = re.search(r"^([^(]+?)\s*\((\d+)", text, re.IGNORECASE)
            if category_match:
                current_category = category_match.group(1).strip()
                continue

            # Parse equipment lines
            if in_country_section and current_category:
                equipment_match = re.match(r"^(\d+)\s+(.+?)\s*:", text)
                if equipment_match:
                    equipment_entries = self._parse_equipment_line(
                        text, country, current_category, html_str
                    )
                    entries.extend(equipment_entries)

        return entries

    def _generate_daily_count_csv(self, entries: List[EquipmentEntry]) -> List[Dict[str, Any]]:
        """
        Generate daily_count.csv format (internal method):
        country, equipment_type, destroyed, abandoned, captured, damaged, type_total, date_recorded
        """
        grouped = defaultdict(lambda: {"destroyed": 0, "abandoned": 0, "captured": 0, "damaged": 0})

        for entry in entries:
            key = (
                entry.country,
                entry.equipment_type,
                entry.date_recorded or self.current_date,
            )
            grouped[key][entry.status] += 1

        csv_data = []
        for (country, eq_type, date), counts in grouped.items():
            total = sum(counts.values())
            csv_data.append(
                {
                    "country": country,
                    "equipment_type": eq_type,
                    "destroyed": counts["destroyed"],
                    "abandoned": counts["abandoned"],
                    "captured": counts["captured"],
                    "damaged": counts["damaged"],
                    "type_total": total,
                    "date_recorded": date,
                }
            )

        return csv_data

    def _generate_totals_by_type_csv(self, entries: List[EquipmentEntry]) -> List[Dict[str, Any]]:
        """
        Generate totals_by_type.csv format (internal method):
        country, type, destroyed, abandoned, captured, damaged, total
        """
        grouped = defaultdict(lambda: {"destroyed": 0, "abandoned": 0, "captured": 0, "damaged": 0})

        for entry in entries:
            key = (entry.country, entry.equipment_type)
            grouped[key][entry.status] += 1

        csv_data = []
        for (country, eq_type), counts in grouped.items():
            total = sum(counts.values())
            csv_data.append(
                {
                    "country": country,
                    "type": eq_type,
                    "destroyed": counts["destroyed"],
                    "abandoned": counts["abandoned"],
                    "captured": counts["captured"],
                    "damaged": counts["damaged"],
                    "total": total,
                }
            )

        return csv_data

    async def get_equipment_data(self, country: str = "russia") -> List[EquipmentEntry]:
        """
        Get equipment entries for a specific country.

        Args:
            country: Country to scrape ('russia' or 'ukraine', default: 'russia')

        Returns:
            List of EquipmentEntry objects

        Example:
            ```python
            import asyncio
            from oryx_wat_scraper import AsyncOryxScraper

            async def main():
                async with AsyncOryxScraper() as scraper:
                    entries = await scraper.get_equipment_data(country="russia")
                    for entry in entries:
                        print(f"{entry.equipment_type}: {entry.status}")

            asyncio.run(main())
            ```
        """
        return await self._scrape_equipment_entries(country)

    async def get_daily_counts(self, countries: List[str] | None = None) -> List[Dict[str, Any]]:
        """
        Get daily count data aggregated by country, equipment type, and date.

        Args:
            countries: List of countries to scrape (default: ['russia', 'ukraine'])

        Returns:
            List of dictionaries with daily count data

        Example:
            ```python
            import asyncio
            from oryx_wat_scraper import AsyncOryxScraper

            async def main():
                async with AsyncOryxScraper() as scraper:
                    daily_counts = await scraper.get_daily_counts(countries=["russia"])
                    for count in daily_counts:
                        print(f"{count['equipment_type']}: {count['destroyed']} destroyed")

            asyncio.run(main())
            ```
        """
        if countries is None:
            countries = ["russia", "ukraine"]

        all_entries = []
        for country in countries:
            entries = await self._scrape_equipment_entries(country)
            all_entries.extend(entries)

        return self._generate_daily_count_csv(all_entries)

    async def get_totals_by_type(self, countries: List[str] | None = None) -> List[Dict[str, Any]]:
        """
        Get total counts aggregated by country and equipment type.

        Args:
            countries: List of countries to scrape (default: ['russia', 'ukraine'])

        Returns:
            List of dictionaries with totals by type

        Example:
            ```python
            import asyncio
            from oryx_wat_scraper import AsyncOryxScraper

            async def main():
                async with AsyncOryxScraper() as scraper:
                    totals = await scraper.get_totals_by_type(countries=["russia"])
                    for total in totals:
                        print(f"{total['type']}: {total['total']} total losses")

            asyncio.run(main())
            ```
        """
        if countries is None:
            countries = ["russia", "ukraine"]

        all_entries = []
        for country in countries:
            entries = await self._scrape_equipment_entries(country)
            all_entries.extend(entries)

        return self._generate_totals_by_type_csv(all_entries)

    async def scrape(self, countries: List[str] | None = None) -> Dict[str, Any]:
        """
        Main scraping method. Scrapes data for specified countries and generates
        CSV-compatible data structures matching the R script output.

        Args:
            countries: List of countries to scrape (default: ['russia', 'ukraine'])

        Returns:
            Dictionary with scraped data and CSV-ready structures
        """
        if countries is None:
            countries = ["russia", "ukraine"]

        all_entries = []

        for country in countries:
            entries = await self._scrape_equipment_entries(country)
            all_entries.extend(entries)

        daily_count = self._generate_daily_count_csv(all_entries)
        totals_by_type = self._generate_totals_by_type_csv(all_entries)

        return {
            "url": self.BASE_URL,
            "date_scraped": self.current_date,
            "total_entries": len(all_entries),
            "daily_count": daily_count,
            "totals_by_type": totals_by_type,
        }

    def _save_csv(self, data: List[Dict], filename: str, fieldnames: List[str]):
        """Save data to CSV file (internal method)."""
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    async def scrape_to_csv(self, output_dir: str = "outputfiles") -> Dict[str, Any]:
        """
        Scrape and save to CSV files matching oryx_data format.

        Args:
            output_dir: Directory to save CSV files (default: 'outputfiles')

        Returns:
            Dictionary with scraped data
        """
        os.makedirs(output_dir, exist_ok=True)

        data = await self.scrape()

        # Save daily_count.csv
        self._save_csv(
            data["daily_count"],
            os.path.join(output_dir, "daily_count.csv"),
            [
                "country",
                "equipment_type",
                "destroyed",
                "abandoned",
                "captured",
                "damaged",
                "type_total",
                "date_recorded",
            ],
        )

        # Save totals_by_type.csv
        self._save_csv(
            data["totals_by_type"],
            os.path.join(output_dir, "totals_by_type.csv"),
            ["country", "type", "destroyed", "abandoned", "captured", "damaged", "total"],
        )

        return data

    async def scrape_to_json(self, output_file: Optional[str] = None, indent: int = 2) -> str:
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
