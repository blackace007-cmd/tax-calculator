# Tax Calculator 2024

A comprehensive Python package for calculating Federal and California state taxes for tax year 2024/2025. This package provides accurate tax calculations including itemized deductions, capital gains, Alternative Minimum Tax (AMT), Net Investment Income Tax (NIIT), and California-specific taxes.

## Features

- **Complete Federal Tax Calculation**
  - Progressive tax brackets for all filing statuses
  - Long-term capital gains with preferential rates (0%, 15%, 20%)
  - Short-term capital gains and qualified dividends
  - Alternative Minimum Tax (AMT) with ISO exercise support
  - Net Investment Income Tax (3.8% NIIT)
  - Additional Medicare Tax (0.9%)

- **California State Tax Calculation**
  - Progressive tax rates (1% to 12.3%)
  - Mental Health Services Tax (1% on income over $1M)
  - State Disability Insurance (SDI) - 2024 and 2025 rates
  - Proper handling of capital gains as ordinary income

- **Itemized Deductions**
  - Medical and dental expenses (7.5% AGI floor)
  - State and Local Tax (SALT) deduction with $10,000 cap
  - Mortgage interest
  - Charitable contributions with AGI limits
  - Donor-Advised Fund (DAF) contribution support

- **Smart Deduction Selection**
  - Automatic comparison of standard vs itemized deductions
  - Additional deductions for age 65+ and blind taxpayers

## Installation

### Using Conda (Recommended)

This project uses conda for environment management. If you haven't set up conda yet, see `/home/azhar/CONDA_GUIDE.md`.

```bash
# Activate the datascience environment
conda activate datascience

# Install the package
cd /home/azhar/tax-calculator
pip install -e .
```

### Using environment.yml

To create a dedicated environment for this project:

```bash
# Create environment from file
conda env create -f environment.yml

# Activate it
conda activate tax-calculator

# Install the package
pip install -e .
```

## Quick Start

### Basic Usage in Python

```python
from taxcalc import (
    FilingStatus,
    TaxpayerInfo,
    IncomeData,
    ItemizedDeductions,
    TaxCalculator2024
)

# Define taxpayer information
taxpayer = TaxpayerInfo(
    filing_status=FilingStatus.MARRIED_JOINT,
    age_primary=45,
    age_spouse=43
)

# Define income sources
income = IncomeData(
    wages_w2=400000,
    long_term_capital_gains=100000,
    qualified_dividends=15000
)

# Define itemized deductions
itemized = ItemizedDeductions(
    state_local_income_taxes=25000,
    mortgage_interest=35000,
    cash_contributions_50pct_orgs=40000
)

# Calculate taxes
calculator = TaxCalculator2024(taxpayer, income, itemized)
results = calculator.calculate_all_taxes()

# Print detailed report
print(calculator.generate_summary_report(results))
```

### Usage in Jupyter Lab

See the comprehensive example notebook at `examples/tax_analysis_example.ipynb` for:
- Multiple calculation scenarios
- Comparison analyses
- Visualization examples
- Custom analysis functions

To launch the example notebook:

```bash
# Activate datascience environment
conda activate datascience

# Launch Jupyter
cd /home/azhar/tax-calculator
jupyter lab examples/tax_analysis_example.ipynb
```

**Jupyter Kernel**: Select "Data Science (conda)" kernel in the notebook.

## Package Structure

```
tax-calculator/
├── taxcalc/                    # Main package
│   ├── __init__.py            # Package initialization
│   ├── models.py              # Data models (TaxpayerInfo, IncomeData, etc.)
│   ├── constants.py           # Tax rates, brackets, and thresholds
│   └── calculator.py          # Main calculator implementation
├── examples/                   # Example notebooks and scripts
│   └── tax_analysis_example.ipynb
├── tests/                      # Unit tests (future)
├── setup.py                    # Package installation configuration
└── README.md                   # This file
```

## API Reference

### Core Classes

#### `TaxpayerInfo`
Basic taxpayer information and filing status.

**Fields:**
- `filing_status`: FilingStatus enum (SINGLE, MARRIED_JOINT, MARRIED_SEPARATE, HEAD_OF_HOUSEHOLD)
- `age_primary`: Age of primary taxpayer
- `age_spouse`: Age of spouse (default: 0)
- `is_blind_primary`: Whether primary taxpayer is blind (default: False)
- `is_blind_spouse`: Whether spouse is blind (default: False)
- `num_dependents`: Number of dependents (default: 0)

#### `IncomeData`
All income sources.

**Fields:**
- `wages_w2`: W-2 wage income
- `interest_income`: Interest income
- `qualified_dividends`: Qualified dividends
- `ordinary_dividends`: Ordinary dividends
- `short_term_capital_gains`: Short-term capital gains
- `long_term_capital_gains`: Long-term capital gains
- `self_employment_income`: Self-employment income
- `rental_income`: Rental income
- `other_income`: Other income
- `tax_exempt_interest`: Tax-exempt interest
- `private_activity_bond_interest`: Private activity bond interest (affects AMT)

#### `ItemizedDeductions`
Itemized deduction categories for Schedule A.

**Fields:**
- `medical_dental_expenses`: Medical and dental expenses
- `state_local_income_taxes`: State and local income taxes
- `real_estate_taxes`: Real estate taxes
- `personal_property_taxes`: Personal property taxes
- `mortgage_interest`: Home mortgage interest
- `mortgage_points`: Mortgage points
- `cash_contributions_50pct_orgs`: Cash contributions to public charities
- `cash_contributions_other`: Cash contributions to other organizations
- `noncash_contributions`: Noncash contributions (appreciated property)
- `donor_advised_fund_contributions`: DAF contributions
- `casualty_theft_losses`: Casualty and theft losses
- `gambling_losses`: Gambling losses (limited to winnings)

#### `AMTAdjustments`
AMT-specific adjustments and preference items.

**Fields:**
- `iso_bargain_element`: ISO exercise bargain element (FMV - exercise price)
- `depreciation_adjustment`: Depreciation adjustments
- `tax_refunds`: Tax refunds (negative adjustment)
- `investment_interest_adjustment`: Investment interest adjustment
- `passive_activity_adjustment`: Passive activity adjustment

#### `TaxCalculator2024`
Main calculator class.

**Methods:**
- `calculate_all_taxes()`: Returns TaxResults with complete tax calculation
- `generate_summary_report(results)`: Returns formatted text report

**Parameters:**
- `taxpayer_info`: TaxpayerInfo object
- `income`: IncomeData object
- `itemized_deductions`: ItemizedDeductions object
- `amt_adjustments`: AMTAdjustments object (optional)
- `use_2025_sdi_rate`: Use 2025 CA SDI rate instead of 2024 (default: False)

#### `TaxResults`
Comprehensive tax calculation results.

**Key Fields:**
- `gross_income`: Total gross income
- `agi`: Adjusted Gross Income
- `taxable_income`: Taxable income after deductions
- `federal_income_tax`: Federal regular income tax
- `capital_gains_tax`: Federal capital gains tax
- `amt_owed`: Alternative Minimum Tax owed
- `niit_owed`: Net Investment Income Tax owed
- `california_income_tax`: California income tax
- `total_tax_liability`: Combined federal and California tax
- `effective_total_rate`: Overall effective tax rate

## Tax Year 2024 Constants

All calculations are based on official IRS and California FTB guidance for tax year 2024:

### Federal
- Standard deduction: $14,600 (Single), $29,200 (Married Joint)
- SALT cap: $10,000
- AMT exemption: $85,700 (Single), $133,300 (Married Joint)
- NIIT threshold: $200,000 (Single), $250,000 (Married Joint)
- Capital gains brackets: 0% / 15% / 20%

### California
- Standard deduction: $5,540 (Single), $11,080 (Married Joint)
- SDI rate: 1.1% (2024), 1.2% (2025)
- Mental Health Tax: 1% on income over $1,000,000
- Top marginal rate: 12.3%

## Examples

### Example 1: Simple Calculation

```python
from taxcalc import *

taxpayer = TaxpayerInfo(filing_status=FilingStatus.SINGLE, age_primary=30)
income = IncomeData(wages_w2=150000)
itemized = ItemizedDeductions()

calc = TaxCalculator2024(taxpayer, income, itemized)
results = calc.calculate_all_taxes()

print(f"Total Tax: ${results.total_tax_liability:,.2f}")
print(f"Effective Rate: {results.effective_total_rate*100:.2f}%")
```

### Example 2: With Capital Gains and Deductions

```python
taxpayer = TaxpayerInfo(
    filing_status=FilingStatus.MARRIED_JOINT,
    age_primary=50,
    age_spouse=48
)

income = IncomeData(
    wages_w2=300000,
    long_term_capital_gains=75000,
    qualified_dividends=10000
)

itemized = ItemizedDeductions(
    state_local_income_taxes=20000,  # Will be capped at $10,000
    mortgage_interest=30000,
    cash_contributions_50pct_orgs=25000
)

calc = TaxCalculator2024(taxpayer, income, itemized)
results = calc.calculate_all_taxes()
print(calc.generate_summary_report(results))
```

### Example 3: AMT Scenario with ISO Exercise

```python
taxpayer = TaxpayerInfo(filing_status=FilingStatus.SINGLE, age_primary=35)

income = IncomeData(
    wages_w2=250000,
    long_term_capital_gains=50000
)

itemized = ItemizedDeductions(
    state_local_income_taxes=30000,
    mortgage_interest=20000
)

amt_adj = AMTAdjustments(
    iso_bargain_element=200000  # Large ISO exercise
)

calc = TaxCalculator2024(taxpayer, income, itemized, amt_adj)
results = calc.calculate_all_taxes()

print(f"Regular Tax: ${results.total_federal_regular_tax:,.2f}")
print(f"AMT Owed: ${results.amt_owed:,.2f}")
print(f"Total Federal Tax: ${results.total_federal_tax:,.2f}")
```

## Important Notes

1. **Above-the-Line Deductions**: This calculator assumes pre-tax contributions (401k, Traditional IRA, HSA) have already been subtracted from W-2 wages. If not, subtract them from `wages_w2` before input.

2. **SALT Deduction Cap**: State and local tax deductions are capped at $10,000 ($5,000 if married filing separately) for federal taxes. The calculator automatically applies this cap.

3. **California Capital Gains**: California taxes all capital gains as ordinary income at regular progressive rates, unlike federal treatment.

4. **AMT Complexity**: For complex AMT situations involving multiple adjustment items, consult a tax professional.

5. **Charitable Contribution Limits**:
   - Cash: 60% of AGI
   - Property: 30% of AGI
   - Excess can be carried forward 5 years (not implemented in this version)

6. **Medical Expense Floor**: Only medical expenses exceeding 7.5% of AGI are deductible.

## Accuracy and Compliance

This calculator implements:
- IRS Revenue Procedure 2023-34 (2024 inflation adjustments)
- California Franchise Tax Board 2024 guidance
- Current federal tax law including TCJA provisions

**Disclaimer**: This calculator is for informational and planning purposes only. Always consult with a qualified tax professional for tax planning and filing. Tax laws are complex and individual circumstances vary.

## Contributing

Contributions are welcome! Areas for enhancement:
- Additional state tax calculations
- Self-employment tax calculations
- Retirement contribution optimization
- Multi-year tax planning
- Additional visualizations

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- Open an issue on GitHub
- Check the example notebook for common use cases
- Review the API documentation above

## Version History

- **1.0.0** (October 2025): Initial release
  - Federal tax calculation
  - California tax calculation
  - AMT, NIIT, Additional Medicare Tax
  - Itemized deductions with all major categories
  - Jupyter notebook examples
