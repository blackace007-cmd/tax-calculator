# Implementation Plan: Auto-Fetch Tax Data Feature

**Branch:** `feature/auto-fetch-tax-data`
**Goal:** Automatically fetch and parse tax brackets and rates from official IRS and California FTB sources

---

## 📋 Overview

This feature will enable automatic updating of tax data from official government sources, eliminating manual updates and ensuring accuracy.

### Data Sources

#### Federal (IRS)
- **Revenue Procedures**: Published annually with inflation adjustments
  - Format: PDF documents (e.g., Revenue Procedure 2024-40 for tax year 2025)
  - URL Pattern: `https://www.irs.gov/pub/irs-drop/rp-{year}-{number}.pdf`
  - Contains: Tax brackets, standard deductions, AMT exemptions, NIIT thresholds, etc.
  - Published: Usually November/December for following tax year

- **IRS.gov Tax Pages**: HTML pages with bracket information
  - URL: `https://www.irs.gov/filing/federal-income-tax-rates-and-brackets`
  - Format: HTML tables
  - Easier to parse but may be less comprehensive

#### California (FTB)
- **Tax Rate Schedules**: Published annually
  - URL: `https://www.ftb.ca.gov/file/personal/tax-calculator-tables-rates.asp`
  - Format: HTML tables and PDF forms
  - Contains: CA tax brackets, standard deductions, SDI rates
  - Published: Late December for following tax year

- **Form 540-ES Instructions**: Contains current year data
  - URL Pattern: `https://www.ftb.ca.gov/forms/{year}/{year}-540-es-instructions.html`
  - Format: HTML/PDF

---

## 🏗️ Architecture Design

### Module Structure

```
taxcalc/
├── fetchers/
│   ├── __init__.py
│   ├── base.py              # Base fetcher class
│   ├── irs_fetcher.py       # IRS data fetcher
│   ├── ca_ftb_fetcher.py    # California FTB fetcher
│   └── parsers/
│       ├── __init__.py
│       ├── pdf_parser.py    # PDF parsing utilities
│       ├── html_parser.py   # HTML parsing utilities
│       └── validators.py    # Data validation
├── cache/
│   ├── __init__.py
│   └── tax_data_cache.py    # Cache management
└── cli/
    ├── __init__.py
    └── update_data.py       # CLI tool for updates
```

### Data Flow

```
1. User runs: `taxcalc-update --year 2025`
   ↓
2. Fetcher downloads data from IRS/FTB
   ↓
3. Parser extracts structured data
   ↓
4. Validator checks data integrity
   ↓
5. Cache stores validated data
   ↓
6. TaxConfig builder creates config from cached data
```

---

## 🔧 Implementation Details

### Phase 1: Foundation (Week 1)

#### 1.1 Base Fetcher Class
```python
# taxcalc/fetchers/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
import requests
from datetime import datetime

@dataclass
class FetchResult:
    """Result of fetching tax data"""
    tax_year: int
    source: str
    data: Dict[str, Any]
    fetched_at: datetime
    success: bool
    error: Optional[str] = None

class BaseTaxDataFetcher(ABC):
    """Base class for tax data fetchers"""

    def __init__(self, tax_year: int, cache_dir: str = None):
        self.tax_year = tax_year
        self.cache_dir = cache_dir or "~/.taxcalc/cache"

    @abstractmethod
    def fetch(self) -> FetchResult:
        """Fetch tax data from source"""
        pass

    @abstractmethod
    def parse(self, raw_data: bytes) -> Dict[str, Any]:
        """Parse raw data into structured format"""
        pass

    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate parsed data"""
        pass
```

#### 1.2 HTTP Utilities
```python
# Common utilities for fetching
def fetch_url(url: str, timeout: int = 30) -> bytes:
    """Fetch content from URL with error handling"""

def download_pdf(url: str) -> bytes:
    """Download PDF file"""

def fetch_html(url: str) -> str:
    """Fetch HTML content"""
```

### Phase 2: IRS Data Fetcher (Week 2)

#### 2.1 Revenue Procedure Parser
```python
# taxcalc/fetchers/irs_fetcher.py

class IRSRevenueProcedureFetcher(BaseTaxDataFetcher):
    """
    Fetches data from IRS Revenue Procedures

    Strategy:
    1. Try to download Revenue Procedure PDF
    2. Extract text using PyPDF2 or pdfplumber
    3. Parse tables using regex patterns
    4. Fall back to HTML scraping if PDF fails
    """

    REVENUE_PROCEDURE_MAP = {
        2024: ("rp-23-34", "https://www.irs.gov/pub/irs-drop/rp-23-34.pdf"),
        2025: ("rp-24-40", "https://www.irs.gov/pub/irs-drop/rp-24-40.pdf"),
        2026: ("rp-25-32", "https://www.irs.gov/pub/irs-drop/rp-25-32.pdf"),
    }

    def fetch(self) -> FetchResult:
        """Download and parse Revenue Procedure"""

    def _parse_pdf(self, pdf_bytes: bytes) -> Dict:
        """Extract tax data from PDF"""
        # Parse sections:
        # - Tax rate tables (Section 3.01)
        # - Standard deduction (Section 3.02)
        # - AMT exemption (Section 3.03)
        # - Capital gains thresholds (Section 3.04)

    def _parse_tax_brackets(self, text: str) -> Dict:
        """Extract tax brackets from text"""
        # Look for patterns like:
        # "If taxable income is:"
        # "Over $X but not over $Y ... $Z plus X% of the amount over $A"
```

#### 2.2 HTML Fallback Parser
```python
class IRSHTMLFetcher(BaseTaxDataFetcher):
    """
    Fallback: Scrape IRS website HTML tables

    URL: https://www.irs.gov/filing/federal-income-tax-rates-and-brackets
    """

    def fetch(self) -> FetchResult:
        """Scrape HTML tables from IRS website"""

    def _parse_table(self, table_html) -> Dict:
        """Extract bracket data from HTML table"""
```

### Phase 3: California FTB Fetcher (Week 3)

#### 3.1 FTB Data Fetcher
```python
# taxcalc/fetchers/ca_ftb_fetcher.py

class CAFTBFetcher(BaseTaxDataFetcher):
    """
    Fetches California tax data from FTB

    Strategy:
    1. Fetch tax rate schedules from FTB website
    2. Parse HTML tables
    3. Extract SDI rate from Form 540-ES instructions
    4. Validate against previous year's data
    """

    TAX_RATE_URLS = {
        2024: "https://www.ftb.ca.gov/file/personal/tax-calculator-tables-rates.asp",
        2025: "https://www.ftb.ca.gov/file/personal/tax-calculator-tables-rates.asp",
    }

    def fetch(self) -> FetchResult:
        """Fetch CA tax data"""

    def _parse_tax_table(self, html: str) -> Dict:
        """Parse CA tax rate tables"""
        # Extract:
        # - Tax brackets by filing status
        # - Standard deductions
        # - Mental Health Services Tax threshold

    def _fetch_sdi_rate(self) -> float:
        """Fetch SDI rate from Form 540-ES or CA website"""
```

### Phase 4: Parsers & Validators (Week 2-3)

#### 4.1 PDF Parser
```python
# taxcalc/fetchers/parsers/pdf_parser.py

class PDFParser:
    """Parse PDF documents"""

    def extract_text(self, pdf_bytes: bytes) -> str:
        """Extract all text from PDF"""
        # Use pdfplumber for better table extraction

    def extract_tables(self, pdf_bytes: bytes) -> List[pd.DataFrame]:
        """Extract tables from PDF"""

    def find_section(self, text: str, section_name: str) -> str:
        """Find specific section in PDF text"""
```

#### 4.2 HTML Parser
```python
# taxcalc/fetchers/parsers/html_parser.py

class HTMLTableParser:
    """Parse HTML tables"""

    def extract_tables(self, html: str) -> List[pd.DataFrame]:
        """Extract all tables from HTML"""
        # Use BeautifulSoup + pandas

    def find_tax_bracket_table(self, tables: List) -> pd.DataFrame:
        """Identify tax bracket table"""
```

#### 4.3 Validators
```python
# taxcalc/fetchers/parsers/validators.py

class TaxDataValidator:
    """Validate fetched tax data"""

    def validate_brackets(self, brackets: Dict) -> bool:
        """Ensure brackets are valid"""
        # Check:
        # - All filing statuses present
        # - Brackets in ascending order
        # - Rates between 0 and 1
        # - No gaps or overlaps

    def validate_against_previous_year(self, new_data: Dict, old_data: Dict) -> List[str]:
        """Compare with previous year, flag anomalies"""
        # Flag if:
        # - Standard deduction decreased
        # - Brackets decreased (unlikely)
        # - Rates changed significantly

    def validate_completeness(self, data: Dict) -> List[str]:
        """Check all required fields present"""
```

### Phase 5: Cache System (Week 4)

#### 5.1 Cache Manager
```python
# taxcalc/cache/tax_data_cache.py

class TaxDataCache:
    """
    Cache tax data locally

    Directory structure:
    ~/.taxcalc/cache/
    ├── 2024/
    │   ├── federal.json
    │   ├── california.json
    │   └── metadata.json
    ├── 2025/
    │   ├── federal.json
    │   ├── california.json
    │   └── metadata.json
    """

    def save(self, tax_year: int, source: str, data: Dict):
        """Save fetched data to cache"""

    def load(self, tax_year: int, source: str) -> Optional[Dict]:
        """Load cached data"""

    def is_stale(self, tax_year: int, max_age_days: int = 90) -> bool:
        """Check if cached data is stale"""

    def clear(self, tax_year: Optional[int] = None):
        """Clear cache"""
```

#### 5.2 Config Builder from Cache
```python
# taxcalc/cache/config_builder.py

class TaxConfigBuilder:
    """Build TaxConfig from cached data"""

    def build_from_cache(self, tax_year: int) -> TaxConfig:
        """Create TaxConfig from cached federal + CA data"""

    def merge_sources(self, federal: Dict, california: Dict) -> Dict:
        """Merge federal and CA data"""
```

### Phase 6: CLI Tool (Week 4)

#### 6.1 Update Command
```python
# taxcalc/cli/update_data.py

import click

@click.command()
@click.option('--year', type=int, help='Tax year to fetch')
@click.option('--source', type=click.Choice(['federal', 'california', 'both']),
              default='both')
@click.option('--force', is_flag=True, help='Force re-fetch even if cached')
@click.option('--validate-only', is_flag=True, help='Only validate existing cache')
def update(year, source, force, validate_only):
    """Update tax data from official sources"""

    if not year:
        year = datetime.now().year

    if validate_only:
        # Validate cached data
        pass
    else:
        # Fetch new data
        if source in ['federal', 'both']:
            fetch_irs_data(year, force)
        if source in ['california', 'both']:
            fetch_ca_data(year, force)

    # Generate updated constants file
    generate_constants_file(year)

@click.command()
@click.option('--year', type=int)
def show_cache(year):
    """Show cached tax data"""

@click.command()
def list_available():
    """List available tax years in cache"""
```

Entry point in `setup.py`:
```python
entry_points={
    'console_scripts': [
        'taxcalc-update=taxcalc.cli.update_data:update',
        'taxcalc-cache=taxcalc.cli.update_data:show_cache',
    ],
}
```

---

## 📊 Data Structure

### Standardized JSON Format

```json
{
  "tax_year": 2025,
  "source": "irs",
  "fetched_at": "2025-10-26T12:00:00Z",
  "federal": {
    "tax_brackets": {
      "single": [
        {"upper_limit": 11925, "rate": 0.10},
        {"upper_limit": 48475, "rate": 0.12},
        {"upper_limit": 103350, "rate": 0.22},
        {"upper_limit": null, "rate": 0.37}
      ],
      "married_joint": [...],
      "married_separate": [...],
      "head_of_household": [...]
    },
    "standard_deductions": {
      "single": 15000,
      "married_joint": 30000,
      "married_separate": 15000,
      "head_of_household": 22500
    },
    "amt": {
      "exemption": {
        "single": 85700,
        "married_joint": 133300
      },
      "phaseout_start": {
        "single": 609350,
        "married_joint": 1218700
      }
    },
    "ltcg_brackets": {...},
    "niit_thresholds": {...},
    "medicare_thresholds": {...}
  },
  "california": {
    "tax_brackets": {...},
    "standard_deductions": {...},
    "sdi_rate": 0.012,
    "mental_health_tax": {
      "threshold": 1000000,
      "rate": 0.01
    }
  }
}
```

---

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/test_fetchers.py
def test_irs_fetcher_parses_revenue_procedure():
    """Test parsing of Revenue Procedure PDF"""

def test_ca_fetcher_parses_html_tables():
    """Test parsing of CA FTB HTML tables"""

def test_validator_catches_invalid_brackets():
    """Test validation of tax brackets"""
```

### Integration Tests
```python
# tests/test_integration.py
def test_full_fetch_and_build_config():
    """Test fetching data and building TaxConfig"""

def test_cache_system():
    """Test caching and retrieval"""
```

### Mock Data
- Store example Revenue Procedure PDFs
- Store example HTML pages
- Test with known good data

---

## 🚀 Rollout Plan

### Week 1: Foundation
- ✅ Create base fetcher class
- ✅ Set up HTTP utilities
- ✅ Create cache directory structure
- ✅ Write validators

### Week 2: IRS Fetcher
- ✅ Implement PDF parser
- ✅ Implement Revenue Procedure parser
- ✅ Implement HTML fallback parser
- ✅ Test with actual Revenue Procedures

### Week 3: CA FTB Fetcher
- ✅ Implement HTML table parser
- ✅ Implement FTB scraper
- ✅ Extract SDI rate logic
- ✅ Test with actual FTB pages

### Week 4: Integration
- ✅ Build cache system
- ✅ Create CLI tool
- ✅ Write comprehensive tests
- ✅ Update documentation

### Week 5: Polish & Release
- ✅ Add error handling and retries
- ✅ Add logging
- ✅ Create user guide
- ✅ Merge to main branch

---

## 📦 Dependencies

Add to `requirements.txt`:
```
# For fetching
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.0.0

# For PDF parsing
pdfplumber>=0.10.0
PyPDF2>=3.0.0

# For CLI
click>=8.1.0

# For data validation
pandas>=2.0.0  # Already included

# For caching
appdirs>=1.4.4  # For cross-platform cache directories
```

---

## 🔒 Error Handling

### Failure Scenarios

1. **Network failures**: Retry with exponential backoff
2. **PDF parsing failures**: Fall back to HTML scraping
3. **Invalid data**: Keep previous year's data, warn user
4. **Missing data**: Mark fields as "needs_manual_update"
5. **Cache corruption**: Re-fetch from source

### Graceful Degradation
```python
# If fetch fails, use cached data
# If cache is stale, warn user but still use it
# If no cache, use hardcoded defaults
```

---

## 📝 Documentation Updates

### User Documentation
- `FETCHING_DATA.md` - Guide for updating tax data
- Update `README.md` with auto-fetch feature
- Add troubleshooting guide

### Developer Documentation
- Document fetcher API
- Document cache structure
- Add contribution guide for adding new data sources

---

## 🎯 Success Criteria

1. ✅ Successfully fetch 2024, 2025, 2026 data from IRS
2. ✅ Successfully fetch 2024, 2025 data from CA FTB
3. ✅ Parse all required fields (brackets, deductions, thresholds)
4. ✅ Validate data matches known correct values
5. ✅ CLI tool works for non-technical users
6. ✅ Cache system prevents redundant fetches
7. ✅ Comprehensive error handling
8. ✅ All tests pass with >90% coverage

---

## 🔮 Future Enhancements

1. **Additional States**: Extend to NY, TX, etc.
2. **Automatic Updates**: Cron job to check for new data
3. **Web Dashboard**: View cached data in browser
4. **Data Diff Tool**: Compare years side-by-side
5. **Historical Data**: Archive all previous years
6. **API Mode**: Serve tax data via REST API
7. **Notification System**: Alert when new tax year data available

---

## ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Website structure changes | High | Version parsers, maintain multiple strategies |
| PDF format changes | Medium | OCR fallback, manual update option |
| Data not yet available | Low | Use previous year + inflation estimate |
| Parsing errors | Medium | Comprehensive validation, manual review flag |
| Legal/scraping issues | Low | Use only public data, respect robots.txt |

---

## 📞 Open Questions

1. Should we parse all historical years or just current + next?
2. Should we provide a web UI or CLI only?
3. How to handle mid-year tax law changes?
4. Should we fetch quarterly (for estimated tax updates)?
5. Should we include self-employment tax tables?

---

This plan provides a comprehensive roadmap for implementing automatic tax data fetching while maintaining reliability and user-friendliness.
