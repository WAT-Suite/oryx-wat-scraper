# Oryx Scraper

Direct HTML scraper for the Oryx blog post documenting equipment losses during the Russian invasion of Ukraine.

This scraper is based on the R script approach from: https://github.com/scarnecchia/scrape_oryx

It extracts individual equipment entries and generates CSV files matching the format used in the oryx_data repository.

## Overview

This scraper parses the HTML content from:
https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html

It extracts:
- **Total losses summaries** (by country and category)
- **Individual equipment counts** by type within each category
- **Status breakdowns** (destroyed, damaged, abandoned, captured)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
# Print JSON to stdout
python scraper.py

# Save to JSON file
python scraper.py -o output.json

# Generate CSV files (matching oryx_data format)
python scraper.py --csv

# Generate CSV files in custom directory
python scraper.py --csv --output-dir my_output

# Custom indentation
python scraper.py -o output.json --indent 4

# Scrape specific countries
python scraper.py --countries russia ukraine
```

### Python API

```python
from scraper import OryxScraper

with OryxScraper() as scraper:
    data = scraper.scrape()
    print(data)

    # Or save directly to JSON
    scraper.scrape_to_json('output.json')
```

## Output Formats

### JSON Output

The scraper returns a JSON structure:

```json
{
  "url": "https://www.oryxspioenkop.com/...",
  "total_losses": [
    {
      "label": "Russia",
      "total": 23933,
      "destroyed": 18606,
      "damaged": 938,
      "abandoned": 1221,
      "captured": 3168
    },
    ...
  ],
  "categories": [
    {
      "category": "Tanks",
      "total": 4322,
      "destroyed": 3225,
      "damaged": 158,
      "abandoned": 400,
      "captured": 539,
      "equipment_types": [
        {
          "category": "Tanks",
          "name": "T-54-3M",
          "count": 2
        },
        {
          "category": "Tanks",
          "name": "T-62M",
          "count": 154
        },
        ...
      ]
    },
    ...
  ]
}
```

### CSV Output (matching oryx_data format)

When using `--csv`, the scraper generates CSV files matching the oryx_data repository:

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

## Data Formats Parsed

### Total Losses Format
```
Russia - 23933, of which: destroyed: 18606, damaged: 938, abandoned: 1221, captured: 3168
```

### Category Header Format
```
Tanks (4322, of which destroyed: 3225, damaged: 158, abandoned: 400, captured: 539)
```

### Equipment Line Format
```
154 T-62M:
2 T-54-3M:
10 T-55A:
```

## Notes

- The scraper uses BeautifulSoup to parse HTML
- It handles the Blogger/Blogspot HTML structure
- Regex patterns are used to extract structured data from text
- All numeric values are parsed as integers
- The scraper respects rate limits with a 30-second timeout

## Requirements

- Python 3.8+
- httpx (for HTTP requests)
- beautifulsoup4 (for HTML parsing)
- lxml (for faster HTML parsing)
