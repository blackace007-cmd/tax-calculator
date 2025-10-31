"""
IRS data fetcher for Revenue Procedures.

This module fetches and parses IRS Revenue Procedures to extract
inflation-adjusted tax data for a given tax year.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from taxcalc.fetchers.base import BaseTaxDataFetcher, FetchResult, FetchStatus
from taxcalc.fetchers.http_utils import HTTPFetcher, FetchError
from taxcalc.fetchers.parsers.pdf_parser import RevenueProcedureParser
from taxcalc.fetchers.parsers.validators import TaxDataValidator

logger = logging.getLogger(__name__)


class IRSRevenueProcedureFetcher(BaseTaxDataFetcher):
    """
    Fetcher for IRS Revenue Procedures.

    Revenue Procedures are published annually with inflation-adjusted amounts.
    Example: Revenue Procedure 2024-40 contains 2025 tax year data.

    Structure:
        - Standard deductions (§63)
        - AMT exemptions and phaseouts (§55)
        - Various other thresholds

    Note: Tax brackets themselves are NOT in Revenue Procedures.
    They need to be scraped from IRS.gov HTML pages.
    """

    # Known Revenue Procedures for recent years
    # Format: {tax_year: (RP number, URL)}
    REVENUE_PROCEDURES = {
        2024: ("rp-23-34", "https://www.irs.gov/pub/irs-drop/rp-23-34.pdf"),
        2025: ("rp-24-40", "https://www.irs.gov/pub/irs-drop/rp-24-40.pdf"),
        2026: ("rp-25-32", "https://www.irs.gov/pub/irs-drop/rp-25-32.pdf"),  # Estimated
    }

    def __init__(
        self,
        tax_year: int,
        cache_dir: Optional[str] = None,
        timeout: int = 30,
        retry_count: int = 3
    ):
        """
        Initialize IRS Revenue Procedure fetcher.

        Args:
            tax_year: Tax year to fetch data for
            cache_dir: Directory for caching (default: ~/.taxcalc/cache)
            timeout: HTTP request timeout in seconds
            retry_count: Number of HTTP retry attempts
        """
        super().__init__(tax_year, cache_dir, timeout, retry_count)
        self.http_fetcher = HTTPFetcher(timeout=timeout, retry_count=retry_count)
        self.pdf_parser = RevenueProcedureParser()
        self.validator = TaxDataValidator(tax_year=tax_year)

    def get_source_name(self) -> str:
        """Get source name for this fetcher"""
        return "irs_revenue_procedure"

    def get_revenue_procedure_url(self) -> Optional[str]:
        """
        Get the URL for this tax year's Revenue Procedure.

        Returns:
            URL if known, None otherwise
        """
        if self.tax_year in self.REVENUE_PROCEDURES:
            rp_number, url = self.REVENUE_PROCEDURES[self.tax_year]
            return url

        # Try to construct URL for unknown years
        # Pattern: RP YY-NN where YY is year-1, NN varies
        # This is a guess and may not work
        logger.warning(
            f"No known Revenue Procedure for tax year {self.tax_year}. "
            "Manual lookup required."
        )
        return None

    def fetch(self, force: bool = False) -> FetchResult:
        """
        Fetch IRS Revenue Procedure data.

        Args:
            force: If True, bypass cache and fetch fresh data

        Returns:
            FetchResult with extracted data
        """
        # Get URL
        url = self.get_revenue_procedure_url()
        if not url:
            result = self.create_result(
                data={},
                status=FetchStatus.FAILED,
                source_url=None
            )
            result.add_error(f"No Revenue Procedure URL known for tax year {self.tax_year}")
            return result

        self.log_fetch_start(url)

        try:
            # Download PDF
            logger.info(f"Downloading Revenue Procedure from {url}")
            pdf_bytes = self.http_fetcher.fetch_pdf(url)

            # Parse PDF
            logger.info(f"Parsing Revenue Procedure (size: {len(pdf_bytes):,} bytes)")
            data = self.parse(pdf_bytes)

            # Validate
            is_valid, errors = self.validate(data)

            if not is_valid:
                result = self.create_result(
                    data=data,
                    status=FetchStatus.PARTIAL,
                    source_url=url
                )
                for error in errors:
                    result.add_error(error)
                result.add_warning("Data validation failed, but partial data available")
            else:
                result = self.create_result(
                    data=data,
                    status=FetchStatus.SUCCESS,
                    source_url=url
                )

            self.log_fetch_complete(result)
            return result

        except FetchError as e:
            logger.error(f"Failed to fetch Revenue Procedure: {e}")
            result = self.create_result(
                data={},
                status=FetchStatus.FAILED,
                source_url=url
            )
            result.add_error(f"HTTP fetch failed: {str(e)}")
            return result

        except Exception as e:
            logger.error(f"Unexpected error during fetch: {e}", exc_info=True)
            result = self.create_result(
                data={},
                status=FetchStatus.FAILED,
                source_url=url
            )
            result.add_error(f"Unexpected error: {str(e)}")
            return result

    def parse(self, raw_data: bytes) -> Dict[str, Any]:
        """
        Parse Revenue Procedure PDF.

        Args:
            raw_data: PDF file content as bytes

        Returns:
            Dictionary with extracted tax data
        """
        return self.pdf_parser.extract_all_data(raw_data, self.tax_year)

    def validate(self, data: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate extracted Revenue Procedure data.

        Args:
            data: Extracted data dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required fields are present
        required_fields = ['standard_deductions', 'amt_exemption', 'amt_phaseout_start']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing or empty field: {field}")

        # Validate standard deductions
        if 'standard_deductions' in data:
            std_ded = data['standard_deductions']
            required_statuses = ['single', 'married_joint', 'married_separate', 'head_of_household']

            for status in required_statuses:
                if status not in std_ded:
                    errors.append(f"Missing standard deduction for {status}")
                elif not isinstance(std_ded[status], (int, float)) or std_ded[status] <= 0:
                    errors.append(f"Invalid standard deduction for {status}: {std_ded[status]}")

        # Validate AMT exemptions
        if 'amt_exemption' in data:
            amt_ex = data['amt_exemption']
            for status in ['single', 'married_joint', 'married_separate']:
                if status not in amt_ex:
                    errors.append(f"Missing AMT exemption for {status}")
                elif not isinstance(amt_ex[status], (int, float)) or amt_ex[status] <= 0:
                    errors.append(f"Invalid AMT exemption for {status}: {amt_ex[status]}")

        # Logical validation: married joint should be >= single
        if 'standard_deductions' in data:
            std_ded = data['standard_deductions']
            if 'single' in std_ded and 'married_joint' in std_ded:
                if std_ded['married_joint'] < std_ded['single']:
                    errors.append(
                        f"Married joint std deduction (${std_ded['married_joint']:,}) "
                        f"less than single (${std_ded['single']:,})"
                    )

        return (len(errors) == 0, errors)

    def __repr__(self) -> str:
        """String representation"""
        return f"IRSRevenueProcedureFetcher(tax_year={self.tax_year})"
