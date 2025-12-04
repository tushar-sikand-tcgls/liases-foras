"""
Test Layer 2 Calculator: Financial Metrics

Tests NPV, IRR, Payback Period with ±2% accuracy requirement (Acceptance Criteria #5)
"""
import pytest
from app.calculators.layer2 import Layer2Calculator
from app.models.domain import FinancialProjection


class TestLayer2Calculator:
    """Test Layer 2 financial metrics with strict accuracy requirements"""

    def test_npv_calculation(self, sample_projection):
        """
        Test NPV calculation accuracy

        Acceptance Criteria #5: NPV must match LF standards within ±2%
        """
        npv = Layer2Calculator.calculate_npv(sample_projection)

        # Expected NPV calculation (manual verification)
        # PV = -50 + 12.5/(1.12)^1 + 15/(1.12)^2 + 17.5/(1.12)^3 + 20/(1.12)^4 + 22.5/(1.12)^5
        # PV = -50 + 11.16 + 11.96 + 12.45 + 12.71 + 12.77 = 11.05 Cr
        expected_npv = 110500000  # 11.05 Cr (approximate)
        tolerance = abs(expected_npv) * 0.02  # ±2%

        assert npv is not None, "NPV calculation failed"
        assert abs(npv - expected_npv) < tolerance, \
            f"NPV {npv/10000000:.2f} Cr outside ±2% tolerance of {expected_npv/10000000:.2f} Cr"

        # NPV should be positive for a viable project
        assert npv > 0, "NPV should be positive for viable project"

    def test_irr_calculation(self, sample_projection):
        """
        Test IRR calculation accuracy

        Acceptance Criteria #5: IRR must match LF standards within ±2%
        """
        irr = Layer2Calculator.calculate_irr(sample_projection)

        assert irr is not None, "IRR calculation failed"

        # Expected IRR ≈ 24% (from PRD examples and project data)
        expected_irr = 0.24
        tolerance = expected_irr * 0.02  # ±2%

        assert abs(irr - expected_irr) < tolerance, \
            f"IRR {irr*100:.2f}% outside ±2% tolerance of {expected_irr*100:.2f}%"

        # IRR should be between 15% and 35% for typical real estate
        assert 0.15 <= irr <= 0.35, f"IRR {irr*100:.2f}% outside reasonable range (15%-35%)"

    def test_irr_convergence(self):
        """Test that IRR calculation converges for various cash flow patterns"""

        test_cases = [
            {
                "name": "Standard growth",
                "initial": 500000000,
                "cfs": [100000000, 150000000, 200000000, 250000000, 300000000],
                "expected_range": (0.20, 0.30)
            },
            {
                "name": "Declining returns",
                "initial": 500000000,
                "cfs": [300000000, 250000000, 200000000, 150000000, 100000000],
                "expected_range": (0.15, 0.25)
            },
            {
                "name": "Stable cash flows",
                "initial": 500000000,
                "cfs": [200000000] * 5,
                "expected_range": (0.25, 0.35)
            }
        ]

        for case in test_cases:
            projection = FinancialProjection(
                initial_investment=case["initial"],
                annual_cash_flows=case["cfs"],
                discount_rate=0.12,
                project_duration_years=len(case["cfs"])
            )

            irr = Layer2Calculator.calculate_irr(projection)

            assert irr is not None, f"IRR failed to converge for {case['name']}"
            assert case["expected_range"][0] <= irr <= case["expected_range"][1], \
                f"IRR {irr*100:.2f}% outside expected range for {case['name']}"

    def test_payback_period(self, sample_projection):
        """
        Test payback period calculation

        Payback should be less than project duration for viable projects
        """
        pbp = Layer2Calculator.calculate_payback_period(sample_projection)

        assert pbp is not None, "Payback period calculation failed"
        assert pbp > 0, "Payback period should be positive"
        assert pbp < sample_projection.project_duration_years, \
            "Payback period should be less than project duration"

        # Typical real estate payback is 2-4 years
        assert 1 <= pbp <= 5, f"Payback period {pbp:.2f} years outside reasonable range (1-5 years)"

    def test_profitability_index(self, sample_projection):
        """
        Test profitability index calculation

        PI > 1.0 indicates profitable project
        """
        pi = Layer2Calculator.calculate_profitability_index(sample_projection)

        assert pi > 0, "Profitability index should be positive"

        # PI > 1 means project is profitable
        assert pi > 1.0, f"Project should be profitable (PI={pi:.3f} should be > 1.0)"

        # Typical real estate PI is 1.0 to 1.5
        assert 1.0 <= pi <= 2.0, f"PI {pi:.3f} outside reasonable range (1.0-2.0)"

    def test_cap_rate(self):
        """Test capitalization rate calculation"""

        annual_noi = 50000000  # 5 Cr annual NOI
        property_value = 500000000  # 50 Cr property value

        cap_rate = Layer2Calculator.calculate_cap_rate(annual_noi, property_value)

        # Cap rate should be 10%
        expected_cap_rate = 0.10
        assert abs(cap_rate - expected_cap_rate) < 0.001, \
            f"Cap rate {cap_rate*100:.2f}% should be 10%"

        # Typical real estate cap rates are 5-15%
        assert 0.05 <= cap_rate <= 0.15, \
            f"Cap rate {cap_rate*100:.2f}% outside reasonable range (5%-15%)"

    def test_roi(self):
        """Test ROI calculation"""

        net_profit = 520000000 - 500000000  # 52 Cr - 50 Cr = 2 Cr profit
        initial_investment = 500000000  # 50 Cr

        roi = Layer2Calculator.calculate_roi(net_profit, initial_investment)

        # ROI should be 4%
        expected_roi = 4.0
        assert abs(roi - expected_roi) < 0.1, \
            f"ROI {roi:.2f}% should be approximately {expected_roi}%"

    def test_sensitivity_analysis(self, sample_projection):
        """
        Test sensitivity analysis

        Should generate Base, Optimistic, and Stress case scenarios
        """
        sensitivity = Layer2Calculator.calculate_sensitivity_analysis(
            sample_projection,
            absorption_range=(0.7, 1.3),
            price_range=(0.9, 1.1)
        )

        # Check all scenarios exist
        assert 'baseCase' in sensitivity
        assert 'optimisticCase' in sensitivity
        assert 'stressCase' in sensitivity

        # Check base case
        base = sensitivity['baseCase']
        assert base['irr_percent'] is not None
        assert base['npv_inr'] is not None

        # Check optimistic > base > stress
        optimistic = sensitivity['optimisticCase']
        stress = sensitivity['stressCase']

        assert optimistic['irr_percent'] > base['irr_percent'], \
            "Optimistic IRR should be higher than base case"
        assert stress['irr_percent'] < base['irr_percent'], \
            "Stress IRR should be lower than base case"

        assert optimistic['npv_inr'] > base['npv_inr'], \
            "Optimistic NPV should be higher than base case"
        assert stress['npv_inr'] < base['npv_inr'], \
            "Stress NPV should be lower than base case"

    def test_edge_cases(self):
        """Test edge cases and error handling"""

        # Zero initial investment should not cause division by zero
        projection = FinancialProjection(
            initial_investment=1,  # Small but non-zero
            annual_cash_flows=[1000000],
            discount_rate=0.12,
            project_duration_years=1
        )

        npv = Layer2Calculator.calculate_npv(projection)
        assert npv is not None

        # Very high IRR (extreme profitable project)
        projection_high = FinancialProjection(
            initial_investment=1000000,
            annual_cash_flows=[10000000] * 3,
            discount_rate=0.12,
            project_duration_years=3
        )

        irr_high = Layer2Calculator.calculate_irr(projection_high)
        assert irr_high is not None
        assert irr_high > 0.50, "High profitability project should have high IRR"

    def test_npv_irr_consistency(self, sample_projection):
        """
        Test consistency between NPV and IRR

        At IRR, NPV should be approximately zero
        """
        irr = Layer2Calculator.calculate_irr(sample_projection)
        assert irr is not None

        # Calculate NPV at the IRR rate
        projection_at_irr = FinancialProjection(
            initial_investment=sample_projection.initial_investment,
            annual_cash_flows=sample_projection.annual_cash_flows,
            discount_rate=irr,
            project_duration_years=sample_projection.project_duration_years
        )

        npv_at_irr = Layer2Calculator.calculate_npv(projection_at_irr)

        # NPV at IRR should be very close to zero (within tolerance)
        assert abs(npv_at_irr) < 1000, \
            f"NPV at IRR should be ~0, but got {npv_at_irr:.2f}"

    def test_result_dict_creation(self, sample_projection):
        """Test standardized result dictionary creation"""

        irr = Layer2Calculator.calculate_irr(sample_projection)
        result = Layer2Calculator.create_result_dict(
            metric_name="IRR",
            value=irr,
            unit="%/year",
            dimension="T^-1",
            projection=sample_projection,
            formula="r where NPV(r) = 0",
            algorithm="Newton's method"
        )

        # Check structure
        assert "metric" in result
        assert "value" in result
        assert "unit" in result
        assert "dimension" in result
        assert "formula" in result
        assert "algorithm" in result
        assert "inputs" in result

        # Check values
        assert result["metric"] == "IRR"
        assert result["unit"] == "%/year"
        assert result["dimension"] == "T^-1"

    def test_provenance_creation(self):
        """Test provenance tracking creation"""

        provenance = Layer2Calculator.create_provenance(
            metric_name="IRR",
            algorithm="Newton's method (scipy.optimize.newton)",
            lf_source="Pillar_4.3",
            data_version="Q3_FY25"
        )

        # Check structure
        assert "inputDimensions" in provenance
        assert "calculationMethod" in provenance
        assert "lfSource" in provenance
        assert "algorithm" in provenance
        assert "timestamp" in provenance
        assert "dataVersion" in provenance
        assert "layer" in provenance

        # Check values
        assert provenance["layer"] == 2
        assert provenance["lfSource"] == "Pillar_4.3"
        assert provenance["dataVersion"] == "Q3_FY25"
        assert "CF" in provenance["inputDimensions"]
        assert "T" in provenance["inputDimensions"]
