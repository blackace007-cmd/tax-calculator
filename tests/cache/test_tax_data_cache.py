"""
Tests for tax data cache.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from taxcalc.cache.tax_data_cache import TaxDataCache, CacheEntry


class TestCacheEntry:
    """Tests for CacheEntry"""

    def test_create_entry(self):
        """Test creating a cache entry"""
        entry = CacheEntry(
            tax_year=2025,
            source='federal',
            data={'test': 'data'},
            cached_at=datetime.now()
        )

        assert entry.tax_year == 2025
        assert entry.source == 'federal'
        assert entry.data == {'test': 'data'}

    def test_age_days(self):
        """Test calculating entry age"""
        # Create entry 10 days ago
        old_time = datetime.now() - timedelta(days=10)
        entry = CacheEntry(
            tax_year=2025,
            source='federal',
            data={},
            cached_at=old_time
        )

        age = entry.age_days()
        assert 9.9 < age < 10.1  # Approximately 10 days

    def test_is_stale(self):
        """Test checking if entry is stale"""
        # Fresh entry
        fresh_entry = CacheEntry(
            tax_year=2025,
            source='federal',
            data={},
            cached_at=datetime.now()
        )
        assert fresh_entry.is_stale(max_age_days=90) is False

        # Stale entry (100 days old)
        stale_entry = CacheEntry(
            tax_year=2025,
            source='federal',
            data={},
            cached_at=datetime.now() - timedelta(days=100)
        )
        assert stale_entry.is_stale(max_age_days=90) is True

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization"""
        original = CacheEntry(
            tax_year=2025,
            source='federal',
            data={'key': 'value'},
            cached_at=datetime.now(),
            source_url='http://test.com'
        )

        # Serialize
        data_dict = original.to_dict()
        assert isinstance(data_dict, dict)
        assert data_dict['tax_year'] == 2025
        assert data_dict['source'] == 'federal'

        # Deserialize
        restored = CacheEntry.from_dict(data_dict)
        assert restored.tax_year == original.tax_year
        assert restored.source == original.source
        assert restored.data == original.data
        assert restored.source_url == original.source_url


class TestTaxDataCache:
    """Tests for TaxDataCache"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create cache instance with temp directory"""
        return TaxDataCache(cache_dir=temp_cache_dir)

    def test_initialization(self, cache, temp_cache_dir):
        """Test cache initialization"""
        assert cache.cache_dir == Path(temp_cache_dir)
        assert cache.cache_dir.exists()

    def test_save_and_load(self, cache):
        """Test saving and loading data"""
        test_data = {
            'tax_brackets': {
                'single': [(10000, 0.10), (50000, 0.20)]
            },
            'standard_deductions': {
                'single': 15000
            }
        }

        # Save
        cache.save(
            tax_year=2025,
            source='federal',
            data=test_data,
            source_url='http://test.com'
        )

        # Load
        entry = cache.load(tax_year=2025, source='federal')

        assert entry is not None
        assert entry.tax_year == 2025
        assert entry.source == 'federal'
        # JSON converts tuples to lists, so compare values
        assert entry.data['standard_deductions'] == test_data['standard_deductions']
        assert len(entry.data['tax_brackets']['single']) == 2
        assert entry.source_url == 'http://test.com'

    def test_load_non_existent(self, cache):
        """Test loading non-existent cache returns None"""
        entry = cache.load(tax_year=2999, source='nonexistent')
        assert entry is None

    def test_is_cached(self, cache):
        """Test checking if data is cached"""
        # Not cached yet
        assert cache.is_cached(2025, 'federal') is False

        # Cache some data
        cache.save(2025, 'federal', {'test': 'data'})

        # Now it's cached
        assert cache.is_cached(2025, 'federal') is True

    def test_is_stale(self, cache):
        """Test checking if cached data is stale"""
        # Cache fresh data
        cache.save(2025, 'federal', {'test': 'data'})

        # Fresh data is not stale
        assert cache.is_stale(2025, 'federal', max_age_days=90) is False

        # Non-existent data is considered stale
        assert cache.is_stale(2999, 'nonexistent', max_age_days=90) is True

    def test_clear_specific_source(self, cache):
        """Test clearing specific source"""
        # Cache multiple sources
        cache.save(2025, 'federal', {'fed': 'data'})
        cache.save(2025, 'california', {'ca': 'data'})

        # Clear only federal
        cache.clear(tax_year=2025, source='federal')

        # Federal should be cleared, California should remain
        assert cache.is_cached(2025, 'federal') is False
        assert cache.is_cached(2025, 'california') is True

    def test_clear_specific_year(self, cache):
        """Test clearing specific year"""
        # Cache multiple years
        cache.save(2024, 'federal', {'2024': 'data'})
        cache.save(2025, 'federal', {'2025': 'data'})

        # Clear only 2024
        cache.clear(tax_year=2024)

        # 2024 should be cleared, 2025 should remain
        assert cache.is_cached(2024, 'federal') is False
        assert cache.is_cached(2025, 'federal') is True

    def test_clear_all(self, cache):
        """Test clearing all cache"""
        # Cache multiple items
        cache.save(2024, 'federal', {'test': 'data'})
        cache.save(2025, 'federal', {'test': 'data'})
        cache.save(2025, 'california', {'test': 'data'})

        # Clear all
        cache.clear()

        # All should be cleared
        assert cache.is_cached(2024, 'federal') is False
        assert cache.is_cached(2025, 'federal') is False
        assert cache.is_cached(2025, 'california') is False

    def test_list_cached_years(self, cache):
        """Test listing cached years"""
        # Initially empty
        assert cache.list_cached_years() == []

        # Cache some years
        cache.save(2023, 'federal', {'test': 'data'})
        cache.save(2025, 'federal', {'test': 'data'})
        cache.save(2024, 'federal', {'test': 'data'})

        years = cache.list_cached_years()
        assert years == [2023, 2024, 2025]  # Should be sorted

    def test_get_cache_info(self, cache):
        """Test getting cache information"""
        # Cache some data
        cache.save(2025, 'federal', {'test': 'data'})

        info = cache.get_cache_info(2025)

        assert info['tax_year'] == 2025
        assert 'sources' in info
        assert info['sources']['federal']['cached'] is True
        assert info['sources']['california']['cached'] is False

    def test_get_cache_size(self, cache):
        """Test getting cache size"""
        initial_size = cache.get_cache_size()

        # Cache some data
        cache.save(2025, 'federal', {'test': 'data'})

        final_size = cache.get_cache_size()
        assert final_size > initial_size

    def test_repr(self, cache):
        """Test string representation"""
        cache.save(2024, 'federal', {'test': 'data'})
        cache.save(2025, 'federal', {'test': 'data'})

        repr_str = repr(cache)
        assert 'TaxDataCache' in repr_str
        assert '2024' in repr_str or '2025' in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
