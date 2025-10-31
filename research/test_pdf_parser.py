"""Test the PDF parser with Revenue Procedure 2024-40"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from taxcalc.fetchers.parsers.pdf_parser import RevenueProcedureParser
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

def main():
    parser = RevenueProcedureParser()

    # Load the PDF
    pdf_path = Path(__file__).parent / 'rp-24-40.pdf'
    print(f"Loading {pdf_path}...\n")

    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    # Extract all data
    print("=" * 80)
    print("EXTRACTING DATA FROM REVENUE PROCEDURE 2024-40 (Tax Year 2025)")
    print("=" * 80)
    print()

    data = parser.extract_all_data(pdf_bytes, tax_year=2025)

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print(f"\nTax Year: {data['tax_year']}")
    print(f"Source: {data['source']}")

    print("\nStandard Deductions:")
    for status, amount in data['standard_deductions'].items():
        print(f"  {status:20} ${amount:,}")

    print("\nAMT Exemptions:")
    for status, amount in data['amt_exemption'].items():
        print(f"  {status:20} ${amount:,}")

    print("\nAMT Phaseout Thresholds:")
    for status, amount in data['amt_phaseout_start'].items():
        print(f"  {status:30} ${amount:,}")

    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
