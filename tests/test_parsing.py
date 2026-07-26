"""
Tests for the HTML parsing and aggregation layer.

These exercise the real page-walking code path end to end. The client tests
mock ``_scrape_equipment_entries`` away, so without these the parser — the part
most likely to break when Oryx changes its markup — would be untested.
"""

import pytest

from oryx_wat_scraper import parsing
from oryx_wat_scraper.exceptions import OryxScraperParseError

DATE = "2024-01-15"


def entries(html):
    return parsing.parse_entries(html, DATE)


def test_parse_entries_attributes_losses_to_country_and_category(sample_html):
    """Country and category headings are <h3>; every loss must inherit both."""
    parsed = entries(sample_html)

    russian_tanks = [e for e in parsed if e.country == "russia" and e.category == "Tanks"]
    assert {e.equipment_type for e in russian_tanks} == {"T-62M", "T-54-3M"}

    # One entry per <a>, not per leading count.
    assert len([e for e in parsed if e.equipment_type == "T-62M"]) == 3
    assert all(e.date_recorded == DATE for e in parsed)


def test_parse_entries_separates_countries(sample_html):
    """A second country heading must switch context, not leak into the first."""
    parsed = entries(sample_html)

    assert {e.country for e in parsed} == {"russia", "ukraine"}

    ukrainian = [e for e in parsed if e.country == "ukraine"]
    assert {e.equipment_type for e in ukrainian} == {"T-72AV"}
    assert {e.category for e in ukrainian} == {"Tanks"}


def test_parse_entries_resets_category_between_countries(sample_html):
    """Ukraine's Tanks must not inherit Russia's trailing Aircraft category."""
    parsed = entries(sample_html)
    assert all(e.category == "Tanks" for e in parsed if e.country == "ukraine")


def test_parse_entries_captures_status_and_url(sample_html):
    """Status and evidence URL come from the link, not the leading count."""
    parsed = entries(sample_html)
    su34 = sorted((e for e in parsed if e.equipment_type == "Su-34"), key=lambda e: e.status)

    assert [e.status for e in su34] == ["damaged", "destroyed"]
    assert su34[0].url == "https://example.com/6"
    assert su34[0].category == "Aircraft"


def test_parse_entries_falls_back_to_text_when_no_links(text_only_html):
    """Without links, statuses are read from the plain text."""
    parsed = entries(text_only_html)

    assert len(parsed) == 3
    assert sorted(e.status for e in parsed) == ["captured", "destroyed", "destroyed"]
    assert all(e.url is None for e in parsed)


def test_parse_entries_ignores_loss_lines_before_any_country_heading():
    """A loss line with no country context is not attributable, so it is dropped."""
    html = """
    <div class="post-body">
        <h3>Tanks (10, of which destroyed: 10)</h3>
        <p>5 T-90: <a href="https://example.com/1">(1, destroyed)</a></p>
    </div>
    """
    assert entries(html) == []


def test_parse_entries_raises_without_content_area():
    with pytest.raises(OryxScraperParseError):
        parsing.parse_entries("<not-html-we-understand/>", DATE)


def test_category_headings_are_not_confused_with_loss_lines(sample_html):
    """Loss lines start with a digit; categories must never absorb them."""
    parsed = entries(sample_html)
    assert "154 T-62M" not in {e.category for e in parsed}
    assert {e.category for e in parsed} == {"Tanks", "Aircraft"}


def test_generate_category_totals_groups_by_category(sample_html):
    totals = {
        (row["country"], row["category"]): row
        for row in parsing.generate_category_totals(entries(sample_html))
    }

    russian_tanks = totals[("russia", "Tanks")]
    assert russian_tanks["destroyed"] == 3
    assert russian_tanks["captured"] == 1
    assert russian_tanks["total"] == 4

    assert totals[("russia", "Aircraft")]["damaged"] == 1
    assert totals[("ukraine", "Tanks")]["abandoned"] == 1


def test_generate_category_daily_count_includes_date(sample_html):
    rows = parsing.generate_category_daily_count(entries(sample_html), DATE)

    assert all(row["date_recorded"] == DATE for row in rows)
    assert all(
        row["category_total"]
        == row["destroyed"] + row["abandoned"] + row["captured"] + row["damaged"]
        for row in rows
    )


def test_generate_daily_count_keeps_oryx_data_format(sample_html):
    """The model-level output must stay compatible with the oryx_data CSV."""
    rows = parsing.generate_daily_count(entries(sample_html), DATE)
    row = next(r for r in rows if r["equipment_type"] == "T-62M")

    assert set(row) == {
        "country",
        "equipment_type",
        "destroyed",
        "abandoned",
        "captured",
        "damaged",
        "type_total",
        "date_recorded",
    }
    assert row["destroyed"] == 2
    assert row["captured"] == 1
    assert row["type_total"] == 3


def test_generate_totals_by_system_renames_type_key(sample_html):
    parsed = entries(sample_html)
    by_type = parsing.generate_totals_by_type(parsed)
    by_system = parsing.generate_totals_by_system(parsed)

    assert all("system" in row and "type" not in row for row in by_system)
    assert [r["type"] for r in by_type] == [r["system"] for r in by_system]


def test_to_system_entries_projects_model_level_detail(sample_html):
    systems = parsing.to_system_entries(entries(sample_html), DATE)

    t62m = [s for s in systems if s.system == "T-62M"]
    assert len(t62m) == 3
    assert {s.category for s in t62m} == {"Tanks"}
    # Oryx does not publish country of origin, so it stays empty by design.
    assert all(s.origin == "" for s in systems)
    assert all(s.date_recorded == DATE for s in systems)
