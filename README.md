# oryx-wat-scraper

[![PyPI version](https://img.shields.io/pypi/v/oryx-wat-scraper.svg)](https://pypi.org/project/oryx-wat-scraper/)
[![PyPI downloads](https://img.shields.io/pypi/dm/oryx-wat-scraper.svg)](https://pypi.org/project/oryx-wat-scraper/)
[![Python versions](https://img.shields.io/pypi/pyversions/oryx-wat-scraper.svg)](https://pypi.org/project/oryx-wat-scraper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/wat-suite/oryx-wat-scraper/workflows/CI/badge.svg)](https://github.com/wat-suite/oryx-wat-scraper/actions)
[![codecov](https://codecov.io/gh/wat-suite/oryx-wat-scraper/branch/main/graph/badge.svg)](https://codecov.io/gh/wat-suite/oryx-wat-scraper)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/mypy-checked-blue.svg)](http://mypy-lang.org/)
[![GitHub stars](https://img.shields.io/github/stars/wat-suite/oryx-wat-scraper.svg?style=social&label=Star)](https://github.com/wat-suite/oryx-wat-scraper)

Python scraper for Oryx equipment loss data, matching the R script approach from [scrape_oryx](https://github.com/scarnecchia/scrape_oryx).

This package scrapes equipment loss data directly from the Oryx blog post and generates CSV files in the same format as the [oryx_data](https://github.com/scarnecchia/oryx_data) repository.

## Features

- ✅ **R Script Compatible**: Matches the approach used in the R script
- ✅ **CSV Output**: Generates CSV files matching oryx_data format
- ✅ **Type-safe**: Full type hints with dataclasses
- ✅ **Context Manager**: Proper resource cleanup
- ✅ **Well-tested**: Comprehensive test suite
- ✅ **Modern Python**: Requires Python 3.10+

## Installation

```bash
pip install oryx-wat-scraper
```

Or using `uv`:

```bash
uv add oryx-wat-scraper
```

Or using `poetry`:

```bash
poetry add oryx-wat-scraper
```

## Quick Start

### Python API

```python
from oryx_wat_scraper import OryxScraper

# Initialize the scraper
scraper = OryxScraper()

# Scrape data
data = scraper.scrape()

# Generate CSV files (matching oryx_data format)
scraper.scrape_to_csv('outputfiles')

# Or get JSON
json_data = scraper.scrape_to_json('output.json')

# Close when done
scraper.close()
```

### Context Manager

```python
from oryx_wat_scraper import OryxScraper

with OryxScraper() as scraper:
    # Scrape specific countries
    data = scraper.scrape(countries=['russia', 'ukraine'])

    # Generate CSV files
    scraper.scrape_to_csv('outputfiles')
```

### Command Line

```bash
# Generate CSV files
oryx-scraper --csv

# Save to JSON
oryx-scraper -o output.json

# Scrape specific countries
oryx-scraper --csv --countries russia ukraine

# Custom output directory
oryx-scraper --csv --output-dir my_output
```

## Output Formats

### CSV Files (matching oryx_data format)

**daily_count.csv** (columns: country, equipment_type, destroyed, abandoned, captured, damaged, type_total, date_recorded)
```csv
country,equipment_type,destroyed,abandoned,captured,damaged,type_total,date_recorded
russia,T-62M,154,5,34,1,194,2024-01-15
ukraine,T-72,45,2,8,0,55,2024-01-15
```

**totals_by_type.csv** (columns: country, type, destroyed, abandoned, captured, damaged, total)
```csv
country,type,destroyed,abandoned,captured,damaged,total
russia,T-62M,154,5,34,1,194
ukraine,T-72,45,2,8,0,55
```

### JSON Output

```python
{
  "url": "https://www.oryxspioenkop.com/...",
  "date_scraped": "2024-01-15",
  "total_entries": 1000,
  "daily_count": [...],
  "totals_by_type": [...]
}
```

## API Reference

### `OryxScraper`

Main scraper class.

#### Methods

- `scrape(countries: List[str] | None = None) -> Dict`: Scrape data for specified countries
- `scrape_to_csv(output_dir: str = 'outputfiles') -> Dict`: Scrape and save to CSV files
- `scrape_to_json(output_file: str | None = None, indent: int = 2) -> str`: Scrape and return/save as JSON
- `close()`: Close the HTTP client

### Models

- `EquipmentEntry`: Individual equipment entry with status
- `SystemEntry`: Individual system entry with status

### Exceptions

- `OryxScraperError`: Base exception
- `OryxScraperNetworkError`: Network errors
- `OryxScraperParseError`: HTML parsing errors
- `OryxScraperValidationError`: Data validation errors

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/wat-suite/oryx-wat-scraper.git
cd oryx-wat-scraper

# Install with uv
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=oryx_wat_scraper --cov-report=html

# Run specific test file
pytest tests/test_client.py
```

### Running CI Checks Locally

You can run the same checks that CI runs locally:

```bash
# Run all checks
black --check .
ruff check .
mypy oryx_wat_scraper
pytest
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy oryx_wat_scraper
```

### Make Commands

```bash
make install-dev  # Install with dev dependencies
make test         # Run tests
make lint         # Run linters
make format       # Format code
make type-check   # Type check
make clean        # Clean build artifacts
```

## Releasing

This project uses GitHub Releases to trigger PyPI publishing. The workflow automatically publishes to PyPI when a final (non-pre-release) GitHub Release is created.

### Release Workflow

#### 1. Update Version

Update the version in `pyproject.toml`:

```toml
[project]
version = "0.2.0"  # Update to your new version
```

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.0.1): Bug fixes, backwards compatible

#### 2. Update Changelog

Update `CHANGELOG.md` with the changes for this version.

#### 3. Commit and Push Changes

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
git push origin main
```

#### 4. Create a Git Tag

Create a tag matching the version (with or without 'v' prefix):

```bash
# Option 1: Tag with 'v' prefix
git tag v0.2.0

# Option 2: Tag without prefix
git tag 0.2.0

# Push the tag
git push origin v0.2.0
```

**Important:** The tag version must match the version in `pyproject.toml` exactly (excluding the 'v' prefix if used).

#### 5. Create GitHub Release

Go to the [GitHub Releases page](https://github.com/wat-suite/oryx-wat-scraper/releases) and click "Draft a new release":

**For Pre-Release (Testing):**
- **Tag:** Select the tag you just created (e.g., `v0.2.0`)
- **Release title:** `v0.2.0` (or your version)
- **Description:** Copy from `CHANGELOG.md` or write release notes
- **☑️ Set as a pre-release:** Check this box
- Click **"Publish release"**

Pre-releases are **not** published to PyPI. Use them for testing before the final release.

**For Final Release (Publishing to PyPI):**
- **Tag:** Select the tag you just created (e.g., `v0.2.0`)
- **Release title:** `v0.2.0` (or your version)
- **Description:** Copy from `CHANGELOG.md` or write release notes
- **☐ Set as a pre-release:** Leave this unchecked
- Click **"Publish release"**

The GitHub Actions workflow will:
1. Verify the tag version matches `pyproject.toml`
2. Build the package
3. Check the package with `twine`
4. Publish to PyPI (only for final releases, not pre-releases)

### Workflow Summary

```
1. Update version in pyproject.toml
2. Update CHANGELOG.md
3. Commit and push changes
4. Create and push git tag
5. Create GitHub Release (pre-release or final)
   └─> Pre-release: Testing only, not published to PyPI
   └─> Final release: Automatically published to PyPI
```

### Troubleshooting

- **Version mismatch error:** Ensure the tag version (without 'v' prefix) exactly matches `pyproject.toml` version
- **Pre-release published:** Pre-releases are intentionally skipped. Create a final release to publish to PyPI
- **Workflow not triggered:** Ensure the release is "Published" (not "Draft") and the tag exists

## Based On

This scraper is based on the R script approach from:
- [scrape_oryx](https://github.com/scarnecchia/scrape_oryx) - R script for scraping Oryx data
- [oryx_data](https://github.com/scarnecchia/oryx_data) - Processed CSV data repository

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Workflow

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass and code is formatted (`black . && ruff check . && pytest`)
6. Commit your changes (following [Conventional Commits](https://www.conventionalcommits.org/))
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Commit Message Guidelines

This project follows [Conventional Commits](https://www.conventionalcommits.org/). Commit messages should be formatted as:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Code Style

- This project uses [Black](https://black.readthedocs.io/) for code formatting
- [Ruff](https://github.com/astral-sh/ruff) is used for linting
- [mypy](https://mypy.readthedocs.io/) is used for type checking
- All code must pass linting and type checking

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/wat-suite/oryx-wat-scraper/issues) on GitHub.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

## Acknowledgments

- [Oryx](https://www.oryxspioenkop.com/) for documenting equipment losses
- [scarnecchia](https://github.com/scarnecchia) for the R script and data processing
- All contributors who help improve this library
