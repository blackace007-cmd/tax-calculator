"""
Tests for base fetcher classes.
"""

import pytest
from datetime import datetime
from taxcalc.fetchers.base import (
    BaseTaxDataFetcher,
    FetchResult,
    FetchStatus
)


class ConcreteFetcher(BaseTaxDataFetcher):
    """Concrete implementation for testing"""

    def fetch(self, force: bool = False) -> FetchResult:
        """Mock fetch implementation"""
        return self.create_result(
            data={'test': 'data'},
            status=FetchStatus.SUCCESS,
            source_url='http://test.com'
        )

    def parse(self, raw_data: bytes) -> dict:
        """Mock parse implementation"""
        return {'parsed': True}

    def validate(self, data: dict) -> tuple:
        """Mock validate implementation"""
        return (True, [])


class TestFetchResult:
    """Tests for FetchResult dataclass"""

    def test_create_result(self):
        """Test creating a fetch result"""
        result = FetchResult(
            tax_year=2025,
            source='test',
            data={'key': 'value'},
            status=FetchStatus.SUCCESS
        )

        assert result.tax_year == 2025
        assert result.source == 'test'
        assert result.data == {'key': 'value'}
        assert result.status == FetchStatus.SUCCESS
        assert isinstance(result.fetched_at, datetime)

    def test_is_success(self):
        """Test is_success method"""
        # Success status
        result = FetchResult(
            tax_year=2025,
            source='test',
            data={},
            status=FetchStatus.SUCCESS
        )
        assert result.is_success() is True

        # Failed status
        result_failed = FetchResult(
            tax_year=2025,
            source='test',
            data={},
            status=FetchStatus.FAILED
        )
        assert result_failed.is_success() is False

        # Cached status
        result_cached = FetchResult(
            tax_year=2025,
            source='test',
            data={},
            status=FetchStatus.CACHED
        )
        assert result_cached.is_success() is True

    def test_add_error(self):
        """Test adding errors"""
        result = FetchResult(
            tax_year=2025,
            source='test',
            data={},
            status=FetchStatus.FAILED
        )

        result.add_error("Test error 1")
        result.add_error("Test error 2")

        assert len(result.errors) == 2
        assert "Test error 1" in result.errors
        assert "Test error 2" in result.errors

    def test_add_warning(self):
        """Test adding warnings"""
        result = FetchResult(
            tax_year=2025,
            source='test',
            data={},
            status=FetchStatus.PARTIAL
        )

        result.add_warning("Warning 1")
        assert len(result.warnings) == 1
        assert "Warning 1" in result.warnings


class TestBaseTaxDataFetcher:
    """Tests for BaseTaxDataFetcher"""

    def test_initialization(self):
        """Test fetcher initialization"""
        fetcher = ConcreteFetcher(tax_year=2025)

        assert fetcher.tax_year == 2025
        assert fetcher.timeout == 30
        assert fetcher.retry_count == 3

    def test_custom_initialization(self):
        """Test fetcher with custom parameters"""
        fetcher = ConcreteFetcher(
            tax_year=2024,
            cache_dir='/custom/cache',
            timeout=60,
            retry_count=5
        )

        assert fetcher.tax_year == 2024
        assert fetcher.cache_dir == '/custom/cache'
        assert fetcher.timeout == 60
        assert fetcher.retry_count == 5

    def test_get_source_name(self):
        """Test getting source name"""
        fetcher = ConcreteFetcher(tax_year=2025)
        assert fetcher.get_source_name() == 'concrete'

    def test_create_result(self):
        """Test creating a result"""
        fetcher = ConcreteFetcher(tax_year=2025)
        result = fetcher.create_result(
            data={'test': 'data'},
            status=FetchStatus.SUCCESS,
            source_url='http://test.com'
        )

        assert result.tax_year == 2025
        assert result.source == 'concrete'
        assert result.data == {'test': 'data'}
        assert result.status == FetchStatus.SUCCESS
        assert result.source_url == 'http://test.com'

    def test_fetch(self):
        """Test fetch method"""
        fetcher = ConcreteFetcher(tax_year=2025)
        result = fetcher.fetch()

        assert result.is_success()
        assert result.tax_year == 2025

    def test_repr(self):
        """Test string representation"""
        fetcher = ConcreteFetcher(tax_year=2025)
        repr_str = repr(fetcher)

        assert 'ConcreteFetcher' in repr_str
        assert '2025' in repr_str


class TestAbstractMethods:
    """Test that abstract methods must be implemented"""

    def test_cannot_instantiate_base_class(self):
        """Test that base class cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseTaxDataFetcher(tax_year=2025)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
