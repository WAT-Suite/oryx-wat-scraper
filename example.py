#!/usr/bin/env python3
"""
Example usage of the Oryx scraper.
"""

from scraper import OryxScraper

def main():
    print("=" * 60)
    print("Oryx Scraper Example")
    print("=" * 60)

    with OryxScraper() as scraper:
        # Scrape the data
        data = scraper.scrape()

        # Print summary
        print(f"\n📊 Total Losses Found: {len(data['total_losses'])}")
        for loss in data['total_losses']:
            print(f"\n  {loss['label']}:")
            print(f"    Total: {loss['total']:,}")
            print(f"    - Destroyed: {loss['destroyed']:,}")
            print(f"    - Damaged: {loss['damaged']:,}")
            print(f"    - Abandoned: {loss['abandoned']:,}")
            print(f"    - Captured: {loss['captured']:,}")

        print(f"\n📦 Categories Found: {len(data['categories'])}")
        for category in data['categories'][:5]:  # Show first 5
            print(f"\n  {category['category']}:")
            print(f"    Total: {category['total']:,}")
            print(f"    Equipment Types: {len(category['equipment_types'])}")
            if category['equipment_types']:
                print(f"    Examples:")
                for eq in category['equipment_types'][:3]:  # Show first 3
                    print(f"      - {eq['name']}: {eq['count']}")

        # Save to file
        output_file = 'oryx_data.json'
        scraper.scrape_to_json(output_file)
        print(f"\n💾 Full data saved to: {output_file}")

if __name__ == '__main__':
    main()
