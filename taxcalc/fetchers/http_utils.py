"""
HTTP utilities for fetching tax data from web sources.

This module provides common HTTP functionality with retry logic,
timeout handling, and error recovery.
"""

import time
import logging
from typing import Optional, Dict
from urllib.parse import urlparse

# Lazy import of requests (imported when needed)
try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)


class FetchError(Exception):
    """Exception raised when fetching data fails"""
    pass


class HTTPFetcher:
    """
    HTTP client for fetching tax data with retry logic.

    Features:
    - Automatic retries with exponential backoff
    - Request timeout handling
    - User agent identification
    - HTTPS verification
    """

    DEFAULT_USER_AGENT = "TaxCalc-DataFetcher/1.0 (https://github.com/blackace007-cmd/tax-calculator)"
    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_RETRY_DELAY = 1.0  # seconds

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        retry_count: int = DEFAULT_RETRY_COUNT,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        user_agent: Optional[str] = None
    ):
        """
        Initialize HTTP fetcher.

        Args:
            timeout: Request timeout in seconds
            retry_count: Number of retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
            user_agent: Custom user agent string
        """
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.session = None

    def _get_session(self):
        """Get or create requests session (lazy loading)"""
        if self.session is None:
            if requests is None:
                raise ImportError(
                    "The 'requests' package is required for fetching data. "
                    "Install it with: pip install requests"
                )
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': self.user_agent,
                'Accept-Encoding': 'gzip, deflate',
            })
        return self.session

    def fetch_url(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> bytes:
        """
        Fetch content from a URL with retry logic.

        Args:
            url: URL to fetch
            method: HTTP method (GET, POST, etc.)
            headers: Additional headers
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response content as bytes

        Raises:
            FetchError: If fetch fails after all retries
        """
        session = self._get_session()

        # Merge headers
        request_headers = headers.copy() if headers else {}

        last_error = None

        for attempt in range(self.retry_count):
            try:
                logger.debug(f"Fetching {url} (attempt {attempt + 1}/{self.retry_count})")

                response = session.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    timeout=self.timeout,
                    **kwargs
                )

                # Raise for HTTP errors
                response.raise_for_status()

                logger.info(f"Successfully fetched {url} ({len(response.content)} bytes)")
                return response.content

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Fetch attempt {attempt + 1}/{self.retry_count} failed for {url}: {e}"
                )

                # Don't retry on 4xx errors (client errors)
                if hasattr(e, 'response') and e.response is not None:
                    if 400 <= e.response.status_code < 500:
                        logger.error(f"Client error ({e.response.status_code}), not retrying")
                        break

                # Wait before retrying (exponential backoff)
                if attempt < self.retry_count - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.debug(f"Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)

        # All retries failed
        raise FetchError(f"Failed to fetch {url} after {self.retry_count} attempts: {last_error}")

    def fetch_pdf(self, url: str) -> bytes:
        """
        Fetch a PDF document.

        Args:
            url: URL of PDF file

        Returns:
            PDF content as bytes

        Raises:
            FetchError: If PDF fetch fails
        """
        logger.info(f"Fetching PDF from {url}")
        content = self.fetch_url(
            url,
            headers={'Accept': 'application/pdf'}
        )

        # Verify it's actually a PDF
        if not content.startswith(b'%PDF'):
            raise FetchError(f"Downloaded file from {url} is not a valid PDF")

        return content

    def fetch_html(self, url: str) -> str:
        """
        Fetch HTML content.

        Args:
            url: URL of HTML page

        Returns:
            HTML content as string

        Raises:
            FetchError: If HTML fetch fails
        """
        logger.info(f"Fetching HTML from {url}")
        content = self.fetch_url(
            url,
            headers={'Accept': 'text/html'}
        )

        # Decode to string
        try:
            # Try UTF-8 first
            return content.decode('utf-8')
        except UnicodeDecodeError:
            # Fall back to latin-1
            logger.warning("UTF-8 decode failed, trying latin-1")
            return content.decode('latin-1', errors='replace')

    def validate_url(self, url: str) -> bool:
        """
        Validate a URL is well-formed and uses HTTPS.

        Args:
            url: URL to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            parsed = urlparse(url)

            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False

            # Prefer HTTPS for security
            if parsed.scheme not in ['https', 'http']:
                return False

            return True

        except Exception:
            return False

    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()
            self.session = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Convenience functions
def fetch_url(
    url: str,
    timeout: int = HTTPFetcher.DEFAULT_TIMEOUT,
    retry_count: int = HTTPFetcher.DEFAULT_RETRY_COUNT
) -> bytes:
    """
    Convenience function to fetch a URL.

    Args:
        url: URL to fetch
        timeout: Request timeout
        retry_count: Number of retries

    Returns:
        Content as bytes
    """
    with HTTPFetcher(timeout=timeout, retry_count=retry_count) as fetcher:
        return fetcher.fetch_url(url)


def fetch_pdf(url: str, timeout: int = HTTPFetcher.DEFAULT_TIMEOUT) -> bytes:
    """
    Convenience function to fetch a PDF.

    Args:
        url: URL of PDF
        timeout: Request timeout

    Returns:
        PDF content as bytes
    """
    with HTTPFetcher(timeout=timeout) as fetcher:
        return fetcher.fetch_pdf(url)


def fetch_html(url: str, timeout: int = HTTPFetcher.DEFAULT_TIMEOUT) -> str:
    """
    Convenience function to fetch HTML.

    Args:
        url: URL of HTML page
        timeout: Request timeout

    Returns:
        HTML content as string
    """
    with HTTPFetcher(timeout=timeout) as fetcher:
        return fetcher.fetch_html(url)
