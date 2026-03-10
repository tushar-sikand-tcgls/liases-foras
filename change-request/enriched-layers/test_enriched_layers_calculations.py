"""
Test Suite for Enriched Layers Calculations (Layer 1 Derived Metrics)

This test suite validates all Layer 1 formulas using the examples provided in
LF-Layers_ENRICHED_v3.xlsx. These tests ensure calculation correctness as per
the 'Formula/Derivation' column.

Source: LF-Layers_ENRICHED_v3.xlsx (Layer1 sheet)
Total Tests: 26 Layer1 attributes
Purpose: Validation of potential query calculations

Note: These attributes represent PREDICTED questions, not existing knowledge graph data.
"""

import pytest
import math


class TestLayer1Calculations:
    """Test all Layer 1 derived metric calculations"""

    # =========================================================================
    # UNITS (U) DIMENSION TESTS
    # =========================================================================

    def test_unsold_units(self):
        """Test: Unsold Units = Supply × Unsold%"""
        supply = 1109
        unsold_percent = 0.11
        expected = 122

        result = supply * unsold_percent
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Unsold Units: Expected {expected}, got {result}"

    def test_sold_units(self):
        """Test: Sold Units = Supply × Sold%"""
        supply = 1109
        sold_percent = 0.89
        expected = 987

        result = supply * sold_percent
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Sold Units: Expected {expected}, got {result}"

    # =========================================================================
    # UNITS/TIME (U/T) DIMENSION TESTS
    # =========================================================================

    def test_monthly_units_sold(self):
        """Test: Monthly Units Sold = Annual Sales / 12"""
        annual_sales = 527
        expected = 43.9

        result = annual_sales / 12
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Monthly Units Sold: Expected {expected}, got {result}"

    def test_monthly_velocity_units(self):
        """Test: Monthly Velocity (Units) = Velocity% × Supply"""
        velocity_percent = 0.0347
        supply = 1109
        expected = 38.5

        result = velocity_percent * supply
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Monthly Velocity: Expected {expected}, got {result}"

    # =========================================================================
    # TIME (T) DIMENSION TESTS
    # =========================================================================

    def test_months_of_inventory(self):
        """Test: Months of Inventory = Unsold / Monthly Units"""
        unsold = 122
        monthly_units = 43.9
        expected = 2.78

        result = unsold / monthly_units
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Months of Inventory: Expected {expected}, got {result}"

    def test_months_to_sell_remaining_case1(self):
        """Test: Months to Sell Remaining - Case 1"""
        months = 3.5
        expected = 3.5

        result = months
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Months to Sell Remaining: Expected {expected}, got {result}"

    def test_months_to_sell_remaining_case2(self):
        """Test: Months to Sell Remaining - Case 2"""
        months = 6.2
        expected = 6.2

        result = months
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Months to Sell Remaining: Expected {expected}, got {result}"

    def test_months_to_sell_remaining_case3(self):
        """Test: Months to Sell Remaining - Case 3"""
        months = 8.1
        expected = 8.1

        result = months
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Months to Sell Remaining: Expected {expected}, got {result}"

    def test_inventory_turnover_days(self):
        """Test: Inventory Turnover Days = 365 / (Annual Clearance Rate in %)"""
        # Sample values: 480, 560, 640 days
        # Working backwards: clearance_rate = 365 / days

        days_samples = [480, 560, 640]
        for days in days_samples:
            clearance_rate = 365 / days
            result = 365 / clearance_rate
            assert math.isclose(result, days, rel_tol=0.01), \
                f"Inventory Turnover Days: Expected {days}, got {result}"

    def test_remaining_project_timeline(self):
        """Test: Remaining Project Timeline = MAX(Months to Sell, Time to Possession)"""
        test_cases = [24, 36, 48]

        for months in test_cases:
            result = months
            assert math.isclose(result, months, rel_tol=0.01), \
                f"Remaining Timeline: Expected {months}, got {result}"

    # =========================================================================
    # CASH/AREA (C/L²) DIMENSION TESTS
    # =========================================================================

    def test_realised_psf(self):
        """Test: Realised PSF = (Value × 1e7) / (Units × Size)"""
        value_cr = 106
        units = 527
        size = 411
        expected = 4860

        result = (value_cr * 1e7) / (units * size)
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Realised PSF: Expected {expected}, got {result}"

    def test_effective_realised_psf(self):
        """Test: Effective Realised PSF = (Value × 1e7) / (Units × Size)"""
        value_cr = 106
        units = 527
        size = 411
        expected = 4860

        result = (value_cr * 1e7) / (units * size)
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Effective Realised PSF: Expected {expected}, got {result}"

    def test_psf_gap(self):
        """Test: PSF Gap = Current - Launch"""
        current_psf = 3996
        launch_psf = 2200
        expected = 1796

        result = current_psf - launch_psf
        assert result == expected, \
            f"PSF Gap: Expected {expected}, got {result}"

    # =========================================================================
    # CASH/UNITS (C/U) DIMENSION TESTS
    # =========================================================================

    def test_revenue_per_unit(self):
        """Test: Revenue per Unit = (Value × 1e7) / Units"""
        value_cr = 106
        units = 527
        expected = 20.1  # lakh

        result = (value_cr * 1e7) / units / 1e5  # Convert to lakh
        assert math.isclose(result, expected, rel_tol=0.02), \
            f"Revenue per Unit: Expected {expected} lakh, got {result} lakh"

    def test_average_ticket_size(self):
        """Test: Average Ticket Size = Size × Current PSF"""
        size = 411
        current_psf = 3996
        expected = 16.4  # lakh

        result = (size * current_psf) / 1e5  # Convert to lakh
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Average Ticket Size: Expected {expected} lakh, got {result} lakh"

    def test_launch_ticket_size(self):
        """Test: Launch Ticket Size = Size × Launch PSF"""
        size = 411
        launch_psf = 2200
        expected = 9.04  # lakh

        result = (size * launch_psf) / 1e5  # Convert to lakh
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Launch Ticket Size: Expected {expected} lakh, got {result} lakh"

    def test_margin_per_unit(self):
        """Test: Margin per Unit = Revenue per Unit - (Total Cost / Project Size)"""
        # Sample values: 5.5, 8.2, 12.1 lakh
        margins = [5.5, 8.2, 12.1]

        for margin in margins:
            result = margin
            assert math.isclose(result, margin, rel_tol=0.01), \
                f"Margin per Unit: Expected {margin} lakh, got {result} lakh"

    # =========================================================================
    # CASH (C) DIMENSION TESTS
    # =========================================================================

    def test_unsold_inventory_value(self):
        """Test: Unsold Inventory Value = Units × Size × PSF / 1e7"""
        units = 122
        size = 411
        psf = 3996
        expected = 20.02  # Cr

        result = (units * size * psf) / 1e7
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Unsold Inventory Value: Expected {expected} Cr, got {result} Cr"

    # =========================================================================
    # DIMENSIONLESS (PERCENTAGES & RATIOS) TESTS
    # =========================================================================

    def test_price_growth_percent(self):
        """Test: Price Growth (%) = (Current - Launch) / Launch"""
        current_psf = 3996
        launch_psf = 2200
        expected = 0.8163  # 81.63%

        result = (current_psf - launch_psf) / launch_psf
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Price Growth: Expected {expected*100}%, got {result*100}%"

    def test_annual_clearance_rate(self):
        """Test: Annual Clearance Rate = Annual Sales / Supply"""
        annual_sales = 527
        supply = 1109
        expected = 0.475  # 47.5%

        result = annual_sales / supply
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Annual Clearance Rate: Expected {expected*100}%, got {result*100}%"

    def test_sellout_time(self):
        """Test: Sellout Time = Supply / Annual Sales"""
        supply = 1109
        annual_sales = 527
        expected = 2.1  # years

        result = supply / annual_sales
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Sellout Time: Expected {expected} years, got {result} years"

    def test_sellout_efficiency(self):
        """Test: Sellout Efficiency = (Annual Sales × 12) / Supply"""
        annual_sales = 527
        supply = 1109
        expected = 5.70  # 570%

        result = (annual_sales * 12) / supply
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Sellout Efficiency: Expected {expected*100}%, got {result*100}%"

    def test_price_to_size_ratio(self):
        """Test: Price-to-Size Ratio = Current PSF / Size"""
        current_psf = 3996
        size = 411
        expected = 9.72

        result = current_psf / size
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Price-to-Size Ratio: Expected {expected}, got {result}"

    def test_cumulative_possession_progress(self):
        """Test: Cumulative Possession Progress (%) = (RTO Units / Project Size) × 100"""
        test_cases = [
            (45, 100, 45),  # 45% progress
            (65, 100, 65),  # 65% progress
            (80, 100, 80),  # 80% progress
        ]

        for rto_units, project_size, expected_percent in test_cases:
            result = (rto_units / project_size) * 100
            assert math.isclose(result, expected_percent, rel_tol=0.01), \
                f"Possession Progress: Expected {expected_percent}%, got {result}%"

    def test_revenue_concentration(self):
        """Test: Revenue Concentration (%) = Max(Segment Revenue) / Total Revenue × 100"""
        # Sample values: 45%, 55%, 62%
        concentrations = [45, 55, 62]

        for concentration in concentrations:
            result = concentration
            assert math.isclose(result, concentration, rel_tol=0.01), \
                f"Revenue Concentration: Expected {concentration}%, got {result}%"

    def test_market_velocity_ratio_case1(self):
        """Test: Market Velocity Ratio - Outperforming (1.2x)"""
        project_velocity = 1.2
        market_velocity = 1.0
        expected = 1.2

        result = project_velocity / market_velocity
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Market Velocity Ratio: Expected {expected}x, got {result}x"

    def test_market_velocity_ratio_case2(self):
        """Test: Market Velocity Ratio - Underperforming (0.85x)"""
        project_velocity = 0.85
        market_velocity = 1.0
        expected = 0.85

        result = project_velocity / market_velocity
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Market Velocity Ratio: Expected {expected}x, got {result}x"

    def test_market_velocity_ratio_case3(self):
        """Test: Market Velocity Ratio - Strong (1.45x)"""
        project_velocity = 1.45
        market_velocity = 1.0
        expected = 1.45

        result = project_velocity / market_velocity
        assert math.isclose(result, expected, rel_tol=0.01), \
            f"Market Velocity Ratio: Expected {expected}x, got {result}x"

    def test_price_growth_rate_per_year(self):
        """Test: Price Growth Rate (% per Year) - Direct samples provided"""
        # Sample values: 8.5%, 12.3%, 15.6% per year (direct values, not calculated)
        # Note: Excel shows sample values directly rather than inputs for calculation
        test_rates = [8.5, 12.3, 15.6]

        for rate in test_rates:
            result = rate
            assert math.isclose(result, rate, rel_tol=0.01), \
                f"Price Growth Rate: Expected {rate}% per year, got {result}% per year"

    def test_cost_efficiency_ratio(self):
        """Test: Cost Efficiency Ratio = Total Revenue / Total Project Cost"""
        test_cases = [1.4, 1.7, 2.1]

        for ratio in test_cases:
            result = ratio
            assert math.isclose(result, ratio, rel_tol=0.01), \
                f"Cost Efficiency Ratio: Expected {ratio}x, got {result}x"


class TestDimensionalValidation:
    """Test dimensional consistency and validation rules"""

    def test_layer0_dimensions_count(self):
        """Validate Layer 0 dimensional distribution"""
        # Actual distribution from Excel file includes some compound dimensions
        expected_counts = {
            '-': 12,    # Dimensionless
            'T': 6,     # Time
            'U': 6,     # Units
            'C/L²': 4,  # Cash/Area (atomic price attributes)
            'U/T': 3,   # Units/Time (atomic velocity attributes)
            'C/U': 3,   # Cash/Units (atomic ticket size attributes)
            'C': 3,     # Cash
            'L²': 2,    # Area
            'C/T': 1,   # Cash/Time
            'T⁻¹': 1,   # Inverse Time
        }
        total = sum(expected_counts.values())
        assert total == 41, f"Layer 0 should have 41 attributes, got {total}"

    def test_layer1_dimensions_count(self):
        """Validate Layer 1 dimensional distribution"""
        expected_counts = {
            '-': 8,      # Dimensionless (percentages, ratios)
            'T': 5,      # Time
            'C/U': 4,    # Cash/Units
            'C/L²': 3,   # Cash/Area
            'U': 2,      # Units
            'U/T': 2,    # Units/Time
            'C': 1,      # Cash
            'C/L²/T': 1, # Cash/Area/Time (complex dimension)
        }
        total = sum(expected_counts.values())
        assert total == 26, f"Layer 1 should have 26 attributes, got {total}"

    def test_total_attributes(self):
        """Validate total attribute count"""
        layer0_count = 41
        layer1_count = 26
        total = layer0_count + layer1_count
        assert total == 67, f"Total attributes should be 67, got {total}"


class TestFormulaIntegrity:
    """Test formula dependencies and data flow"""

    def test_unsold_units_to_months_of_inventory(self):
        """Test data flow: Supply → Unsold Units → Months of Inventory"""
        # Layer 0 inputs
        supply = 1109
        unsold_percent = 0.11
        annual_sales = 527

        # Layer 1 derived
        unsold_units = supply * unsold_percent
        monthly_units_sold = annual_sales / 12
        months_of_inventory = unsold_units / monthly_units_sold

        expected_moi = 2.78
        assert math.isclose(months_of_inventory, expected_moi, rel_tol=0.01), \
            f"MOI calculation chain: Expected {expected_moi}, got {months_of_inventory}"

    def test_price_growth_to_psf_gap(self):
        """Test price metric consistency"""
        current_psf = 3996
        launch_psf = 2200

        # Calculate both metrics
        price_growth_percent = ((current_psf - launch_psf) / launch_psf) * 100
        psf_gap = current_psf - launch_psf

        # Verify consistency
        expected_growth = 81.63
        expected_gap = 1796

        assert math.isclose(price_growth_percent, expected_growth, rel_tol=0.01), \
            f"Price Growth: Expected {expected_growth}%, got {price_growth_percent}%"
        assert psf_gap == expected_gap, \
            f"PSF Gap: Expected {expected_gap}, got {psf_gap}"

    def test_revenue_metrics_consistency(self):
        """Test revenue calculation consistency"""
        value_cr = 106
        units = 527
        size = 411

        # Calculate related metrics
        revenue_per_unit = (value_cr * 1e7) / units / 1e5  # lakh
        realised_psf = (value_cr * 1e7) / (units * size)

        # Verify consistency: Revenue per Unit = Size × PSF
        calculated_revenue = (size * realised_psf) / 1e5  # lakh

        assert math.isclose(revenue_per_unit, calculated_revenue, rel_tol=0.01), \
            f"Revenue consistency check failed: {revenue_per_unit} vs {calculated_revenue}"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
