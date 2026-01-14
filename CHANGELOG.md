# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
