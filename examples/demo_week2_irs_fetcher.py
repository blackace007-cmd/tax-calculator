#!/usr/bin/env python3
"""
Demo script for Week 2: IRS Revenue Procedure Fetcher

This demonstrates:
- Fetching IRS Revenue Procedure PDF
- Parsing inflation-adjusted amounts
- Data validation
- Complete integration of Week 2 work
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from taxcalc.fetchers.irs_fetcher import IRSRevenueProcedureFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

def main():
    print("=" * 80)
    print("TAX CALCULATOR - WEEK 2: IRS REVENUE PROCEDURE FETCHER")
    print("=" * 80)
    print()
    print("This demo fetches and parses real IRS Revenue Procedure data.")
    print()

    # Test with tax year 2025
    tax_year = 2025
    print(f"Fetching data for tax year {tax_year}...")
    print()

    # Create fetcher
    fetcher = IRSRevenueProcedureFetcher(tax_year=tax_year)

    print(f"Fetcher: {fetcher}")
    print(f"Source: {fetcher.get_source_name()}")
    print(f"URL: {fetcher.get_revenue_procedure_url()}")
    print()

    # Fetch data
    print("=" * 80)
    print("FETCHING DATA...")
    print("=" * 80)
    print()

    result = fetcher.fetch()

    # Display results
    print()
    print("=" * 80)
    print("FETCH RESULT")
    print("=" * 80)
    print(f"Status: {result.status.value}")
    print(f"Success: {result.is_success()}")
    print(f"Tax Year: {result.tax_year}")
    print(f"Source: {result.source}")
    print(f"Fetched At: {result.fetched_at}")
    print(f"Source URL: {result.source_url}")
    print()

    if result.errors:
        print(f"Errors ({len(result.errors)}):")
        for error in result.errors:
            print(f"  ✗ {error}")
        print()

    if result.warnings:
        print(f"Warnings ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")
        print()

    if result.is_success() or result.status == "partial":
        print("=" * 80)
        print("EXTRACTED DATA")
        print("=" * 80)
        print()

        # Standard Deductions
        if 'standard_deductions' in result.data:
            print("Standard Deductions:")
            for status, amount in sorted(result.data['standard_deductions'].items()):
                print(f"  {status:20} ${amount:,}")
            print()

        # AMT Exemptions
        if 'amt_exemption' in result.data:
            print("AMT Exemptions:")
            for status, amount in sorted(result.data['amt_exemption'].items()):
                print(f"  {status:20} ${amount:,}")
            print()

        # AMT Phaseout
        if 'amt_phaseout_start' in result.data:
            print("AMT Exemption Phaseout Thresholds:")
            for status, amount in sorted(result.data['amt_phaseout_start'].items()):
                print(f"  {status:20} ${amount:,}")
            print()

    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()
    print("Week 2 Accomplishments:")
    print("  ✓ PDF download from IRS.gov")
    print("  ✓ PDF text extraction with pdfplumber")
    print("  ✓ Regex parsing of Revenue Procedure format")
    print("  ✓ Data validation and error handling")
    print("  ✓ Integration with base fetcher framework")
    print()
    print("Next Steps (Week 3):")
    print("  - Scrape tax brackets from IRS HTML pages")
    print("  - Implement California FTB fetcher")
    print("  - Add LTCG bracket extraction")
    print()

    return 0 if result.is_success() else 1


if __name__ == '__main__':
    sys.exit(main())
