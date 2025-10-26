"""
Tests for HTTP utilities.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from taxcalc.fetchers.http_utils import (
    HTTPFetcher,
    FetchError,
    fetch_url,
    fetch_pdf,
    fetch_html
)


class TestHTTPFetcher:
    """Tests for HTTPFetcher class"""

    def test_initialization(self):
        """Test HTTP fetcher initialization"""
        fetcher = HTTPFetcher(
            timeout=60,
            retry_count=5,
            retry_delay=2.0
        )

        assert fetcher.timeout == 60
        assert fetcher.retry_count == 5
        assert fetcher.retry_delay == 2.0
        assert fetcher.DEFAULT_USER_AGENT in fetcher.user_agent

    def test_custom_user_agent(self):
        """Test custom user agent"""
        fetcher = HTTPFetcher(user_agent="CustomAgent/1.0")
        assert fetcher.user_agent == "CustomAgent/1.0"

    @patch('taxcalc.fetchers.http_utils.requests')
    def test_successful_fetch(self, mock_requests):
        """Test successful URL fetch"""
        # Mock response
        mock_response = Mock()
        mock_response.content = b'test content'
        mock_response.status_code = 200

        # Mock session
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_requests.Session.return_value = mock_session

        fetcher = HTTPFetcher()
        content = fetcher.fetch_url('http://test.com')

        assert content == b'test content'
        mock_session.request.assert_called_once()

    @patch('taxcalc.fetchers.http_utils.requests')
    def test_fetch_with_retries(self, mock_requests):
        """Test fetch with retries on failure"""
        # Mock responses: first two fail, third succeeds
        mock_fail_response = Mock()
        mock_fail_response.status_code = 500
        mock_fail_response.raise_for_status.side_effect = Exception("Server error")

        mock_success_response = Mock()
        mock_success_response.content = b'success'
        mock_success_response.status_code = 200

        mock_session = Mock()
        mock_session.request.side_effect = [
            mock_fail_response,
            mock_fail_response,
            mock_success_response
        ]
        mock_requests.Session.return_value = mock_session

        fetcher = HTTPFetcher(retry_count=3, retry_delay=0.01)  # Fast retries for testing
        content = fetcher.fetch_url('http://test.com')

        assert content == b'success'
        assert mock_session.request.call_count == 3

    @patch('taxcalc.fetchers.http_utils.requests')
    def test_fetch_all_retries_fail(self, mock_requests):
        """Test fetch when all retries fail"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Server error")

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_requests.Session.return_value = mock_session

        fetcher = HTTPFetcher(retry_count=3, retry_delay=0.01)

        with pytest.raises(FetchError):
            fetcher.fetch_url('http://test.com')

    @patch('taxcalc.fetchers.http_utils.requests')
    def test_fetch_pdf(self, mock_requests):
        """Test PDF fetching"""
        # Mock PDF content (PDF files start with %PDF)
        pdf_content = b'%PDF-1.4\ntest pdf content'

        mock_response = Mock()
        mock_response.content = pdf_content
        mock_response.status_code = 200

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_requests.Session.return_value = mock_session

        fetcher = HTTPFetcher()
        content = fetcher.fetch_pdf('http://test.com/file.pdf')

        assert content == pdf_content

    @patch('taxcalc.fetchers.http_utils.requests')
    def test_fetch_invalid_pdf(self, mock_requests):
        """Test fetching invalid PDF raises error"""
        mock_response = Mock()
        mock_response.content = b'not a pdf'
        mock_response.status_code = 200

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_requests.Session.return_value = mock_session

        fetcher = HTTPFetcher()

        with pytest.raises(FetchError, match="not a valid PDF"):
            fetcher.fetch_pdf('http://test.com/file.pdf')

    @patch('taxcalc.fetchers.http_utils.requests')
    def test_fetch_html(self, mock_requests):
        """Test HTML fetching"""
        html_content = b'<html><body>Test</body></html>'

        mock_response = Mock()
        mock_response.content = html_content
        mock_response.status_code = 200

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_requests.Session.return_value = mock_session

        fetcher = HTTPFetcher()
        content = fetcher.fetch_html('http://test.com')

        assert content == '<html><body>Test</body></html>'

    def test_validate_url(self):
        """Test URL validation"""
        fetcher = HTTPFetcher()

        # Valid URLs
        assert fetcher.validate_url('https://www.irs.gov/') is True
        assert fetcher.validate_url('http://www.ftb.ca.gov/') is True

        # Invalid URLs
        assert fetcher.validate_url('not a url') is False
        assert fetcher.validate_url('ftp://test.com') is False
        assert fetcher.validate_url('') is False

    def test_context_manager(self):
        """Test using fetcher as context manager"""
        with HTTPFetcher() as fetcher:
            assert fetcher.session is None  # Session created lazily

        # Session should be closed after exiting context
        # (We can't easily test this without mocking)


class TestConvenienceFunctions:
    """Test convenience functions"""

    @patch('taxcalc.fetchers.http_utils.HTTPFetcher')
    def test_fetch_url_function(self, mock_fetcher_class):
        """Test fetch_url convenience function"""
        mock_fetcher = Mock()
        mock_fetcher.fetch_url.return_value = b'content'
        mock_fetcher_class.return_value.__enter__.return_value = mock_fetcher

        content = fetch_url('http://test.com')

        assert content == b'content'
        mock_fetcher.fetch_url.assert_called_once_with('http://test.com')

    @patch('taxcalc.fetchers.http_utils.HTTPFetcher')
    def test_fetch_pdf_function(self, mock_fetcher_class):
        """Test fetch_pdf convenience function"""
        mock_fetcher = Mock()
        mock_fetcher.fetch_pdf.return_value = b'%PDF'
        mock_fetcher_class.return_value.__enter__.return_value = mock_fetcher

        content = fetch_pdf('http://test.com/file.pdf')

        assert content == b'%PDF'

    @patch('taxcalc.fetchers.http_utils.HTTPFetcher')
    def test_fetch_html_function(self, mock_fetcher_class):
        """Test fetch_html convenience function"""
        mock_fetcher = Mock()
        mock_fetcher.fetch_html.return_value = '<html></html>'
        mock_fetcher_class.return_value.__enter__.return_value = mock_fetcher

        content = fetch_html('http://test.com')

        assert content == '<html></html>'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
