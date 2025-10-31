"""
PDF parsing utilities for tax documents.

This module provides utilities for extracting text and tables from PDF documents,
particularly IRS Revenue Procedures and tax forms.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

logger = logging.getLogger(__name__)


class PDFParseError(Exception):
    """Exception raised when PDF parsing fails"""
    pass


class PDFParser:
    """
    PDF parser for tax documents.

    Supports multiple parsing strategies with fallbacks.
    """

    def __init__(self):
        """Initialize PDF parser"""
        if pdfplumber is None and PyPDF2 is None:
            raise ImportError(
                "PDF parsing requires 'pdfplumber' or 'PyPDF2'. "
                "Install with: pip install pdfplumber PyPDF2"
            )

    def extract_text(self, pdf_bytes: bytes) -> str:
        """
        Extract all text from PDF.

        Args:
            pdf_bytes: PDF file content as bytes

        Returns:
            Extracted text as string

        Raises:
            PDFParseError: If extraction fails
        """
        # Try pdfplumber first (better quality)
        if pdfplumber:
            try:
                return self._extract_text_pdfplumber(pdf_bytes)
            except Exception as e:
                logger.warning(f"pdfplumber extraction failed: {e}, trying PyPDF2")

        # Fall back to PyPDF2
        if PyPDF2:
            try:
                return self._extract_text_pypdf2(pdf_bytes)
            except Exception as e:
                logger.error(f"PyPDF2 extraction failed: {e}")
                raise PDFParseError(f"Failed to extract text from PDF: {e}")

        raise PDFParseError("No PDF parsing library available")

    def _extract_text_pdfplumber(self, pdf_bytes: bytes) -> str:
        """Extract text using pdfplumber"""
        text_parts = []

        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return "\n".join(text_parts)

    def _extract_text_pypdf2(self, pdf_bytes: bytes) -> str:
        """Extract text using PyPDF2"""
        text_parts = []

        reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        return "\n".join(text_parts)

    def find_section(self, text: str, section_markers: List[str]) -> Optional[str]:
        """
        Find a specific section in PDF text.

        Args:
            text: Full PDF text
            section_markers: List of patterns that identify the section start

        Returns:
            Section text if found, None otherwise
        """
        for marker in section_markers:
            # Create pattern to find section - match until next section marker or end
            # Sections typically start with ".NN " (e.g., ".15 Standard Deduction")
            pattern = re.compile(
                rf'{re.escape(marker)}\.?\s*\n.*?(?=\n\.[\d]+\s+[A-Z]|\Z)',
                re.DOTALL | re.IGNORECASE
            )

            match = pattern.search(text)
            if match:
                return match.group(0)

        return None

    def extract_dollar_amounts(self, text: str) -> List[int]:
        """
        Extract dollar amounts from text.

        Args:
            text: Text to search

        Returns:
            List of dollar amounts as integers
        """
        # Pattern for dollar amounts like $15,000 or $1,350
        pattern = r'\$(\d{1,3}(?:,\d{3})*)'

        matches = re.findall(pattern, text)
        amounts = []

        for match in matches:
            # Remove commas and convert to int
            amount = int(match.replace(',', ''))
            amounts.append(amount)

        return amounts

    def extract_filing_status_data(
        self,
        text: str,
        filing_statuses: List[str]
    ) -> Dict[str, List[int]]:
        """
        Extract data organized by filing status.

        Args:
            text: Text to parse
            filing_statuses: List of filing status names to look for

        Returns:
            Dictionary mapping filing status to extracted amounts
        """
        result = {}

        for status in filing_statuses:
            # Look for status in text (case insensitive)
            pattern = rf'{re.escape(status)}.*?\$(\d{{1,3}}(?:,\d{{3}})*)'

            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = int(match.group(1).replace(',', ''))
                result[status] = amount

        return result


class RevenueProcedureParser(PDFParser):
    """
    Specialized parser for IRS Revenue Procedures.

    Revenue Procedures contain inflation-adjusted amounts for tax years.
    Structure typically:
        SECTION 1. PURPOSE
        SECTION 2. ADJUSTED ITEMS
            .01 Tax Rate Tables (not in RP, just mentioned)
            .15 Standard Deduction
            .11 AMT Exemption
            ... etc
        SECTION 3. EFFECTIVE DATE
    """

    # Common filing status names in Revenue Procedures
    FILING_STATUSES = [
        'Married Individuals Filing Joint Returns',
        'Heads of Households',
        'Unmarried Individuals',
        'Married Individuals Filing Separate Returns',
        'Surviving Spouses'
    ]

    # Simplified status mapping - ORDER MATTERS! More specific patterns first
    # Note: Both "Married Individuals Filing Joint" and "Joint Returns" formats exist
    STATUS_MAP = {
        'married individuals filing joint returns': 'married_joint',
        'joint returns or surviving spouses': 'married_joint',
        'married individuals filing separate returns': 'married_separate',
        'heads of households': 'head_of_household',
        'unmarried individuals': 'single',
        'surviving spouses': 'married_joint',  # Same as married joint
    }

    def extract_standard_deduction(self, text: str) -> Dict[str, int]:
        """
        Extract standard deduction amounts.

        Args:
            text: Revenue Procedure text

        Returns:
            Dictionary with standard deductions by filing status
        """
        # Find standard deduction section - look for the section number and title
        section = self.find_section(text, ['.15 Standard Deduction'])

        if not section:
            logger.warning("Could not find Standard Deduction section")
            return {}

        logger.debug(f"Found standard deduction section ({len(section)} chars)")

        # Extract amounts with their associated filing statuses
        result = {}

        # Pattern: Filing Status ... $Amount
        # Look for table format in the section
        lines = section.split('\n')
        for line in lines:
            # Skip header lines
            if 'Filing Status' in line or ('Standard' in line and 'Deduction' in line):
                continue

            # Try each pattern - stop at first match to avoid duplicates
            for pattern, status_key in self.STATUS_MAP.items():
                if status_key in result:
                    # Already found this status
                    continue

                if re.search(pattern, line, re.IGNORECASE):
                    # Extract dollar amount from this line
                    amounts = self.extract_dollar_amounts(line)
                    if amounts:
                        # Take the last amount on the line (usually the deduction value)
                        result[status_key] = amounts[-1]
                        logger.debug(f"Extracted {status_key}: ${amounts[-1]:,}")
                        break  # Found match for this line, move to next line

        return result

    def extract_amt_exemption(self, text: str) -> Dict[str, int]:
        """
        Extract AMT exemption amounts.

        Args:
            text: Revenue Procedure text

        Returns:
            Dictionary with AMT exemptions by filing status
        """
        # Find AMT section - look for the actual section in the body text
        # The section starts with ".11 Exemption Amounts..."
        pattern = re.compile(
            r'\.11\s+Exemption Amounts for Alternative Minimum Tax\..*?(?=\n\.[\d]+\s+[A-Z]|\Z)',
            re.DOTALL | re.IGNORECASE
        )

        match = pattern.search(text)
        if not match:
            logger.warning("Could not find AMT Exemption section")
            return {}

        section = match.group(0)
        logger.debug(f"Found AMT section ({len(section)} chars)")

        result = {}
        lines = section.split('\n')

        for line in lines:
            # Look for exemption amounts (before the 28% rate section)
            if '28 percent' in line.lower() or 'excess taxable income' in line.lower():
                break  # Stop at the tax rate section

            # Try each pattern - stop at first match to avoid duplicates
            for pattern, status_key in self.STATUS_MAP.items():
                if status_key in result:
                    # Already found this status
                    continue

                if re.search(pattern, line, re.IGNORECASE):
                    amounts = self.extract_dollar_amounts(line)
                    if amounts:
                        result[status_key] = amounts[-1]  # Last amount on the line
                        logger.debug(f"Extracted AMT {status_key}: ${amounts[-1]:,}")
                        break  # Found match for this line, move to next line

        return result

    def extract_amt_phaseout(self, text: str) -> Dict[str, int]:
        """
        Extract AMT exemption phaseout thresholds.

        Args:
            text: Revenue Procedure text

        Returns:
            Dictionary with phaseout start thresholds by filing status
        """
        # Find AMT section - the phaseout info is in the same section
        pattern = re.compile(
            r'\.11\s+Exemption Amounts for Alternative Minimum Tax\..*?(?=\n\.[\d]+\s+[A-Z]|\Z)',
            re.DOTALL | re.IGNORECASE
        )

        match = pattern.search(text)
        if not match:
            logger.warning("Could not find AMT section for phaseout extraction")
            return {}

        section = match.group(0)

        # Find the phaseout subsection
        # It says "amounts used under § 55(d)(2) to determine the phaseout"
        phaseout_match = re.search(
            r'amounts used under.*?55\(d\)\(2\).*?phaseout.*?(?=\.[\d]+\s+[A-Z]|\Z)',
            section,
            re.DOTALL | re.IGNORECASE
        )

        if not phaseout_match:
            logger.debug("Could not find phaseout subsection in AMT section")
            return {}

        phaseout_section = phaseout_match.group(0)
        logger.debug(f"Found phaseout section ({len(phaseout_section)} chars)")

        result = {}
        lines = phaseout_section.split('\n')

        for line in lines:
            # Skip header lines
            if 'Threshold' in line or 'Amount' in line:
                continue

            # Try each pattern - stop at first match
            for pattern, status_key in self.STATUS_MAP.items():
                if status_key in result:
                    continue

                if re.search(pattern, line, re.IGNORECASE):
                    amounts = self.extract_dollar_amounts(line)
                    if amounts:
                        # First amount is the phaseout start threshold
                        result[status_key] = amounts[0]
                        logger.debug(f"Extracted AMT phaseout {status_key}: ${amounts[0]:,}")
                        break

        return result

    def extract_all_data(self, pdf_bytes: bytes, tax_year: int) -> Dict[str, Any]:
        """
        Extract all relevant data from Revenue Procedure.

        Args:
            pdf_bytes: PDF content
            tax_year: Tax year this RP applies to

        Returns:
            Dictionary with all extracted data
        """
        logger.info(f"Parsing Revenue Procedure for tax year {tax_year}")

        # Extract full text
        text = self.extract_text(pdf_bytes)

        # Extract various components
        data = {
            'tax_year': tax_year,
            'source': 'IRS Revenue Procedure',
            'standard_deductions': self.extract_standard_deduction(text),
            'amt_exemption': self.extract_amt_exemption(text),
            'amt_phaseout_start': self.extract_amt_phaseout(text),
        }

        logger.info(f"Extracted data: {len(data)} sections")

        return data
