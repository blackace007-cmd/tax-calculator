"""
Tax data fetchers for automatically retrieving tax information from official sources.

This module provides functionality to fetch tax brackets, rates, and thresholds
from IRS and California FTB websites.
"""

from .base import BaseTaxDataFetcher, FetchResult, FetchStatus

__all__ = [
    'BaseTaxDataFetcher',
    'FetchResult',
    'FetchStatus',
]

__version__ = '1.0.0'
