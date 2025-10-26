# Auto-Fetch Tax Data Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
├─────────────────────────────────────────────────────────────────┤
│  CLI Tool                  │  Python API                         │
│  $ taxcalc-update --year   │  >>> from taxcalc import           │
│    2025                    │  >>> update_tax_data(2025)         │
└────────────┬────────────────────────────┬──────────────────────┘
             │                            │
             v                            v
┌─────────────────────────────────────────────────────────────────┐
│                     Orchestrator                                 │
│  - Coordinates fetchers                                         │
│  - Manages cache                                                 │
│  - Handles errors/retries                                       │
└────────────┬──────────────────────────┬────────────────────────┘
             │                          │
    ┌────────v────────┐        ┌───────v──────────┐
    │  IRS Fetcher    │        │  CA FTB Fetcher  │
    └────────┬────────┘        └───────┬──────────┘
             │                          │
    ┌────────v────────────┐   ┌────────v──────────────┐
    │  Strategy 1: PDF    │   │  Strategy 1: HTML     │
    │  (Revenue Proc)     │   │  (Tax Rate Tables)    │
    └─────────────────────┘   └───────────────────────┘
    ┌─────────────────────┐   ┌───────────────────────┐
    │  Strategy 2: HTML   │   │  Strategy 2: PDF      │
    │  (IRS.gov tables)   │   │  (Form 540-ES)        │
    └────────┬────────────┘   └───────┬───────────────┘
             │                         │
             └─────────┬───────────────┘
                       │
                       v
             ┌─────────────────────┐
             │   Parser Layer       │
             ├─────────────────────┤
             │  - PDF Parser       │
             │  - HTML Parser      │
             │  - Table Extractor  │
             │  - Regex Matcher    │
             └─────────┬───────────┘
                       │
                       v
             ┌─────────────────────┐
             │  Validator Layer    │
             ├─────────────────────┤
             │  - Schema Check     │
             │  - Range Check      │
             │  - YoY Comparison   │
             │  - Completeness     │
             └─────────┬───────────┘
                       │
                       v
             ┌─────────────────────┐
             │   Cache Layer       │
             ├─────────────────────┤
             │  ~/.taxcalc/cache/  │
             │    ├── 2024/        │
             │    ├── 2025/        │
             │    └── 2026/        │
             └─────────┬───────────┘
                       │
                       v
             ┌─────────────────────┐
             │  Config Builder     │
             ├─────────────────────┤
             │  Transforms cached  │
             │  JSON → TaxConfig   │
             └─────────┬───────────┘
                       │
                       v
             ┌─────────────────────┐
             │   TaxCalculator     │
             │   (existing code)   │
             └─────────────────────┘
```

## Data Flow

### Fetch Flow
```
1. User Request
   │
   ├──→ Check Cache
   │    ├─ Valid? → Use cached data
   │    └─ Stale/Missing? → Continue
   │
   ├──→ Fetch from Source
   │    ├─ IRS.gov
   │    └─ FTB.ca.gov
   │
   ├──→ Parse Data
   │    ├─ Extract tables
   │    └─ Convert to JSON
   │
   ├──→ Validate Data
   │    ├─ Schema check
   │    ├─ Range check
   │    └─ Compare with previous year
   │
   ├──→ Save to Cache
   │
   └──→ Build TaxConfig
```

### Parsing Strategies

#### IRS Revenue Procedure PDF
```
PDF Download
    │
    ├─→ Extract Text (pdfplumber)
    │
    ├─→ Find Section 3 (Tax Rate Tables)
    │   │
    │   ├─→ Section 3.01: Income Tax Rates
    │   ├─→ Section 3.02: Standard Deduction
    │   ├─→ Section 3.03: AMT Exemption
    │   └─→ Section 3.04: Capital Gains Thresholds
    │
    ├─→ Parse Tables
    │   │
    │   ├─→ Regex: "Over \$(\d+) but not over \$(\d+)"
    │   └─→ Extract rates: "(\d+)%"
    │
    └─→ Structure as JSON
```

#### California FTB HTML Tables
```
HTML Fetch
    │
    ├─→ BeautifulSoup Parse
    │
    ├─→ Find Tax Rate Tables
    │   │
    │   ├─→ Look for: "Tax Rate Schedules"
    │   └─→ Extract <table> elements
    │
    ├─→ Parse with pandas
    │   │
    │   └─→ pd.read_html()
    │
    └─→ Transform to JSON
```

## Error Handling Strategy

```
┌─────────────────────────┐
│  Attempt Primary        │
│  Strategy (PDF)         │
└──────────┬──────────────┘
           │
           ├─ Success? → Continue
           │
           └─ Failure? → Try Fallback
                         │
              ┌──────────v──────────┐
              │  Attempt Fallback   │
              │  Strategy (HTML)    │
              └──────────┬──────────┘
                         │
                         ├─ Success? → Continue
                         │
                         └─ Failure? → Check Cache
                                      │
                           ┌──────────v──────────┐
                           │  Use Cached Data    │
                           │  (if available)     │
                           └──────────┬──────────┘
                                      │
                                      ├─ Available? → Warn & Use
                                      │
                                      └─ Not Available? → Use Defaults
                                                        │
                                              ┌─────────v─────────┐
                                              │  Flag for Manual  │
                                              │  Review           │
                                              └───────────────────┘
```

## Cache Structure

```
~/.taxcalc/cache/
├── metadata.json                 # Cache metadata
├── 2024/
│   ├── federal.json              # Federal tax data
│   ├── california.json           # CA tax data
│   ├── config.json               # Built TaxConfig
│   └── metadata.json             # Fetch metadata
│       ├── fetched_at
│       ├── source_urls
│       ├── validation_status
│       └── manual_overrides
├── 2025/
│   └── ...
└── 2026/
    └── ...
```

## Validation Pipeline

```
Raw Data
    │
    ├─→ Schema Validation
    │   ├─ All required fields present?
    │   ├─ Correct data types?
    │   └─ All filing statuses included?
    │
    ├─→ Range Validation
    │   ├─ Tax rates between 0% and 100%?
    │   ├─ Brackets in ascending order?
    │   └─ No negative values?
    │
    ├─→ Logical Validation
    │   ├─ No bracket gaps?
    │   ├─ No bracket overlaps?
    │   └─ Last bracket = infinity?
    │
    ├─→ Year-over-Year Comparison
    │   ├─ Brackets increased (inflation)?
    │   ├─ Rates unchanged or reasonable?
    │   └─ Flag anomalies
    │
    └─→ Manual Review Flags
        ├─ Create review list
        └─ Log warnings
```

## CLI Usage Examples

### Basic Update
```bash
# Update tax data for current year
taxcalc-update

# Update specific year
taxcalc-update --year 2025

# Update only federal or CA
taxcalc-update --year 2025 --source federal
taxcalc-update --year 2025 --source california
```

### Advanced Options
```bash
# Force re-fetch (ignore cache)
taxcalc-update --year 2025 --force

# Dry run (validate only, don't fetch)
taxcalc-update --year 2025 --validate-only

# Verbose output
taxcalc-update --year 2025 --verbose

# Show what would be fetched
taxcalc-update --year 2025 --dry-run
```

### Cache Management
```bash
# View cached data
taxcalc-cache show --year 2025

# List all cached years
taxcalc-cache list

# Clear cache
taxcalc-cache clear --year 2025
taxcalc-cache clear --all

# Export cache to file
taxcalc-cache export --year 2025 --output tax_data_2025.json
```

## Python API Examples

### Programmatic Update
```python
from taxcalc.fetchers import update_tax_data

# Update and get config
config = update_tax_data(year=2025, force=False)

# Use immediately
calc = TaxCalculator(taxpayer, income, itemized, config=config)
```

### Custom Fetching
```python
from taxcalc.fetchers import IRSFetcher, CAFTBFetcher
from taxcalc.cache import TaxDataCache

# Fetch federal data
irs = IRSFetcher(tax_year=2025)
federal_data = irs.fetch()

# Fetch CA data
ca = CAFTBFetcher(tax_year=2025)
ca_data = ca.fetch()

# Save to cache
cache = TaxDataCache()
cache.save(2025, 'federal', federal_data)
cache.save(2025, 'california', ca_data)

# Build config
config = cache.build_config(2025)
```

## Integration Points

### With Existing Code
```python
# Before: Manual constants
from taxcalc import get_tax_config_2024

# After: Auto-fetched data
from taxcalc import get_tax_config_2025  # Auto-fetches if needed
from taxcalc.fetchers import ensure_tax_data_available

# Ensure data is available
ensure_tax_data_available(2025)
config = get_tax_config_2025()
```

### Backward Compatibility
```python
# Old code still works
calc = TaxCalculator2024(taxpayer, income, itemized)

# New code with auto-fetch
calc = TaxCalculator(taxpayer, income, itemized, config=auto_config(2025))
```

## Performance Considerations

### Caching Strategy
- **First run**: Fetch + parse (~30-60 seconds)
- **Subsequent runs**: Load from cache (~0.1 seconds)
- **Cache TTL**: 90 days (configurable)

### Network Optimization
- **Retry logic**: Exponential backoff (1s, 2s, 4s)
- **Timeout**: 30 seconds per request
- **Compression**: Accept gzip encoding
- **User agent**: Identify as taxcalc bot

### Parallel Fetching
```python
# Fetch federal and CA in parallel
with ThreadPoolExecutor(max_workers=2) as executor:
    future_federal = executor.submit(fetch_irs, 2025)
    future_ca = executor.submit(fetch_ca, 2025)

    federal = future_federal.result()
    ca = future_ca.result()
```

## Security Considerations

1. **HTTPS Only**: All fetches over HTTPS
2. **Certificate Validation**: Verify SSL certificates
3. **Input Sanitization**: Validate all parsed data
4. **No Code Execution**: Parse data only, no eval()
5. **Rate Limiting**: Respect robots.txt, avoid hammering servers
6. **Cache Permissions**: Restrict cache directory to user only

## Monitoring & Logging

```python
# Logging levels
import logging

logger = logging.getLogger('taxcalc.fetchers')

# INFO: Normal operations
logger.info("Fetching IRS data for 2025...")

# WARNING: Recoverable issues
logger.warning("PDF parsing failed, falling back to HTML")

# ERROR: Fetch failures
logger.error("Failed to fetch data from IRS.gov")

# DEBUG: Detailed tracing
logger.debug("Parsed 7 tax brackets for single filers")
```

## Success Metrics

- **Accuracy**: 100% match with official data
- **Reliability**: 99% successful fetches
- **Performance**: <60s for fresh fetch, <1s for cached
- **Coverage**: All required fields populated
- **Maintenance**: Minimal manual intervention needed
