"""
Cache management for fetched tax data.

This module provides functionality to cache tax data locally to avoid
repeated fetching from sources.
"""

from .tax_data_cache import TaxDataCache, CacheEntry

__all__ = [
    'TaxDataCache',
    'CacheEntry',
]
