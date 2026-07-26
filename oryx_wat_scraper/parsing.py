"""
Pure parsing and aggregation logic for Oryx pages.

Everything here is IO-free: it turns page HTML into entries, and entries into
aggregates. The sync and async clients both delegate to this module so the two
cannot drift apart.
"""

import re
from collections import defaultdict
from typing import Any

from bs4 import BeautifulSoup

from oryx_wat_scraper.exceptions import OryxScraperParseError
from oryx_wat_scraper.models import EquipmentEntry, SystemEntry

STATUSES = ("destroyed", "abandoned", "captured", "damaged")

# Blocks that can carry a country heading, a category heading or a loss line.
# Oryx puts country and category headings in <h3>, so headings must be scanned
# alongside <p>/<li> or every loss line is dropped for want of a country.
CONTENT_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6", "p", "li")

# "Russia - 23933, of which: destroyed: ..." / "Ukraine - 1234, of which ..."
COUNTRY_HEADING = re.compile(r"^\s*(russia|ukraine)\b\s*[-–—:]", re.IGNORECASE)

# "Tanks (4322, of which destroyed: ...)" - must start with a letter, so that
# loss lines ("154 T-62M: ...") can never be mistaken for a category.
CATEGORY_HEADING = re.compile(r"^\s*([A-Za-z][^(]*?)\s*\(\s*\d+")

# "154 T-62M: (1, destroyed) ..."
LOSS_LINE = re.compile(r"^\s*(\d+)\s+(.+?)\s*:")

# <a href="...">(1, destroyed)</a> - one link per documented loss.
LOSS_LINK = re.compile(
    r'<a[^>]*href="([^"]*)"[^>]*>\(\s*(\d+)\s*,\s*(destroyed|captured|abandoned|damaged)\s*\)</a>',
    re.IGNORECASE,
)

# Text fallback: "(1, 2, 3, destroyed)" - the numbers are individual losses.
LOSS_TEXT = re.compile(
    r"\((\d+(?:\s*,\s*\d+)*)\s*,\s*(destroyed|captured|abandoned|damaged)\)",
    re.IGNORECASE,
)


def parse_equipment_line(
    line: str,
    country: str,
    category: str,
    html_line: str | None = None,
    date_recorded: str | None = None,
) -> list[EquipmentEntry]:
    """
    Parse a single loss line into one entry per documented loss.

    ``'154 T-62M: (1, destroyed) (2, destroyed) (1, captured)'`` yields three
    entries. Prefers the HTML links, which Oryx emits one-per-loss; falls back
    to the plain text, and finally to the leading count.
    """
    entries: list[EquipmentEntry] = []

    match = LOSS_LINE.match(line.strip())
    if not match:
        return entries

    total_count = int(match.group(1))
    equipment_name = match.group(2).strip()

    def add(status: str, url: str | None = None) -> None:
        entries.append(
            EquipmentEntry(
                country=country.lower(),
                equipment_type=equipment_name,
                status=status.lower(),
                category=category,
                url=url,
                date_recorded=date_recorded,
            )
        )

    # Preferred: one link per individual piece of equipment.
    if html_line:
        for link_match in LOSS_LINK.finditer(html_line):
            url = link_match.group(1)
            add(link_match.group(3), url if url.startswith("http") else None)

    # Fallback: parse the statuses out of the plain text.
    if not entries:
        for status_match in LOSS_TEXT.finditer(line):
            status = status_match.group(2)
            for _ in re.findall(r"\d+", status_match.group(1)):
                add(status)

    # Last resort: a count with no parseable status detail.
    if not entries and total_count > 0:
        for _ in range(total_count):
            add("destroyed")

    return entries


def parse_entries(html_content: str, date_recorded: str | None = None) -> list[EquipmentEntry]:
    """
    Parse every equipment entry, for every country, out of a page.

    Walks the content blocks in document order, tracking the country and
    category headings most recently seen, and attributing each loss line to
    that context.
    """
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

    entries: list[EquipmentEntry] = []
    current_country: str | None = None
    current_category: str | None = None

    for element in content.find_all(CONTENT_TAGS):
        text = element.get_text(" ", strip=True)
        if not text:
            continue

        country_match = COUNTRY_HEADING.match(text)
        if country_match:
            current_country = country_match.group(1).lower()
            current_category = None
            continue

        category_match = CATEGORY_HEADING.match(text)
        if category_match:
            current_category = category_match.group(1).strip()
            continue

        if current_country and current_category and LOSS_LINE.match(text):
            entries.extend(
                parse_equipment_line(
                    text,
                    current_country,
                    current_category,
                    str(element),
                    date_recorded,
                )
            )

    return entries


def _tally(entries: list[EquipmentEntry], key: Any) -> dict[Any, dict[str, int]]:
    """Count entries by status under a caller-supplied grouping key."""
    grouped: dict[Any, dict[str, int]] = defaultdict(lambda: dict.fromkeys(STATUSES, 0))
    for entry in entries:
        if entry.status in grouped[key(entry)]:
            grouped[key(entry)][entry.status] += 1
    return grouped


def generate_daily_count(entries: list[EquipmentEntry], default_date: str) -> list[dict[str, Any]]:
    """
    Aggregate by country, model and date - the ``oryx_data`` daily_count format.

    Columns: country, equipment_type, destroyed, abandoned, captured, damaged,
    type_total, date_recorded
    """
    grouped = _tally(
        entries,
        lambda e: (e.country, e.equipment_type, e.date_recorded or default_date),
    )
    return [
        {
            "country": country,
            "equipment_type": equipment_type,
            **counts,
            "type_total": sum(counts.values()),
            "date_recorded": date,
        }
        for (country, equipment_type, date), counts in grouped.items()
    ]


def generate_totals_by_type(entries: list[EquipmentEntry]) -> list[dict[str, Any]]:
    """
    Aggregate by country and model - the ``oryx_data`` totals_by_type format.

    Columns: country, type, destroyed, abandoned, captured, damaged, total
    """
    grouped = _tally(entries, lambda e: (e.country, e.equipment_type))
    return [
        {
            "country": country,
            "type": equipment_type,
            **counts,
            "total": sum(counts.values()),
        }
        for (country, equipment_type), counts in grouped.items()
    ]


def generate_totals_by_system(entries: list[EquipmentEntry]) -> list[dict[str, Any]]:
    """Same as :func:`generate_totals_by_type`, keyed ``system`` instead of ``type``."""
    return [
        {"system" if key == "type" else key: value for key, value in row.items()}
        for row in generate_totals_by_type(entries)
    ]


def generate_category_daily_count(
    entries: list[EquipmentEntry], default_date: str
) -> list[dict[str, Any]]:
    """
    Aggregate by country, Oryx category and date.

    Columns: country, category, destroyed, abandoned, captured, damaged,
    category_total, date_recorded
    """
    categorised = [entry for entry in entries if entry.category]
    grouped = _tally(
        categorised,
        lambda e: (e.country, e.category, e.date_recorded or default_date),
    )
    return [
        {
            "country": country,
            "category": category,
            **counts,
            "category_total": sum(counts.values()),
            "date_recorded": date,
        }
        for (country, category, date), counts in grouped.items()
    ]


def generate_category_totals(entries: list[EquipmentEntry]) -> list[dict[str, Any]]:
    """
    Aggregate by country and Oryx category, ignoring date.

    Columns: country, category, destroyed, abandoned, captured, damaged, total
    """
    categorised = [entry for entry in entries if entry.category]
    grouped = _tally(categorised, lambda e: (e.country, e.category))
    return [
        {
            "country": country,
            "category": category,
            **counts,
            "total": sum(counts.values()),
        }
        for (country, category), counts in grouped.items()
    ]


def to_system_entries(entries: list[EquipmentEntry], default_date: str) -> list[SystemEntry]:
    """
    Project equipment entries onto system-level entries.

    ``origin`` is left empty: Oryx does not publish a country of origin per
    system, so it is the caller's job to enrich it from another source.
    """
    return [
        SystemEntry(
            country=entry.country,
            system=entry.equipment_type,
            status=entry.status,
            origin="",
            category=entry.category,
            url=entry.url,
            date_recorded=entry.date_recorded or default_date,
        )
        for entry in entries
    ]
