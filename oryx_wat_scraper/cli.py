"""
CLI entry point for oryx-wat-scraper.
"""

import sys

from oryx_wat_scraper import OryxScraper


def main(args: list[str] | None = None) -> int:
    """
    CLI entry point.

    Args:
        args: Command line arguments (default: sys.argv[1:])

    Returns:
        Exit code (0 for success, 1 for error)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape Oryx equipment loss data (matching R script approach)"
    )
    parser.add_argument(
        "-o", "--output", help="Output JSON file path (default: print to stdout)", default=None
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Generate CSV files matching oryx_data format",
    )
    parser.add_argument(
        "--output-dir",
        default="outputfiles",
        help="Output directory for CSV files (default: outputfiles)",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation (default: 2)")
    parser.add_argument(
        "--countries",
        nargs="+",
        default=["russia", "ukraine"],
        help="Countries to scrape (default: russia ukraine)",
    )

    parsed_args = parser.parse_args(args)

    try:
        with OryxScraper() as scraper:
            if parsed_args.csv:
                scraper.scrape_to_csv(parsed_args.output_dir)
                print(f"✓ Scraping completed. CSV files saved to {parsed_args.output_dir}")
            else:
                json_output = scraper.scrape_to_json(
                    output_file=parsed_args.output, indent=parsed_args.indent
                )

                if not parsed_args.output:
                    print(json_output)
                else:
                    print(f"✓ Scraping completed. Data saved to {parsed_args.output}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
