"""
Cache management for tax data.

This module handles local caching of fetched tax data to minimize
network requests and speed up repeated access.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """
    Entry in the tax data cache.

    Attributes:
        tax_year: Tax year for this data
        source: Source name ('federal' or 'california')
        data: The cached tax data
        cached_at: When this data was cached
        source_url: URL where data was originally fetched from
        checksum: Optional checksum for data integrity
    """
    tax_year: int
    source: str
    data: Dict[str, Any]
    cached_at: datetime
    source_url: Optional[str] = None
    checksum: Optional[str] = None

    def age_days(self) -> float:
        """Get age of cached data in days"""
        return (datetime.now() - self.cached_at).total_seconds() / 86400

    def is_stale(self, max_age_days: int = 90) -> bool:
        """Check if cached data is stale"""
        return self.age_days() > max_age_days

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'tax_year': self.tax_year,
            'source': self.source,
            'data': self.data,
            'cached_at': self.cached_at.isoformat(),
            'source_url': self.source_url,
            'checksum': self.checksum,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary"""
        d = d.copy()
        d['cached_at'] = datetime.fromisoformat(d['cached_at'])
        return cls(**d)


class TaxDataCache:
    """
    Manager for tax data cache.

    Directory structure:
    ```
    cache_dir/
    ├── 2024/
    │   ├── federal.json
    │   ├── california.json
    │   └── metadata.json
    ├── 2025/
    │   └── ...
    ```
    """

    DEFAULT_CACHE_DIR = os.path.expanduser('~/.taxcalc/cache')
    DEFAULT_MAX_AGE_DAYS = 90

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize cache manager.

        Args:
            cache_dir: Custom cache directory (default: ~/.taxcalc/cache)
        """
        self.cache_dir = Path(cache_dir or self.DEFAULT_CACHE_DIR)
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Cache directory: {self.cache_dir}")

    def _get_year_dir(self, tax_year: int) -> Path:
        """Get directory for a specific tax year"""
        year_dir = self.cache_dir / str(tax_year)
        year_dir.mkdir(exist_ok=True)
        return year_dir

    def _get_cache_file(self, tax_year: int, source: str) -> Path:
        """Get cache file path for a source"""
        return self._get_year_dir(tax_year) / f"{source}.json"

    def save(
        self,
        tax_year: int,
        source: str,
        data: Dict[str, Any],
        source_url: Optional[str] = None
    ) -> None:
        """
        Save data to cache.

        Args:
            tax_year: Tax year
            source: Source name ('federal' or 'california')
            data: Tax data to cache
            source_url: URL where data was fetched from
        """
        entry = CacheEntry(
            tax_year=tax_year,
            source=source,
            data=data,
            cached_at=datetime.now(),
            source_url=source_url
        )

        cache_file = self._get_cache_file(tax_year, source)

        try:
            with open(cache_file, 'w') as f:
                json.dump(entry.to_dict(), f, indent=2, allow_nan=True)

            logger.info(f"Cached {source} data for {tax_year} to {cache_file}")

        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
            raise

    def load(self, tax_year: int, source: str) -> Optional[CacheEntry]:
        """
        Load data from cache.

        Args:
            tax_year: Tax year
            source: Source name

        Returns:
            CacheEntry if found, None otherwise
        """
        cache_file = self._get_cache_file(tax_year, source)

        if not cache_file.exists():
            logger.debug(f"No cache found for {source}/{tax_year}")
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            entry = CacheEntry.from_dict(data)
            logger.info(f"Loaded {source} data for {tax_year} from cache (age: {entry.age_days():.1f} days)")
            return entry

        except Exception as e:
            logger.error(f"Failed to load cache from {cache_file}: {e}")
            return None

    def is_cached(self, tax_year: int, source: str) -> bool:
        """
        Check if data is cached.

        Args:
            tax_year: Tax year
            source: Source name

        Returns:
            True if cached, False otherwise
        """
        return self._get_cache_file(tax_year, source).exists()

    def is_stale(
        self,
        tax_year: int,
        source: str,
        max_age_days: int = DEFAULT_MAX_AGE_DAYS
    ) -> bool:
        """
        Check if cached data is stale.

        Args:
            tax_year: Tax year
            source: Source name
            max_age_days: Maximum age in days

        Returns:
            True if stale or not cached, False if fresh
        """
        entry = self.load(tax_year, source)
        if entry is None:
            return True
        return entry.is_stale(max_age_days)

    def clear(self, tax_year: Optional[int] = None, source: Optional[str] = None):
        """
        Clear cache.

        Args:
            tax_year: Specific year to clear (None = all years)
            source: Specific source to clear (None = all sources)
        """
        if tax_year is None:
            # Clear all years
            for year_dir in self.cache_dir.iterdir():
                if year_dir.is_dir() and year_dir.name.isdigit():
                    if source:
                        cache_file = year_dir / f"{source}.json"
                        if cache_file.exists():
                            cache_file.unlink()
                            logger.info(f"Cleared cache: {cache_file}")
                    else:
                        import shutil
                        shutil.rmtree(year_dir)
                        logger.info(f"Cleared cache directory: {year_dir}")
        else:
            # Clear specific year
            year_dir = self._get_year_dir(tax_year)
            if source:
                cache_file = year_dir / f"{source}.json"
                if cache_file.exists():
                    cache_file.unlink()
                    logger.info(f"Cleared cache: {cache_file}")
            else:
                if year_dir.exists():
                    import shutil
                    shutil.rmtree(year_dir)
                    logger.info(f"Cleared cache directory: {year_dir}")

    def list_cached_years(self) -> List[int]:
        """
        List all tax years with cached data.

        Returns:
            List of tax years
        """
        years = []
        for year_dir in self.cache_dir.iterdir():
            if year_dir.is_dir() and year_dir.name.isdigit():
                years.append(int(year_dir.name))
        return sorted(years)

    def get_cache_info(self, tax_year: int) -> Dict[str, Any]:
        """
        Get information about cached data for a year.

        Args:
            tax_year: Tax year

        Returns:
            Dictionary with cache information
        """
        info = {
            'tax_year': tax_year,
            'sources': {},
        }

        for source in ['federal', 'california']:
            entry = self.load(tax_year, source)
            if entry:
                info['sources'][source] = {
                    'cached': True,
                    'age_days': entry.age_days(),
                    'stale': entry.is_stale(),
                    'cached_at': entry.cached_at.isoformat(),
                    'source_url': entry.source_url,
                }
            else:
                info['sources'][source] = {'cached': False}

        return info

    def get_cache_size(self) -> int:
        """
        Get total cache size in bytes.

        Returns:
            Total size in bytes
        """
        total_size = 0
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
        return total_size

    def __repr__(self) -> str:
        years = self.list_cached_years()
        return f"TaxDataCache(dir={self.cache_dir}, years={years})"
