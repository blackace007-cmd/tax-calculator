#!/usr/bin/env python3
"""
Demo script for Week 1 foundation features.

This script demonstrates the base infrastructure for the auto-fetch system:
- HTTP fetching utilities
- Data validation
- Cache management
- Base fetcher classes

Week 1 focuses on the foundation - actual IRS/FTB fetchers come in Week 2-3.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from taxcalc.fetchers.http_utils import HTTPFetcher, fetch_url
from taxcalc.fetchers.parsers.validators import TaxDataValidator
from taxcalc.cache.tax_data_cache import TaxDataCache, CacheEntry
from taxcalc.fetchers.base import BaseTaxDataFetcher, FetchResult, FetchStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_http_fetcher():
    """Demonstrate HTTP fetching capabilities"""
    print("=" * 80)
    print("DEMO 1: HTTP Fetcher")
    print("=" * 80)

    # Create HTTP fetcher with custom settings
    fetcher = HTTPFetcher(
        timeout=10,
        retry_count=3,
        retry_delay=1.0
    )

    print(f"\nHTTP Fetcher configured:")
    print(f"  Timeout: {fetcher.timeout}s")
    print(f"  Retry count: {fetcher.retry_count}")
    print(f"  User agent: {fetcher.user_agent}")

    # Test URL validation
    print("\nTesting URL validation:")
    test_urls = [
        'https://www.irs.gov/',
        'http://www.ftb.ca.gov/',
        'not a url',
        'ftp://invalid.com'
    ]

    for url in test_urls:
        is_valid = fetcher.validate_url(url)
        print(f"  {url:<40} {'✓ Valid' if is_valid else '✗ Invalid'}")

    print("\n✓ HTTP Fetcher demo complete\n")


def demo_validator():
    """Demonstrate data validation"""
    print("=" * 80)
    print("DEMO 2: Data Validator")
    print("=" * 80)

    validator = TaxDataValidator(tax_year=2025)

    # Test data with valid federal structure
    valid_data = {
        'tax_brackets': {
            'single': [
                (11925, 0.10),
                (48475, 0.12),
                (103350, 0.22),
                (float('inf'), 0.37)
            ],
            'married_joint': [
                (23850, 0.10),
                (96950, 0.12),
                (206700, 0.22),
                (float('inf'), 0.37)
            ],
            'married_separate': [
                (11925, 0.10),
                (48475, 0.12),
                (float('inf'), 0.37)
            ],
            'head_of_household': [
                (17000, 0.10),
                (64850, 0.12),
                (float('inf'), 0.37)
            ]
        },
        'standard_deductions': {
            'single': 15000,
            'married_joint': 30000,
            'married_separate': 15000,
            'head_of_household': 22500
        },
        'ltcg_brackets': {
            'single': [(48350, 0.00), (533400, 0.15), (float('inf'), 0.20)],
            'married_joint': [(96700, 0.00), (600050, 0.15), (float('inf'), 0.20)],
            'married_separate': [(48350, 0.00), (300025, 0.15), (float('inf'), 0.20)],
            'head_of_household': [(64750, 0.00), (566700, 0.15), (float('inf'), 0.20)]
        },
        'amt_exemption': {
            'single': 85700,
            'married_joint': 133300,
            'married_separate': 66650,
            'head_of_household': 85700
        },
        'amt_phaseout_start': {
            'single': 609350,
            'married_joint': 1218700,
            'married_separate': 609350,
            'head_of_household': 609350
        },
        'niit_thresholds': {
            'single': 200000,
            'married_joint': 250000,
            'married_separate': 125000,
            'head_of_household': 200000
        },
        'medicare_thresholds': {
            'single': 200000,
            'married_joint': 250000,
            'married_separate': 125000,
            'head_of_household': 200000
        }
    }

    print("\nValidating valid federal data...")
    is_valid, errors = validator.validate_federal_data(valid_data)
    print(f"  Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for error in errors[:3]:
            print(f"    - {error}")

    # Test data with invalid brackets (wrong order)
    invalid_data = {
        **valid_data,
        'tax_brackets': {
            'single': [
                (50000, 0.10),
                (30000, 0.12),  # Wrong order!
                (float('inf'), 0.37)
            ],
            'married_joint': [(float('inf'), 0.10)],
            'married_separate': [(float('inf'), 0.10)],
            'head_of_household': [(float('inf'), 0.10)]
        }
    }

    print("\nValidating invalid federal data (wrong bracket order)...")
    is_valid, errors = validator.validate_federal_data(invalid_data)
    print(f"  Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    if errors:
        print(f"  Errors found: {len(errors)}")
        for error in errors[:3]:
            print(f"    - {error}")

    print("\n✓ Validator demo complete\n")


def demo_cache():
    """Demonstrate cache management"""
    print("=" * 80)
    print("DEMO 3: Tax Data Cache")
    print("=" * 80)

    # Create cache in temp directory for demo
    import tempfile
    temp_dir = tempfile.mkdtemp()
    cache = TaxDataCache(cache_dir=temp_dir)

    print(f"\nCache directory: {cache.cache_dir}")

    # Save some data
    federal_data = {
        'tax_brackets': {
            'single': [(10000, 0.10), (float('inf'), 0.20)]
        },
        'standard_deductions': {
            'single': 15000,
            'married_joint': 30000,
            'married_separate': 15000,
            'head_of_household': 22500
        }
    }

    ca_data = {
        'tax_brackets': {
            'single': [(10000, 0.01), (float('inf'), 0.10)]
        },
        'sdi_rate': 0.012
    }

    print("\nSaving data to cache...")
    cache.save(2024, 'federal', federal_data, source_url='http://irs.gov/test')
    cache.save(2024, 'california', ca_data, source_url='http://ftb.ca.gov/test')
    cache.save(2025, 'federal', federal_data, source_url='http://irs.gov/test')
    print("  ✓ Saved federal data for 2024")
    print("  ✓ Saved California data for 2024")
    print("  ✓ Saved federal data for 2025")

    # List cached years
    print("\nCached years:")
    years = cache.list_cached_years()
    for year in years:
        print(f"  - {year}")

    # Get cache info
    print("\nCache info for 2024:")
    info = cache.get_cache_info(2024)
    for source, source_info in info['sources'].items():
        if source_info['cached']:
            print(f"  {source}:")
            print(f"    Cached: Yes")
            print(f"    Age: {source_info['age_days']:.1f} days")
            print(f"    URL: {source_info['source_url']}")
        else:
            print(f"  {source}: Not cached")

    # Load data
    print("\nLoading federal data for 2024...")
    entry = cache.load(2024, 'federal')
    if entry:
        print(f"  ✓ Loaded successfully")
        print(f"  Tax year: {entry.tax_year}")
        print(f"  Source: {entry.source}")
        print(f"  Data keys: {list(entry.data.keys())}")
        print(f"  Age: {entry.age_days():.2f} days")

    # Cache size
    size_bytes = cache.get_cache_size()
    print(f"\nTotal cache size: {size_bytes:,} bytes")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    print("\n✓ Cache demo complete (temp cache cleaned up)\n")


def demo_base_fetcher():
    """Demonstrate base fetcher class"""
    print("=" * 80)
    print("DEMO 4: Base Fetcher Class")
    print("=" * 80)

    # Create a simple concrete fetcher for demo
    class DemoFetcher(BaseTaxDataFetcher):
        """Demo fetcher implementation"""

        def fetch(self, force: bool = False) -> FetchResult:
            self.log_fetch_start("http://demo.com")

            # Simulate fetching
            data = {
                'tax_brackets': {
                    'single': [(float('inf'), 0.10)]
                }
            }

            result = self.create_result(
                data=data,
                status=FetchStatus.SUCCESS,
                source_url="http://demo.com"
            )

            self.log_fetch_complete(result)
            return result

        def parse(self, raw_data: bytes) -> dict:
            return {'parsed': True}

        def validate(self, data: dict) -> tuple:
            return (True, [])

    print("\nCreating demo fetcher for tax year 2025...")
    fetcher = DemoFetcher(tax_year=2025, timeout=30, retry_count=3)

    print(f"  Fetcher: {fetcher}")
    print(f"  Tax year: {fetcher.tax_year}")
    print(f"  Timeout: {fetcher.timeout}s")
    print(f"  Retry count: {fetcher.retry_count}")
    print(f"  Source name: {fetcher.get_source_name()}")

    print("\nFetching data...")
    result = fetcher.fetch()

    print(f"\nFetch result:")
    print(f"  Status: {result.status.value}")
    print(f"  Success: {result.is_success()}")
    print(f"  Tax year: {result.tax_year}")
    print(f"  Source: {result.source}")
    print(f"  Data keys: {list(result.data.keys())}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")

    print("\n✓ Base fetcher demo complete\n")


def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("TAX CALCULATOR - WEEK 1 FOUNDATION DEMO")
    print("=" * 80)
    print("\nThis demo showcases the foundation built in Week 1:")
    print("  1. HTTP Fetcher - Network utilities with retry logic")
    print("  2. Validator - Data validation framework")
    print("  3. Cache - Local caching system")
    print("  4. Base Fetcher - Abstract base for data fetchers")
    print("\n")

    try:
        demo_http_fetcher()
        demo_validator()
        demo_cache()
        demo_base_fetcher()

        print("=" * 80)
        print("ALL DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nNext steps:")
        print("  Week 2: Implement IRS Revenue Procedure fetcher")
        print("  Week 3: Implement California FTB fetcher")
        print("  Week 4: Build CLI tool and integration")
        print("\nFoundation is ready for building actual fetchers!")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
