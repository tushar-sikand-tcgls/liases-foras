"""
L2 Metrics Validator
====================

Validates Layer 2 financial metrics for data quality and sanity.
Prevents absurd values like ₹90,000 Crore land costs from propagating.
"""

from typing import Tuple, Dict, Any


class L2MetricsValidator:
    """Validator for Layer 2 financial metrics"""

    @staticmethod
    def validate_total_cost(
        total_cost_cr: float,
        total_revenue_cr: float,
        total_units: int,
        project_name: str = "Unknown"
    ) -> Tuple[bool, str]:
        """
        Validate total cost for sanity

        Rules:
        1. Cost should not be > 10× revenue (absurd loss scenario)
        2. Cost per unit should be ₹20-200 lakh/unit (reasonable range)

        Args:
            total_cost_cr: Total project cost in Crores
            total_revenue_cr: Total revenue in Crores
            total_units: Number of units
            project_name: Project name for logging

        Returns:
            (is_valid, message)
        """
        # Rule 1: Cost vs Revenue sanity
        if total_cost_cr > total_revenue_cr * 10:
            return False, (
                f"[{project_name}] Total cost (₹{total_cost_cr:.2f} Cr) is > 10× revenue "
                f"(₹{total_revenue_cr:.2f} Cr). This indicates data error."
            )

        # Rule 2: Cost per unit range (minimum check only)
        if total_units and total_cost_cr > 0:
            cost_per_unit_cr = total_cost_cr / total_units
            cost_per_unit_lakh = cost_per_unit_cr * 100  # Convert Cr to lakh

            if cost_per_unit_lakh < 20:
                return False, (
                    f"[{project_name}] Cost per unit (₹{cost_per_unit_lakh:.2f} lakh) is "
                    f"unrealistically low (< ₹20 lakh)"
                )
            # NOTE: No upper limit - luxury/premium projects can have very high cost per unit

        return True, "OK"

    @staticmethod
    def validate_npv(
        npv_cr: float,
        total_cost_cr: float,
        project_name: str = "Unknown"
    ) -> Tuple[bool, str]:
        """
        Validate NPV for sanity

        Rule: NPV magnitude should not be > 5× total cost
        (If NPV is -₹90,000 Cr and cost is ₹100 Cr, something is very wrong)

        Args:
            npv_cr: Net Present Value in Crores
            total_cost_cr: Total cost in Crores
            project_name: Project name for logging

        Returns:
            (is_valid, message)
        """
        if total_cost_cr > 0 and abs(npv_cr) > total_cost_cr * 5:
            return False, (
                f"[{project_name}] NPV magnitude (₹{abs(npv_cr):.2f} Cr) is > 5× total cost "
                f"(₹{total_cost_cr:.2f} Cr). This indicates calculation error."
            )

        return True, "OK"

    @staticmethod
    def validate_payback_period(
        payback_years: float,
        project_name: str = "Unknown"
    ) -> Tuple[bool, str]:
        """
        Validate payback period for sanity

        Rule: Payback period should be 0-50 years for residential projects
        (855 years is clearly wrong)

        Args:
            payback_years: Payback period in years
            project_name: Project name for logging

        Returns:
            (is_valid, message)
        """
        if payback_years < 0:
            return False, (
                f"[{project_name}] Payback period ({payback_years:.2f} years) is negative. "
                f"This indicates negative cash flow or calculation error."
            )

        if payback_years > 50:
            return False, (
                f"[{project_name}] Payback period ({payback_years:.2f} years) is > 50 years. "
                f"This is unrealistic for residential projects."
            )

        return True, "OK"

    @staticmethod
    def validate_irr(
        irr_pct: float,
        project_name: str = "Unknown"
    ) -> Tuple[bool, str]:
        """
        Validate IRR for sanity

        Rule: IRR should be between -50% and +100% for real estate
        (Values like -99% or 500% indicate calculation errors)

        Args:
            irr_pct: IRR percentage
            project_name: Project name for logging

        Returns:
            (is_valid, message)
        """
        if irr_pct < -50:
            return False, (
                f"[{project_name}] IRR ({irr_pct:.2f}%) is < -50%. "
                f"This indicates severe calculation or data error."
            )

        if irr_pct > 100:
            return False, (
                f"[{project_name}] IRR ({irr_pct:.2f}%) is > 100%. "
                f"This is unrealistic for real estate projects."
            )

        return True, "OK"

    @staticmethod
    def validate_all_l2_metrics(
        l2_metrics: Dict[str, Any],
        project: Dict[str, Any]
    ) -> Tuple[bool, list]:
        """
        Validate all L2 metrics for a project

        Args:
            l2_metrics: Dict of L2 metrics with nested {value, unit} structure
            project: Project dict with L1 attributes

        Returns:
            (is_valid, list_of_errors)
        """
        from app.services.data_service import data_service

        errors = []
        project_name = data_service.get_value(project.get('projectName', {})) or 'Unknown'

        # Extract values
        total_cost_cr = data_service.get_value(l2_metrics.get('totalCostCr', {}).get('value', 0))
        total_revenue_cr = data_service.get_value(l2_metrics.get('totalRevenueCr', {}).get('value', 0))
        npv_cr = data_service.get_value(l2_metrics.get('npvCr', {}).get('value', 0))
        irr_pct = data_service.get_value(l2_metrics.get('irrPct', {}).get('value', 0))
        payback_years = data_service.get_value(l2_metrics.get('paybackPeriodYears', {}).get('value', 0))
        total_units = data_service.get_value(project.get('totalSupplyUnits', {}).get('value', 0))

        # Run validations
        is_valid, msg = L2MetricsValidator.validate_total_cost(
            total_cost_cr, total_revenue_cr, total_units, project_name
        )
        if not is_valid:
            errors.append(msg)

        is_valid, msg = L2MetricsValidator.validate_npv(npv_cr, total_cost_cr, project_name)
        if not is_valid:
            errors.append(msg)

        is_valid, msg = L2MetricsValidator.validate_payback_period(payback_years, project_name)
        if not is_valid:
            errors.append(msg)

        is_valid, msg = L2MetricsValidator.validate_irr(irr_pct, project_name)
        if not is_valid:
            errors.append(msg)

        return (len(errors) == 0, errors)


# Global validator instance
l2_validator = L2MetricsValidator()
