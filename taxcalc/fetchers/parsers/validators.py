"""
Validators for tax data.

This module provides validation logic to ensure fetched tax data
is complete, correct, and reasonable.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from ...models import FilingStatus

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised when validation fails"""
    pass


class TaxDataValidator:
    """
    Validator for tax data fetched from sources.

    Performs multiple levels of validation:
    1. Schema validation - ensure required fields present
    2. Range validation - ensure values are reasonable
    3. Logical validation - ensure data makes sense
    4. Year-over-year validation - compare with previous year
    """

    # Expected fields in tax data
    REQUIRED_FEDERAL_FIELDS = [
        'tax_brackets',
        'standard_deductions',
        'ltcg_brackets',
        'amt_exemption',
        'amt_phaseout_start',
        'niit_thresholds',
        'medicare_thresholds',
    ]

    REQUIRED_CALIFORNIA_FIELDS = [
        'tax_brackets',
        'standard_deductions',
        'sdi_rate',
        'mental_health_tax',
    ]

    def __init__(self, tax_year: int):
        """
        Initialize validator.

        Args:
            tax_year: Tax year being validated
        """
        self.tax_year = tax_year

    def validate_federal_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate federal tax data.

        Args:
            data: Federal tax data dictionary

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # 1. Schema validation
        errors.extend(self._validate_schema(data, self.REQUIRED_FEDERAL_FIELDS))

        # 2. Validate tax brackets
        if 'tax_brackets' in data:
            errors.extend(self._validate_tax_brackets(data['tax_brackets'], 'federal'))

        # 3. Validate standard deductions
        if 'standard_deductions' in data:
            errors.extend(self._validate_standard_deductions(data['standard_deductions']))

        # 4. Validate capital gains brackets
        if 'ltcg_brackets' in data:
            errors.extend(self._validate_ltcg_brackets(data['ltcg_brackets']))

        # 5. Validate AMT data
        if 'amt_exemption' in data:
            errors.extend(self._validate_amt_data(data))

        # 6. Validate thresholds
        if 'niit_thresholds' in data:
            errors.extend(self._validate_thresholds(data['niit_thresholds'], 'NIIT'))

        if 'medicare_thresholds' in data:
            errors.extend(self._validate_thresholds(data['medicare_thresholds'], 'Medicare'))

        is_valid = len(errors) == 0
        if not is_valid:
            logger.error(f"Federal data validation failed with {len(errors)} errors")

        return is_valid, errors

    def validate_california_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate California tax data.

        Args:
            data: California tax data dictionary

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # 1. Schema validation
        errors.extend(self._validate_schema(data, self.REQUIRED_CALIFORNIA_FIELDS))

        # 2. Validate tax brackets
        if 'tax_brackets' in data:
            errors.extend(self._validate_tax_brackets(data['tax_brackets'], 'california'))

        # 3. Validate standard deductions
        if 'standard_deductions' in data:
            errors.extend(self._validate_standard_deductions(data['standard_deductions']))

        # 4. Validate SDI rate
        if 'sdi_rate' in data:
            sdi_rate = data['sdi_rate']
            if not (0 < sdi_rate < 0.05):  # Expect between 0% and 5%
                errors.append(f"SDI rate {sdi_rate*100:.1f}% is outside expected range (0%-5%)")

        # 5. Validate Mental Health Tax
        if 'mental_health_tax' in data:
            mht = data['mental_health_tax']
            if 'threshold' not in mht or 'rate' not in mht:
                errors.append("Mental Health Tax missing threshold or rate")
            elif mht['threshold'] < 500000 or mht['threshold'] > 2000000:
                errors.append(f"Mental Health Tax threshold ${mht['threshold']:,} seems unusual")

        is_valid = len(errors) == 0
        if not is_valid:
            logger.error(f"California data validation failed with {len(errors)} errors")

        return is_valid, errors

    def _validate_schema(self, data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate that all required fields are present"""
        errors = []

        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        return errors

    def _validate_tax_brackets(
        self,
        brackets: Dict[str, List],
        source: str
    ) -> List[str]:
        """
        Validate tax bracket structure and values.

        Args:
            brackets: Dictionary of tax brackets by filing status
            source: Source name (for error messages)

        Returns:
            List of error messages
        """
        errors = []

        # Check all filing statuses present
        expected_statuses = [
            'single', 'married_joint', 'married_separate', 'head_of_household'
        ]

        for status in expected_statuses:
            if status not in brackets:
                errors.append(f"{source}: Missing brackets for filing status '{status}'")
                continue

            bracket_list = brackets[status]

            # Validate bracket list
            if not isinstance(bracket_list, list) or len(bracket_list) == 0:
                errors.append(f"{source}/{status}: Brackets must be non-empty list")
                continue

            # Validate each bracket
            prev_upper = 0
            for i, bracket in enumerate(bracket_list):
                # Check structure
                if not isinstance(bracket, (list, tuple)) or len(bracket) != 2:
                    errors.append(f"{source}/{status}: Bracket {i} invalid format")
                    continue

                upper_limit, rate = bracket

                # Validate rate
                if not (0 <= rate <= 1):
                    errors.append(
                        f"{source}/{status}: Bracket {i} has invalid rate {rate*100:.1f}%"
                    )

                # Validate upper limit (skip infinity)
                if upper_limit != float('inf'):
                    if upper_limit <= prev_upper:
                        errors.append(
                            f"{source}/{status}: Bracket {i} upper limit ${upper_limit:,} "
                            f"not greater than previous ${prev_upper:,}"
                        )
                    prev_upper = upper_limit

            # Last bracket should be infinity
            if bracket_list[-1][0] != float('inf'):
                errors.append(f"{source}/{status}: Last bracket must have infinity upper limit")

        return errors

    def _validate_standard_deductions(self, deductions: Dict[str, float]) -> List[str]:
        """Validate standard deduction amounts"""
        errors = []

        expected_statuses = [
            'single', 'married_joint', 'married_separate', 'head_of_household'
        ]

        for status in expected_statuses:
            if status not in deductions:
                errors.append(f"Missing standard deduction for '{status}'")
                continue

            amount = deductions[status]

            # Reasonable range: $5,000 to $50,000
            if not (5000 <= amount <= 50000):
                errors.append(
                    f"Standard deduction for '{status}' (${amount:,}) "
                    f"is outside expected range ($5,000 - $50,000)"
                )

        # Married joint should be about 2x single
        if 'single' in deductions and 'married_joint' in deductions:
            ratio = deductions['married_joint'] / deductions['single']
            if not (1.8 <= ratio <= 2.2):
                errors.append(
                    f"Married/Single deduction ratio ({ratio:.2f}) is unusual (expect ~2.0)"
                )

        return errors

    def _validate_ltcg_brackets(self, brackets: Dict[str, List]) -> List[str]:
        """Validate long-term capital gains brackets"""
        errors = []

        expected_rates = {0.00, 0.15, 0.20}

        for status, bracket_list in brackets.items():
            for i, (upper_limit, rate) in enumerate(bracket_list):
                if rate not in expected_rates:
                    errors.append(
                        f"LTCG/{status}: Bracket {i} has unexpected rate {rate*100:.0f}% "
                        f"(expect 0%, 15%, or 20%)"
                    )

        return errors

    def _validate_amt_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate AMT-related data"""
        errors = []

        if 'amt_exemption' not in data or 'amt_phaseout_start' not in data:
            return errors  # Already flagged by schema validation

        exemptions = data['amt_exemption']
        phaseouts = data['amt_phaseout_start']

        # Check all filing statuses
        for status in ['single', 'married_joint', 'married_separate', 'head_of_household']:
            if status not in exemptions:
                errors.append(f"AMT: Missing exemption for '{status}'")
                continue

            if status not in phaseouts:
                errors.append(f"AMT: Missing phaseout start for '{status}'")
                continue

            exemption = exemptions[status]
            phaseout = phaseouts[status]

            # Exemption should be $50K - $200K
            if not (50000 <= exemption <= 200000):
                errors.append(
                    f"AMT/{status}: Exemption ${exemption:,} outside expected range"
                )

            # Phaseout should be $200K - $2M
            if not (200000 <= phaseout <= 2000000):
                errors.append(
                    f"AMT/{status}: Phaseout start ${phaseout:,} outside expected range"
                )

        return errors

    def _validate_thresholds(
        self,
        thresholds: Dict[str, float],
        name: str
    ) -> List[str]:
        """Validate threshold values (NIIT, Medicare, etc.)"""
        errors = []

        for status, threshold in thresholds.items():
            # Thresholds should be $100K - $500K
            if not (100000 <= threshold <= 500000):
                errors.append(
                    f"{name}/{status}: Threshold ${threshold:,} outside expected range"
                )

        # Married thresholds should be higher than single
        if 'single' in thresholds and 'married_joint' in thresholds:
            if thresholds['married_joint'] <= thresholds['single']:
                errors.append(
                    f"{name}: Married threshold should be higher than single"
                )

        return errors

    def compare_with_previous_year(
        self,
        current_data: Dict[str, Any],
        previous_data: Dict[str, Any],
        source: str
    ) -> List[str]:
        """
        Compare current year data with previous year, flag anomalies.

        Args:
            current_data: Current year tax data
            previous_data: Previous year tax data
            source: Source name ('federal' or 'california')

        Returns:
            List of warnings (not errors - anomalies may be valid)
        """
        warnings = []

        # Compare standard deductions (should increase with inflation)
        if 'standard_deductions' in current_data and 'standard_deductions' in previous_data:
            for status in current_data['standard_deductions']:
                if status in previous_data['standard_deductions']:
                    current = current_data['standard_deductions'][status]
                    previous = previous_data['standard_deductions'][status]

                    if current < previous:
                        warnings.append(
                            f"{source}/{status}: Standard deduction decreased "
                            f"(${previous:,} → ${current:,})"
                        )

                    # Expect 2-4% increase
                    pct_change = ((current - previous) / previous) * 100
                    if pct_change > 10:
                        warnings.append(
                            f"{source}/{status}: Large standard deduction increase "
                            f"({pct_change:.1f}%)"
                        )

        return warnings
