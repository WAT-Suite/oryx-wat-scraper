# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-07-26

### Added
- `category` field on `EquipmentEntry`, carrying the Oryx section heading
  ("Tanks") alongside the specific model ("T-62M")
- `category` field on `SystemEntry`
- `get_category_daily_counts()` and `get_category_totals()` — aggregates grouped
  by Oryx category, the level consumers filter on
- `get_system_entries()` — individual system-level losses with status and
  evidence URL, finally populating the previously unused `SystemEntry` model
- `get_totals_by_system()` — model-level totals keyed `system` rather than `type`
- `category_daily_count` and `category_totals` keys in `scrape()` output
- `oryx_wat_scraper.parsing` module holding the IO-free parsing and aggregation
  logic shared by the sync and async clients
- Test coverage for the HTML parsing path, which was previously mocked out
  entirely in every test

### Fixed
- **The scraper returned zero entries for every page.** Country headings are
  `<h3>` on the Oryx page, but the element scan only looked at `<p>`, `<li>` and
  `<div>`, so no loss line was ever attributed to a country and all results came
  back empty. Headings are now scanned too.
- Category headings no longer leak across country sections
- The page is fetched once per call instead of once per requested country
- `asyncio_mode = "auto"` set so the async test suite actually runs

### Changed
- `AsyncOryxScraper` now shares the sync client's parsing implementation rather
  than duplicating it, so the two cannot drift apart

## [0.1.0] - 2026-01-14

### Added
- Initial release with Oryx scraper functionality
- Support for scraping equipment loss data from Oryx blog
- CSV and JSON output formats
- Command-line interface
- Async client support (`AsyncOryxScraper`) with async/await methods
- Clean public API with `get_equipment_data()`, `get_daily_counts()`, and `get_totals_by_type()` methods
- Comprehensive test coverage for both sync and async clients

### Changed
- Refactored internal methods to be private (prefixed with `_`)
- Improved API design - users can now easily get the data they need without exposing implementation details
- Based on R script approach from scarnecchia/scrape_oryx

### Fixed
- Improved HTML parsing and error handling
- Fixed type annotations for better mypy compliance
- Removed unused variables

[Unreleased]: https://github.com/WAT-Suite/oryx-wat-scraper/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/WAT-Suite/oryx-wat-scraper/releases/tag/v0.1.0
