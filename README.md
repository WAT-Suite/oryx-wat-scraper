# oryx-wat-scraper

[![PyPI version](https://img.shields.io/pypi/v/oryx-wat-scraper.svg)](https://pypi.org/project/oryx-wat-scraper/)
[![PyPI downloads](https://img.shields.io/pypi/dm/oryx-wat-scraper.svg)](https://pypi.org/project/oryx-wat-scraper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
git clone https://github.com/your-org/oryx-wat-scraper.git
cd oryx-wat-scraper

# Install with uv
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=oryx_wat_scraper --cov-report=html

# Run specific test file
uv run pytest tests/test_client.py
```

### Code Quality

```bash
# Format code
uv run black .

# Lint code
uv run ruff check .

# Type check
uv run mypy oryx_wat_scraper
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

## Based On

This scraper is based on the R script approach from:
- [scrape_oryx](https://github.com/scarnecchia/scrape_oryx) - R script for scraping Oryx data
- [oryx_data](https://github.com/scarnecchia/oryx_data) - Processed CSV data repository

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass and code is formatted
6. Commit your changes (following the commit message guidelines)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Acknowledgments

- [Oryx](https://www.oryxspioenkop.com/) for documenting equipment losses
- [scarnecchia](https://github.com/scarnecchia) for the R script and data processing
- All contributors who help improve this library
