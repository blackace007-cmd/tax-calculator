"""
Tests for tax data validators.
"""

import pytest
from taxcalc.fetchers.parsers.validators import TaxDataValidator, ValidationError


class TestTaxDataValidator:
    """Tests for TaxDataValidator"""

    def test_valid_federal_brackets(self):
        """Test validation of valid federal tax brackets"""
        validator = TaxDataValidator(tax_year=2025)

        data = {
            'tax_brackets': {
                'single': [
                    (11925, 0.10),
                    (48475, 0.12),
                    (103350, 0.22),
                    (float('inf'), 0.37)
                ],
                'married_joint': [
                    (23850, 0.10),
                    (96950, 0.12),
                    (float('inf'), 0.37)
                ],
                'married_separate': [
                    (11925, 0.10),
                    (float('inf'), 0.37)
                ],
                'head_of_household': [
                    (17000, 0.10),
                    (float('inf'), 0.37)
                ]
            },
            'standard_deductions': {
                'single': 15000,
                'married_joint': 30000,
                'married_separate': 15000,
                'head_of_household': 22500
            },
            'ltcg_brackets': {
                'single': [
                    (48350, 0.00),
                    (533400, 0.15),
                    (float('inf'), 0.20)
                ],
                'married_joint': [
                    (96700, 0.00),
                    (float('inf'), 0.20)
                ],
                'married_separate': [
                    (48350, 0.00),
                    (float('inf'), 0.20)
                ],
                'head_of_household': [
                    (64750, 0.00),
                    (float('inf'), 0.20)
                ]
            },
            'amt_exemption': {
                'single': 85700,
                'married_joint': 133300,
                'married_separate': 66650,
                'head_of_household': 85700
            },
            'amt_phaseout_start': {
                'single': 609350,
                'married_joint': 1218700,
                'married_separate': 609350,
                'head_of_household': 609350
            },
            'niit_thresholds': {
                'single': 200000,
                'married_joint': 250000,
                'married_separate': 125000,
                'head_of_household': 200000
            },
            'medicare_thresholds': {
                'single': 200000,
                'married_joint': 250000,
                'married_separate': 125000,
                'head_of_household': 200000
            }
        }

        is_valid, errors = validator.validate_federal_data(data)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_filing_status(self):
        """Test validation fails when filing status is missing"""
        validator = TaxDataValidator(tax_year=2025)

        data = {
            'tax_brackets': {
                'single': [(float('inf'), 0.10)],
                # Missing married_joint, married_separate, head_of_household
            },
            'standard_deductions': {
                'single': 15000,
                'married_joint': 30000,
                'married_separate': 15000,
                'head_of_household': 22500
            },
            'ltcg_brackets': {},
            'amt_exemption': {},
            'amt_phaseout_start': {},
            'niit_thresholds': {},
            'medicare_thresholds': {}
        }

        is_valid, errors = validator.validate_federal_data(data)
        assert is_valid is False
        assert any('married_joint' in err for err in errors)

    def test_invalid_tax_rate(self):
        """Test validation fails with invalid tax rate"""
        validator = TaxDataValidator(tax_year=2025)

        data = {
            'tax_brackets': {
                'single': [
                    (10000, 1.50),  # Invalid: rate > 1
                    (float('inf'), 0.37)
                ],
                'married_joint': [(float('inf'), 0.10)],
                'married_separate': [(float('inf'), 0.10)],
                'head_of_household': [(float('inf'), 0.10)]
            },
            'standard_deductions': {
                'single': 15000,
                'married_joint': 30000,
                'married_separate': 15000,
                'head_of_household': 22500
            },
            'ltcg_brackets': {},
            'amt_exemption': {},
            'amt_phaseout_start': {},
            'niit_thresholds': {},
            'medicare_thresholds': {}
        }

        is_valid, errors = validator.validate_federal_data(data)
        assert is_valid is False
        assert any('invalid rate' in err.lower() for err in errors)

    def test_brackets_not_ascending(self):
        """Test validation fails when brackets not in ascending order"""
        validator = TaxDataValidator(tax_year=2025)

        data = {
            'tax_brackets': {
                'single': [
                    (50000, 0.10),
                    (30000, 0.12),  # Wrong order
                    (float('inf'), 0.37)
                ],
                'married_joint': [(float('inf'), 0.10)],
                'married_separate': [(float('inf'), 0.10)],
                'head_of_household': [(float('inf'), 0.10)]
            },
            'standard_deductions': {
                'single': 15000,
                'married_joint': 30000,
                'married_separate': 15000,
                'head_of_household': 22500
            },
            'ltcg_brackets': {},
            'amt_exemption': {},
            'amt_phaseout_start': {},
            'niit_thresholds': {},
            'medicare_thresholds': {}
        }

        is_valid, errors = validator.validate_federal_data(data)
        assert is_valid is False
        assert any('not greater than' in err for err in errors)

    def test_standard_deduction_ratio(self):
        """Test validation warns about unusual standard deduction ratios"""
        validator = TaxDataValidator(tax_year=2025)

        data = {
            'tax_brackets': {},
            'standard_deductions': {
                'single': 15000,
                'married_joint': 50000,  # Unusual ratio (3.33x instead of ~2x)
                'married_separate': 15000,
                'head_of_household': 22500
            },
            'ltcg_brackets': {},
            'amt_exemption': {},
            'amt_phaseout_start': {},
            'niit_thresholds': {},
            'medicare_thresholds': {}
        }

        is_valid, errors = validator.validate_federal_data(data)
        assert is_valid is False
        assert any('ratio' in err.lower() for err in errors)

    def test_valid_california_data(self):
        """Test validation of valid California data"""
        validator = TaxDataValidator(tax_year=2025)

        data = {
            'tax_brackets': {
                'single': [
                    (10756, 0.01),
                    (25499, 0.02),
                    (float('inf'), 0.123)
                ],
                'married_joint': [
                    (21512, 0.01),
                    (float('inf'), 0.123)
                ],
                'married_separate': [
                    (10756, 0.01),
                    (float('inf'), 0.123)
                ],
                'head_of_household': [
                    (21527, 0.01),
                    (float('inf'), 0.123)
                ]
            },
            'standard_deductions': {
                'single': 5540,
                'married_joint': 11080,
                'married_separate': 5540,
                'head_of_household': 11080
            },
            'sdi_rate': 0.012,
            'mental_health_tax': {
                'threshold': 1000000,
                'rate': 0.01
            }
        }

        is_valid, errors = validator.validate_california_data(data)
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_sdi_rate(self):
        """Test validation fails with invalid SDI rate"""
        validator = TaxDataValidator(tax_year=2025)

        data = {
            'tax_brackets': {
                'single': [(float('inf'), 0.01)],
                'married_joint': [(float('inf'), 0.01)],
                'married_separate': [(float('inf'), 0.01)],
                'head_of_household': [(float('inf'), 0.01)]
            },
            'standard_deductions': {
                'single': 5540,
                'married_joint': 11080,
                'married_separate': 5540,
                'head_of_household': 11080
            },
            'sdi_rate': 0.10,  # 10% is too high
            'mental_health_tax': {
                'threshold': 1000000,
                'rate': 0.01
            }
        }

        is_valid, errors = validator.validate_california_data(data)
        assert is_valid is False
        assert any('SDI rate' in err for err in errors)

    def test_year_over_year_comparison(self):
        """Test year-over-year comparison"""
        validator = TaxDataValidator(tax_year=2025)

        current_data = {
            'standard_deductions': {
                'single': 15000,
                'married_joint': 30000
            }
        }

        previous_data = {
            'standard_deductions': {
                'single': 14600,
                'married_joint': 29200
            }
        }

        warnings = validator.compare_with_previous_year(
            current_data, previous_data, 'federal'
        )

        # Should not have warnings for reasonable increases
        assert len(warnings) == 0

    def test_year_over_year_decrease_warning(self):
        """Test warning when values decrease year-over-year"""
        validator = TaxDataValidator(tax_year=2025)

        current_data = {
            'standard_deductions': {
                'single': 14000,  # Decreased from previous year
                'married_joint': 30000
            }
        }

        previous_data = {
            'standard_deductions': {
                'single': 15000,
                'married_joint': 29200
            }
        }

        warnings = validator.compare_with_previous_year(
            current_data, previous_data, 'federal'
        )

        assert len(warnings) > 0
        assert any('decreased' in warn.lower() for warn in warnings)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
