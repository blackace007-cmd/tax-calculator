"""
Base classes for tax data fetchers.

This module provides the abstract base class and common utilities for
fetching tax data from various sources.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class FetchStatus(Enum):
    """Status of a fetch operation"""
    SUCCESS = "success"
    PARTIAL = "partial"  # Some data fetched, some failed
    FAILED = "failed"
    CACHED = "cached"  # Used cached data


@dataclass
class FetchResult:
    """
    Result of fetching tax data from a source.

    Attributes:
        tax_year: Tax year for this data
        source: Source name (e.g., 'irs', 'ca_ftb')
        data: Structured tax data as dictionary
        status: Status of the fetch operation
        fetched_at: Timestamp when data was fetched
        source_url: URL(s) where data was fetched from
        errors: List of errors encountered (if any)
        warnings: List of warnings (if any)
        metadata: Additional metadata about the fetch
    """
    tax_year: int
    source: str
    data: Dict[str, Any]
    status: FetchStatus
    fetched_at: datetime = field(default_factory=datetime.now)
    source_url: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_success(self) -> bool:
        """Check if fetch was successful"""
        return self.status in [FetchStatus.SUCCESS, FetchStatus.PARTIAL, FetchStatus.CACHED]

    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)
        logger.error(f"[{self.source}] {error}")

    def add_warning(self, warning: str):
        """Add a warning message"""
        self.warnings.append(warning)
        logger.warning(f"[{self.source}] {warning}")


class BaseTaxDataFetcher(ABC):
    """
    Abstract base class for tax data fetchers.

    All fetchers must implement:
    - fetch(): Retrieve data from source
    - parse(): Parse raw data into structured format
    - validate(): Validate the parsed data

    Attributes:
        tax_year: Tax year to fetch data for
        cache_dir: Directory for caching fetched data
        timeout: HTTP request timeout in seconds
        retry_count: Number of retry attempts for failed requests
    """

    def __init__(
        self,
        tax_year: int,
        cache_dir: Optional[str] = None,
        timeout: int = 30,
        retry_count: int = 3
    ):
        """
        Initialize the fetcher.

        Args:
            tax_year: Tax year to fetch (e.g., 2025)
            cache_dir: Custom cache directory (default: ~/.taxcalc/cache)
            timeout: Request timeout in seconds
            retry_count: Number of retry attempts
        """
        self.tax_year = tax_year
        self.cache_dir = cache_dir
        self.timeout = timeout
        self.retry_count = retry_count
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def fetch(self, force: bool = False) -> FetchResult:
        """
        Fetch tax data from the source.

        Args:
            force: If True, bypass cache and fetch fresh data

        Returns:
            FetchResult with data and status

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement fetch()")

    @abstractmethod
    def parse(self, raw_data: bytes) -> Dict[str, Any]:
        """
        Parse raw data into structured format.

        Args:
            raw_data: Raw bytes from source (PDF, HTML, etc.)

        Returns:
            Dictionary with structured tax data

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement parse()")

    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate parsed data.

        Args:
            data: Structured tax data to validate

        Returns:
            Tuple of (is_valid, list_of_errors)

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement validate()")

    def get_source_name(self) -> str:
        """
        Get the name of this data source.

        Returns:
            Source name (e.g., 'irs', 'ca_ftb')
        """
        return self.__class__.__name__.lower().replace('fetcher', '')

    def create_result(
        self,
        data: Dict[str, Any],
        status: FetchStatus,
        source_url: Optional[str] = None
    ) -> FetchResult:
        """
        Create a FetchResult object.

        Args:
            data: Fetched and parsed data
            status: Status of the operation
            source_url: URL where data was fetched from

        Returns:
            FetchResult object
        """
        return FetchResult(
            tax_year=self.tax_year,
            source=self.get_source_name(),
            data=data,
            status=status,
            source_url=source_url,
            fetched_at=datetime.now()
        )

    def log_fetch_start(self, url: Optional[str] = None):
        """Log the start of a fetch operation"""
        msg = f"Fetching {self.tax_year} tax data"
        if url:
            msg += f" from {url}"
        self.logger.info(msg)

    def log_fetch_complete(self, result: FetchResult):
        """Log the completion of a fetch operation"""
        self.logger.info(
            f"Fetch complete: {result.status.value} "
            f"({len(result.errors)} errors, {len(result.warnings)} warnings)"
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(tax_year={self.tax_year})"
