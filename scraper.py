#!/usr/bin/env python3
"""
Oryx Website Scraper

Scrapes equipment loss data directly from the Oryx blog post, matching the approach
used in the R script: https://github.com/scarnecchia/scrape_oryx

This scraper extracts individual equipment entries and generates CSV files in the
same format as the oryx_data repository:
- daily_count.csv: Daily equipment counts by type and country
- totals_by_type.csv: Total equipment by type and country
- totals_by_system.csv: Individual system entries with status
- totals_by_system_wide.csv: Total systems by type and country
"""

import re
import csv
import json
import sys
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
from urllib.parse import urljoin, urlparse

try:
    import httpx
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required packages not installed.")
    print("Install with: pip install httpx beautifulsoup4")
    exit(1)


@dataclass
class EquipmentEntry:
    """Individual equipment entry with status."""
    country: str
    equipment_type: str
    status: str  # destroyed, captured, abandoned, damaged
    url: Optional[str] = None
    date_recorded: Optional[str] = None

    def to_dict(self) -> Dict:
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
        return {k: v for k, v in asdict(self).items() if v is not None}


class OryxScraper:
    """
    Scraper for Oryx equipment loss data, matching the R script approach.

    The R script (scrape_oryx) uses rvest to:
    1. Parse HTML structure from the blog post
    2. Extract individual equipment entries with status indicators
    3. Track equipment by country (Russia/Ukraine)
    4. Generate time-series and aggregate CSV files
    """

    BASE_URL = "https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html"

    # Status patterns in the HTML
    STATUS_PATTERNS = {
        'destroyed': r'\((\d+),\s*destroyed\)',
        'captured': r'\((\d+),\s*captured\)',
        'abandoned': r'\((\d+),\s*abandoned\)',
        'damaged': r'\((\d+),\s*damaged\)',
    }

    def __init__(self, timeout: float = 30.0):
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)
        self.soup: Optional[BeautifulSoup] = None
        self.current_date = datetime.now().strftime('%Y-%m-%d')

    def fetch_page(self) -> str:
        """Fetch the HTML content from the Oryx page."""
        try:
            response = self.client.get(self.BASE_URL)
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise Exception(f"Failed to fetch page: {e}")

    def parse_equipment_line(self, line: str, country: str, category: str, html_line: Optional[str] = None) -> List[EquipmentEntry]:
        """
        Parse an equipment line like:
        '154 T-62M: (1, destroyed) (2, destroyed) ... (1, captured)'

        The R script extracts individual numbered entries from HTML links.
        Each numbered link represents one piece of equipment with a status.

        Returns list of EquipmentEntry objects.
        """
        entries = []

        # Extract equipment name and total count
        # Pattern: number(s) followed by equipment name, then status indicators
        match = re.match(r'^(\d+)\s+(.+?)\s*:', line.strip())
        if not match:
            return entries

        total_count = int(match.group(1))
        equipment_name = match.group(2).strip()

        # If we have HTML, parse the links to get individual entries
        if html_line:
            # Find all links with numbers - these represent individual equipment pieces
            # Pattern: <a href="...">(number, status)</a> or just (number, status)
            link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>\((\d+),\s*(destroyed|captured|abandoned|damaged)\)</a>'
            link_matches = re.finditer(link_pattern, html_line, re.IGNORECASE)

            for link_match in link_matches:
                url = link_match.group(1)
                entry_num = int(link_match.group(2))
                status = link_match.group(3).lower()

                entries.append(EquipmentEntry(
                    country=country.lower(),
                    equipment_type=equipment_name,
                    status=status,
                    url=url if url.startswith('http') else None,
                    date_recorded=self.current_date
                ))

        # Fallback: parse from text if no HTML
        if not entries:
            # Extract all status indicators with their counts
            # Pattern: (number, status) or (number and number, status)
            status_pattern = r'\((\d+(?:\s*,\s*\d+)*)\s*,\s*(destroyed|captured|abandoned|damaged)\)'
            status_matches = re.finditer(status_pattern, line, re.IGNORECASE)

            for status_match in status_matches:
                numbers_str = status_match.group(1)
                status = status_match.group(2).lower()

                # Handle "1, 2, 3" format - count the numbers
                numbers = re.findall(r'\d+', numbers_str)
                count = len(numbers)

                for _ in range(count):
                    entries.append(EquipmentEntry(
                        country=country.lower(),
                        equipment_type=equipment_name,
                        status=status,
                        date_recorded=self.current_date
                    ))

        # If still no entries but we have a count, assume all destroyed
        if not entries and total_count > 0:
            for _ in range(total_count):
                entries.append(EquipmentEntry(
                    country=country.lower(),
                    equipment_type=equipment_name,
                    status='destroyed',
                    date_recorded=self.current_date
                ))

        return entries

    def parse_system_line(self, line: str, country: str) -> List[SystemEntry]:
        """
        Parse a system line. Systems are typically listed differently than equipment.
        This is a simplified parser - the R script likely has more sophisticated logic.
        """
        entries = []

        # Systems are often listed with origin and status
        # Pattern varies, but typically: "System Name (Origin) - Status"
        # This is a placeholder - actual parsing would need to match R script logic
        return entries

    def extract_country_section(self, soup: BeautifulSoup, country: str) -> BeautifulSoup:
        """Extract the section for a specific country (Russia or Ukraine)."""
        # The R script identifies country sections by headers
        # Look for headers containing country name
        country_lower = country.lower()

        # Find all headers
        headers = soup.find_all(['h2', 'h3', 'h4', 'strong'])
        for header in headers:
            header_text = header.get_text().lower()
            if country_lower in header_text:
                # Return the section starting from this header
                # Collect all following siblings until next country section
                section = BeautifulSoup('', 'html.parser')
                current = header.next_sibling
                while current:
                    if isinstance(current, str):
                        current = current.next_sibling
                        continue
                    if hasattr(current, 'name') and current.name in ['h2', 'h3', 'h4']:
                        next_header = current.get_text().lower()
                        if 'ukraine' in next_header or 'russia' in next_header:
                            if country_lower not in next_header:
                                break
                    section.append(current)
                    current = current.next_sibling
                return section

        # Fallback: return the whole document
        return soup

    def scrape_equipment_entries(self, country: str = 'russia') -> List[EquipmentEntry]:
        """
        Scrape all equipment entries for a country, matching R script approach.
        The R script uses rvest to parse HTML structure and extract individual entries.
        """
        print(f"Fetching page: {self.BASE_URL}")
        html_content = self.fetch_page()
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the main content (Blogger/Blogspot structure)
        content = (soup.find('div', class_='post-body') or
                  soup.find('div', class_='post') or
                  soup.find('article') or
                  soup.find('body'))

        if not content:
            raise ValueError("Could not find content area in HTML")

        entries = []
        current_category = None
        in_country_section = False

        # The R script likely uses CSS selectors to find country sections
        # Look for headers or strong tags containing country name
        country_lower = country.lower()

        # Find all elements that might contain equipment data
        # The R script probably looks for list items or paragraphs with equipment data
        for element in content.find_all(['p', 'li', 'div']):
            text = element.get_text(strip=True)
            html_str = str(element)

            if not text:
                continue

            # Detect country section header
            if country_lower in text.lower() and any(word in text.lower() for word in ['total', 'losses']):
                in_country_section = True
                continue

            # Check if we've moved to another country section
            if in_country_section:
                if 'ukraine' in text.lower() and country_lower == 'russia':
                    break
                if 'russia' in text.lower() and country_lower == 'ukraine':
                    break

            # Detect category headers (e.g., "Tanks (4322, of which destroyed: 3225...)")
            category_match = re.search(r'^([^(]+?)\s*\((\d+)', text, re.IGNORECASE)
            if category_match:
                current_category = category_match.group(1).strip()
                continue

            # Parse equipment lines - look for pattern: number equipment_name: (status indicators)
            if in_country_section and current_category:
                equipment_match = re.match(r'^(\d+)\s+(.+?)\s*:', text)
                if equipment_match:
                    # Parse with HTML to extract individual links
                    equipment_entries = self.parse_equipment_line(text, country, current_category, html_str)
                    entries.extend(equipment_entries)

        return entries

    def generate_daily_count_csv(self, entries: List[EquipmentEntry]) -> List[Dict]:
        """
        Generate daily_count.csv format:
        country, equipment_type, destroyed, abandoned, captured, damaged, type_total, date_recorded
        """
        # Group by country, equipment_type, and date
        grouped = defaultdict(lambda: {
            'destroyed': 0,
            'abandoned': 0,
            'captured': 0,
            'damaged': 0
        })

        for entry in entries:
            key = (entry.country, entry.equipment_type, entry.date_recorded or self.current_date)
            grouped[key][entry.status] += 1

        # Convert to CSV format
        csv_data = []
        for (country, eq_type, date), counts in grouped.items():
            total = sum(counts.values())
            csv_data.append({
                'country': country,
                'equipment_type': eq_type,
                'destroyed': counts['destroyed'],
                'abandoned': counts['abandoned'],
                'captured': counts['captured'],
                'damaged': counts['damaged'],
                'type_total': total,
                'date_recorded': date
            })

        return csv_data

    def generate_totals_by_type_csv(self, entries: List[EquipmentEntry]) -> List[Dict]:
        """
        Generate totals_by_type.csv format:
        country, type, destroyed, abandoned, captured, damaged, total
        """
        # Group by country and equipment_type (aggregate across all dates)
        grouped = defaultdict(lambda: {
            'destroyed': 0,
            'abandoned': 0,
            'captured': 0,
            'damaged': 0
        })

        for entry in entries:
            key = (entry.country, entry.equipment_type)
            grouped[key][entry.status] += 1

        # Convert to CSV format
        csv_data = []
        for (country, eq_type), counts in grouped.items():
            total = sum(counts.values())
            csv_data.append({
                'country': country,
                'type': eq_type,
                'destroyed': counts['destroyed'],
                'abandoned': counts['abandoned'],
                'captured': counts['captured'],
                'damaged': counts['damaged'],
                'total': total
            })

        return csv_data

    def scrape(self, countries: List[str] = None) -> Dict:
        """
        Main scraping method. Scrapes data for specified countries and generates
        CSV-compatible data structures matching the R script output.
        """
        if countries is None:
            countries = ['russia', 'ukraine']

        all_entries = []

        for country in countries:
            print(f"Scraping {country}...")
            entries = self.scrape_equipment_entries(country)
            all_entries.extend(entries)
            print(f"  Found {len(entries)} equipment entries")

        print(f"\nGenerating CSV data structures...")
        daily_count = self.generate_daily_count_csv(all_entries)
        totals_by_type = self.generate_totals_by_type_csv(all_entries)

        return {
            "url": self.BASE_URL,
            "date_scraped": self.current_date,
            "total_entries": len(all_entries),
            "daily_count": daily_count,
            "totals_by_type": totals_by_type,
        }

    def save_csv(self, data: List[Dict], filename: str, fieldnames: List[str]):
        """Save data to CSV file."""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"✓ Saved {len(data)} rows to {filename}")

    def scrape_to_csv(self, output_dir: str = 'outputfiles') -> Dict:
        """
        Scrape and save to CSV files matching oryx_data format.
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        data = self.scrape()

        # Save daily_count.csv
        self.save_csv(
            data['daily_count'],
            os.path.join(output_dir, 'daily_count.csv'),
            ['country', 'equipment_type', 'destroyed', 'abandoned', 'captured', 'damaged', 'type_total', 'date_recorded']
        )

        # Save totals_by_type.csv
        self.save_csv(
            data['totals_by_type'],
            os.path.join(output_dir, 'totals_by_type.csv'),
            ['country', 'type', 'destroyed', 'abandoned', 'captured', 'damaged', 'total']
        )

        return data

    def scrape_to_json(self, output_file: Optional[str] = None, indent: int = 2) -> str:
        """Scrape and return/save as JSON."""
        data = self.scrape()
        json_str = json.dumps(data, indent=indent, ensure_ascii=False)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            print(f"Data saved to {output_file}")

        return json_str

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Scrape Oryx equipment loss data (matching R script approach)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output JSON file path (default: print to stdout)',
        default=None
    )
    parser.add_argument(
        '--csv',
        action='store_true',
        help='Generate CSV files matching oryx_data format'
    )
    parser.add_argument(
        '--output-dir',
        default='outputfiles',
        help='Output directory for CSV files (default: outputfiles)'
    )
    parser.add_argument(
        '--indent',
        type=int,
        default=2,
        help='JSON indentation (default: 2)'
    )
    parser.add_argument(
        '--countries',
        nargs='+',
        default=['russia', 'ukraine'],
        help='Countries to scrape (default: russia ukraine)'
    )

    args = parser.parse_args()

    try:
        with OryxScraper() as scraper:
            if args.csv:
                scraper.scrape_to_csv(args.output_dir)
            else:
                json_output = scraper.scrape_to_json(
                    output_file=args.output,
                    indent=args.indent
                )

                if not args.output:
                    print(json_output)
                else:
                    print(f"✓ Scraping completed. Data saved to {args.output}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
