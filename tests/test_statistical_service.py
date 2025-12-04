"""
Unit tests for Statistical Service

Tests all 8 statistical operations:
1. TOTAL (SUM)
2. AVERAGE (MEAN)
3. MEDIAN
4. MODE
5. STANDARD DEVIATION
6. VARIANCE
7. PERCENTILE
8. NORMAL DISTRIBUTION
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from app.services.statistical_service import StatisticalService


class TestStatisticalService:
    """Test suite for statistical service"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = StatisticalService()

        # Sample real estate data (PSF values)
        self.sample_data = [4200, 4500, 4300, 4800, 3900, 5100, 4400, 4600, 4200, 4500]

        # Sample data with outliers
        self.outlier_data = [4200, 4300, 4400, 4500, 4600, 8900, 1200]  # 8900 and 1200 are outliers

        # Sample data for mode testing (multimodal)
        self.mode_data = [4200, 4200, 4500, 4500, 4300, 4800]

        # Small dataset (less than minimum for some operations)
        self.small_data = [4200]

        # Invalid data
        self.invalid_data = [4200, None, "invalid", 4500, np.nan]

    def test_validate_input_valid_data(self):
        """Test input validation with valid data"""
        is_valid, error, arr = self.service.validate_input(self.sample_data, "mean")

        assert is_valid is True
        assert error is None
        assert len(arr) == 10
        assert np.allclose(arr[0], 4200)

    def test_validate_input_empty_data(self):
        """Test input validation with empty data"""
        is_valid, error, arr = self.service.validate_input([], "mean")

        assert is_valid is False
        assert "Empty dataset" in error
        assert arr is None

    def test_validate_input_non_numeric_data(self):
        """Test input validation with non-numeric data"""
        is_valid, error, arr = self.service.validate_input(self.invalid_data, "mean")

        assert is_valid is True  # Should filter out invalid values
        assert error is None
        assert len(arr) == 2  # Only 4200 and 4500 are valid

    def test_validate_input_insufficient_data(self):
        """Test input validation with insufficient data for operation"""
        is_valid, error, arr = self.service.validate_input(self.small_data, "std_dev")

        assert is_valid is False
        assert "Insufficient data" in error
        assert arr is None

    def test_calculate_mode(self):
        """Test MODE calculation"""
        arr = np.array(self.mode_data)
        result = self.service.calculate_mode(arr)

        assert result["mode"] in [4200, 4500]  # Either is valid (multimodal)
        assert result["frequency"] == 2
        assert result["is_multimodal"] is True
        assert len(result["all_modes"]) == 2
        assert 4200 in result["all_modes"]
        assert 4500 in result["all_modes"]

    def test_calculate_mode_single_mode(self):
        """Test MODE calculation with single mode"""
        arr = np.array([4200, 4200, 4200, 4300, 4400])
        result = self.service.calculate_mode(arr)

        assert result["mode"] == 4200
        assert result["frequency"] == 3
        assert result["is_multimodal"] is False

    def test_calculate_normal_distribution(self):
        """Test NORMAL_DISTRIBUTION analysis"""
        arr = np.array(self.sample_data)
        result = self.service.calculate_normal_distribution(arr)

        # Check basic statistics
        assert "mean" in result
        assert "std_dev" in result
        assert abs(result["mean"] - 4450) < 10  # Should be close to 4450

        # Check distribution properties
        assert "is_normal" in result
        assert "p_value" in result
        assert "skewness" in result
        assert "kurtosis" in result

        # Check outlier detection
        assert "outliers" in result
        assert "count" in result["outliers"]
        assert "values" in result["outliers"]
        assert "z_scores" in result["outliers"]

        # Check confidence intervals
        assert "confidence_intervals" in result
        assert "68%" in result["confidence_intervals"]
        assert "95%" in result["confidence_intervals"]
        assert "99.7%" in result["confidence_intervals"]

        # Check coefficient of variation
        assert "coefficient_of_variation" in result

    def test_calculate_normal_distribution_with_outliers(self):
        """Test NORMAL_DISTRIBUTION with outliers"""
        arr = np.array(self.outlier_data)
        result = self.service.calculate_normal_distribution(arr)

        # Should detect outliers
        assert result["outliers"]["count"] >= 1
        assert len(result["outliers"]["values"]) >= 1

        # Check if extreme values are marked as outliers
        outlier_values = result["outliers"]["values"]
        assert 8900 in outlier_values or 1200 in outlier_values

    def test_calculate_series_statistics_all_operations(self):
        """Test comprehensive statistics with all 8 operations"""
        result = self.service.calculate_series_statistics(
            values=self.sample_data,
            metric_name="Price PSF",
            context="market_pricing"
        )

        # Check metadata
        assert result["metric_name"] == "Price PSF"
        assert result["context"] == "market_pricing"
        assert "timestamp" in result

        # Check data quality
        assert result["data_quality"]["original_count"] == 10
        assert result["data_quality"]["valid_count"] == 10
        assert result["data_quality"]["quality_score"] == 100.0

        # Check all 8 operations are present
        ops = result["operations"]
        assert "total" in ops
        assert "average" in ops
        assert "median" in ops
        assert "mode" in ops
        assert "std_dev" in ops
        assert "variance" in ops
        assert "percentiles" in ops
        assert "normal_distribution" in ops

        # Verify specific calculations (with tolerance for floating point)
        assert abs(ops["total"]["value"] - 44500) < 1
        assert abs(ops["average"]["value"] - 4450) < 1
        assert ops["median"]["value"] == 4450

        # Check interpretation
        assert "interpretation" in result
        assert "insights" in result["interpretation"]
        assert "recommendations" in result["interpretation"]

    def test_calculate_series_statistics_specific_operations(self):
        """Test statistics with specific operations only"""
        result = self.service.calculate_series_statistics(
            values=self.sample_data,
            operations=["AVERAGE", "STD_DEV"],
            metric_name="Price PSF"
        )

        ops = result["operations"]

        # Only requested operations should be present
        assert "average" in ops
        assert "std_dev" in ops

        # These should not be present
        assert "total" not in ops
        assert "median" not in ops
        assert "mode" not in ops

    def test_calculate_series_statistics_with_invalid_data(self):
        """Test statistics with invalid/missing data"""
        result = self.service.calculate_series_statistics(
            values=self.invalid_data,
            operations=["AVERAGE"],
            metric_name="Price PSF"
        )

        # Should handle invalid data gracefully
        assert result["data_quality"]["original_count"] == 5
        assert result["data_quality"]["valid_count"] == 2  # Only 4200 and 4500
        assert result["data_quality"]["quality_score"] == 40.0

        # Should calculate on valid data only
        assert abs(result["operations"]["average"]["value"] - 4350) < 1

    def test_calculate_series_statistics_empty_data(self):
        """Test statistics with empty data"""
        result = self.service.calculate_series_statistics(
            values=[],
            operations=["AVERAGE"],
            metric_name="Price PSF"
        )

        # Should return error
        assert "error" in result
        assert result["error_code"] == 201
        assert "Empty dataset" in result["error"]

    def test_business_interpretation_high_volatility(self):
        """Test business interpretation for high volatility data"""
        # Create high volatility data
        high_vol_data = [2000, 8000, 3000, 7000, 2500, 7500]

        result = self.service.calculate_series_statistics(
            values=high_vol_data,
            operations=["AVERAGE", "STD_DEV"],
            context="market_pricing"
        )

        insights = result["interpretation"]["insights"]
        recommendations = result["interpretation"]["recommendations"]

        # Should detect high volatility
        assert any("High volatility" in insight for insight in insights)
        assert any("risk mitigation" in rec for rec in recommendations)

    def test_business_interpretation_low_volatility(self):
        """Test business interpretation for low volatility data"""
        # Create low volatility data
        low_vol_data = [4400, 4450, 4420, 4480, 4440, 4460]

        result = self.service.calculate_series_statistics(
            values=low_vol_data,
            operations=["AVERAGE", "STD_DEV"],
            context="market_pricing"
        )

        insights = result["interpretation"]["insights"]

        # Should detect low volatility
        assert any("Low volatility" in insight or "stable" in insight.lower()
                  for insight in insights)

    def test_business_interpretation_skewness(self):
        """Test business interpretation for skewed distributions"""
        # Right-skewed data (high outliers)
        right_skewed = [4000, 4100, 4200, 4300, 8000]

        result = self.service.calculate_series_statistics(
            values=right_skewed,
            operations=["AVERAGE", "MEDIAN"],
            context="market_pricing"
        )

        insights = result["interpretation"]["insights"]

        # Should detect right skew (mean > median)
        assert any("skewed" in insight.lower() for insight in insights)

    def test_percentile_calculations(self):
        """Test PERCENTILE calculations"""
        result = self.service.calculate_series_statistics(
            values=self.sample_data,
            operations=["PERCENTILE"],
            metric_name="Price PSF"
        )

        percentiles = result["operations"]["percentiles"]

        # Check all percentiles are present
        assert "p10" in percentiles
        assert "p25" in percentiles
        assert "p50" in percentiles  # Should equal median
        assert "p75" in percentiles
        assert "p90" in percentiles

        # Check ordering (percentiles should be non-decreasing)
        assert percentiles["p10"] <= percentiles["p25"]
        assert percentiles["p25"] <= percentiles["p50"]
        assert percentiles["p50"] <= percentiles["p75"]
        assert percentiles["p75"] <= percentiles["p90"]

    def test_formula_and_use_case_documentation(self):
        """Test that all operations include formula and use_case"""
        result = self.service.calculate_series_statistics(
            values=self.sample_data,
            operations=None  # All operations
        )

        ops = result["operations"]

        # Check each operation has required documentation
        for op_name, op_data in ops.items():
            assert "formula" in op_data, f"{op_name} missing formula"
            assert "use_case" in op_data, f"{op_name} missing use_case"
            assert "dimension" in op_data, f"{op_name} missing dimension"

    @patch('app.services.statistical_service.data_service')
    def test_aggregate_by_region(self, mock_data_service):
        """Test regional aggregation"""
        # Mock project data
        mock_projects = [
            {"projectName": {"value": "Project A"}, "projectId": {"value": "1"},
             "location": {"value": "Chakan"}, "city": {"value": "Pune"},
             "l1_attributes": {"projectSize": {"value": 100000}}},
            {"projectName": {"value": "Project B"}, "projectId": {"value": "2"},
             "location": {"value": "Chakan"}, "city": {"value": "Pune"},
             "l1_attributes": {"projectSize": {"value": 150000}}}
        ]

        mock_data_service.get_all_projects.return_value = mock_projects
        mock_data_service.get_value.side_effect = lambda x: x.get("value") if isinstance(x, dict) else x

        self.service.data_service = mock_data_service

        result = self.service.aggregate_by_region(
            region="Chakan",
            city="Pune",
            attribute_path="l1_attributes.projectSize",
            attribute_name="Project Size"
        )

        assert result["region"] == "Chakan"
        assert result["city"] == "Pune"
        assert result["attribute"] == "Project Size"
        assert result["project_count"] == 2
        assert len(result["projects"]) == 2
        assert "statistics" in result

    @patch('app.services.statistical_service.data_service')
    def test_get_top_n_projects(self, mock_data_service):
        """Test top N projects ranking"""
        # Mock project data with different values
        mock_projects = [
            {"projectName": {"value": f"Project {i}"}, "projectId": {"value": str(i)},
             "location": {"value": "Chakan"}, "city": {"value": "Pune"},
             "l1_attributes": {"price": {"value": 4000 + i*100}}}
            for i in range(10)
        ]

        mock_data_service.get_all_projects.return_value = mock_projects
        mock_data_service.get_value.side_effect = lambda x: x.get("value") if isinstance(x, dict) else x

        self.service.data_service = mock_data_service

        # Get top 3 projects by price
        result = self.service.get_top_n_projects(
            region="Chakan",
            city="Pune",
            attribute_path="l1_attributes.price",
            attribute_name="Price",
            n=3,
            ascending=False  # Top (highest values)
        )

        assert result["ranking_type"] == "top"
        assert result["n"] == 3
        assert len(result["projects"]) == 3
        assert result["total_projects"] == 10

        # Check ordering (should be descending for top)
        values = [p["value"] for p in result["projects"]]
        assert values == sorted(values, reverse=True)

        # Get bottom 3 projects
        result_bottom = self.service.get_top_n_projects(
            region="Chakan",
            city="Pune",
            attribute_path="l1_attributes.price",
            attribute_name="Price",
            n=3,
            ascending=True  # Bottom (lowest values)
        )

        assert result_bottom["ranking_type"] == "bottom"
        values_bottom = [p["value"] for p in result_bottom["projects"]]
        assert values_bottom == sorted(values_bottom)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])