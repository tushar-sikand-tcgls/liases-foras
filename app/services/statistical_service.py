"""
Statistical Service for Aggregation Queries

Handles 8 core statistical operations for real estate analysis:
1. TOTAL (SUM) - Aggregate all values
2. AVERAGE (MEAN) - Arithmetic mean value
3. MEDIAN - Middle value (50th percentile)
4. MODE - Most frequent value
5. STANDARD DEVIATION - Measure of spread/volatility
6. VARIANCE - Squared deviation
7. PERCENTILE - P% of data below this value
8. NORMAL DISTRIBUTION - Gaussian curve fit & outlier detection

Real Estate Context:
- Market Analysis: Total market supply, average project size
- Risk Assessment: Volatility, outlier detection
- Benchmarking: Percentile rankings, top performers
- Decision Making: Distribution analysis, typical values
"""
import numpy as np
from scipy import stats
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import math
from app.services.data_service import data_service


class StatisticalService:
    """Service for statistical calculations and aggregations"""

    # Error codes for statistical operations
    ERROR_CODES = {
        201: "Empty dataset - No data provided for analysis",
        202: "Insufficient data - Need at least 2 values for this operation",
        203: "Non-numeric values - Dataset contains non-numeric entries",
        204: "Invalid percentile - Percentile must be between 0 and 100",
        205: "Division by zero - Cannot compute with zero variance",
        206: "Invalid parameter - Check input parameters"
    }

    # Minimum data points for various operations
    MIN_DATA_POINTS = {
        "mode": 1,
        "mean": 1,
        "median": 1,
        "std_dev": 2,
        "variance": 2,
        "normal_test": 8,
        "percentile": 1
    }

    def __init__(self):
        self.data_service = data_service

    def validate_input(
        self,
        values: List[Union[float, int, None]],
        operation: str
    ) -> Tuple[bool, Optional[str], Optional[np.ndarray]]:
        """
        Validate input data for statistical operations

        Args:
            values: Input values
            operation: Statistical operation to perform

        Returns:
            Tuple of (is_valid, error_message, cleaned_array)
        """
        if not values or len(values) == 0:
            return False, self.ERROR_CODES[201], None

        # Remove None and NaN values
        cleaned = [v for v in values if v is not None]

        # Check for non-numeric values
        try:
            arr = np.array([float(v) for v in cleaned if not (isinstance(v, float) and np.isnan(v))])
        except (ValueError, TypeError):
            return False, self.ERROR_CODES[203], None

        if len(arr) == 0:
            return False, self.ERROR_CODES[201], None

        # Check minimum data points requirement
        min_points = self.MIN_DATA_POINTS.get(operation, 1)
        if len(arr) < min_points:
            return False, f"{self.ERROR_CODES[202]} (need {min_points} for {operation})", None

        return True, None, arr

    def calculate_mode(self, values: np.ndarray) -> Dict[str, Any]:
        """
        Calculate mode(s) - most frequent value(s)

        Args:
            values: Numpy array of values

        Returns:
            Dictionary with mode(s) and frequency
        """
        mode_result = stats.mode(values, nan_policy='omit', keepdims=False)

        # Check if multiple modes exist (for multimodal distributions)
        unique, counts = np.unique(values, return_counts=True)
        max_count = np.max(counts)
        all_modes = unique[counts == max_count]

        return {
            "mode": float(mode_result.mode) if np.isscalar(mode_result.mode) else float(mode_result.mode[0]),
            "frequency": int(mode_result.count) if np.isscalar(mode_result.count) else int(mode_result.count[0]),
            "all_modes": [float(m) for m in all_modes],
            "is_multimodal": len(all_modes) > 1
        }

    def calculate_normal_distribution(self, values: np.ndarray) -> Dict[str, Any]:
        """
        Analyze normal distribution properties and detect outliers

        Args:
            values: Numpy array of values

        Returns:
            Dictionary with distribution properties and outlier detection
        """
        mean = np.mean(values)
        std_dev = np.std(values, ddof=1)

        # Z-scores for outlier detection
        z_scores = (values - mean) / std_dev if std_dev > 0 else np.zeros_like(values)

        # Outliers (|z-score| > 2.5)
        outlier_mask = np.abs(z_scores) > 2.5
        outliers = values[outlier_mask]

        # Normality test
        is_normal = False
        p_value = None
        if len(values) >= 8:
            _, p_value = stats.normaltest(values)
            is_normal = p_value > 0.05

        # Calculate confidence intervals (68-95-99.7 rule)
        confidence_intervals = {
            "68%": (mean - std_dev, mean + std_dev),
            "95%": (mean - 2*std_dev, mean + 2*std_dev),
            "99.7%": (mean - 3*std_dev, mean + 3*std_dev)
        }

        return {
            "mean": float(mean),
            "std_dev": float(std_dev),
            "is_normal": is_normal,
            "p_value": float(p_value) if p_value is not None else None,
            "skewness": float(stats.skew(values)),
            "kurtosis": float(stats.kurtosis(values)),
            "outliers": {
                "count": int(np.sum(outlier_mask)),
                "values": [float(o) for o in outliers],
                "z_scores": [float(z) for z in z_scores[outlier_mask]]
            },
            "confidence_intervals": confidence_intervals,
            "coefficient_of_variation": float(std_dev / mean * 100) if mean != 0 else None
        }

    def calculate_series_statistics(
        self,
        values: List[Union[float, int]],
        operations: List[str] = None,
        metric_name: str = "metric",
        context: str = "real_estate"
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics with all 8 operations

        Args:
            values: List of numerical values
            operations: List of operations to perform (default: all 8)
            metric_name: Name of the metric for labeling
            context: Business context (e.g., "real_estate", "market_analysis")

        Returns:
            Comprehensive statistical analysis with business interpretation
        """
        # Default to all operations if not specified
        if operations is None:
            operations = ["TOTAL", "AVERAGE", "MEDIAN", "MODE",
                         "STD_DEV", "VARIANCE", "PERCENTILE", "NORMAL_DIST"]

        # Validate input
        is_valid, error_msg, arr = self.validate_input(values, "comprehensive")
        if not is_valid:
            return {
                "error": error_msg,
                "error_code": 201 if "Empty" in error_msg else 203,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        # Initialize results
        results = {
            "metric_name": metric_name,
            "context": context,
            "data_quality": {
                "original_count": len(values),
                "valid_count": len(arr),
                "missing_count": len(values) - len(arr),
                "quality_score": len(arr) / len(values) * 100  # Percentage
            },
            "operations": {},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Execute requested operations
        if "TOTAL" in operations:
            results["operations"]["total"] = {
                "value": float(np.sum(arr)),
                "formula": "Σ(x_i)",
                "use_case": "Total market supply, revenue aggregation",
                "dimension": "Same as input"
            }

        if "AVERAGE" in operations:
            results["operations"]["average"] = {
                "value": float(np.mean(arr)),
                "formula": "Σ(x) / n",
                "use_case": "Typical project size, average price",
                "dimension": "Same as input"
            }

        if "MEDIAN" in operations:
            results["operations"]["median"] = {
                "value": float(np.median(arr)),
                "formula": "Middle value when sorted",
                "use_case": "Typical value without outlier influence",
                "dimension": "Same as input"
            }

        if "MODE" in operations:
            mode_result = self.calculate_mode(arr)
            results["operations"]["mode"] = {
                **mode_result,
                "formula": "Most frequent value(s)",
                "use_case": "Common price range, popular unit type",
                "dimension": "Same as input"
            }

        if "STD_DEV" in operations and len(arr) >= 2:
            results["operations"]["std_dev"] = {
                "value": float(np.std(arr, ddof=1)),
                "formula": "√[Σ(x-μ)²/(n-1)]",
                "use_case": "Risk assessment, price volatility",
                "dimension": "Same as input"
            }

        if "VARIANCE" in operations and len(arr) >= 2:
            results["operations"]["variance"] = {
                "value": float(np.var(arr, ddof=1)),
                "formula": "Σ(x-μ)²/(n-1)",
                "use_case": "Statistical basis for risk analysis",
                "dimension": "Input²"
            }

        if "PERCENTILE" in operations:
            results["operations"]["percentiles"] = {
                "p10": float(np.percentile(arr, 10)),
                "p25": float(np.percentile(arr, 25)),
                "p50": float(np.percentile(arr, 50)),  # Median
                "p75": float(np.percentile(arr, 75)),
                "p90": float(np.percentile(arr, 90)),
                "formula": "Value at P% position when sorted",
                "use_case": "Top performers, benchmarking analysis",
                "dimension": "Same as input"
            }

        if "NORMAL_DIST" in operations:
            normal_result = self.calculate_normal_distribution(arr)
            results["operations"]["normal_distribution"] = {
                **normal_result,
                "formula": "Gaussian PDF with μ and σ",
                "use_case": "Outlier detection, probability analysis",
                "dimension": "Probability/Z-scores"
            }

        # Add business interpretation based on context
        results["interpretation"] = self._generate_interpretation(results, context)

        return results

    def _generate_interpretation(self, results: Dict, context: str) -> Dict[str, Any]:
        """
        Generate business interpretation of statistical results

        Args:
            results: Statistical calculation results
            context: Business context

        Returns:
            Business interpretation and recommendations
        """
        interpretation = {"insights": [], "recommendations": []}

        ops = results.get("operations", {})

        # Check coefficient of variation for volatility
        if "average" in ops and "std_dev" in ops:
            mean_val = ops["average"]["value"]
            std_val = ops["std_dev"]["value"]
            if mean_val > 0:
                cv = (std_val / mean_val) * 100
                if cv > 30:
                    interpretation["insights"].append(
                        f"High volatility detected (CV={cv:.1f}%). Market shows significant variation."
                    )
                    interpretation["recommendations"].append(
                        "Consider risk mitigation strategies for high market volatility"
                    )
                elif cv < 10:
                    interpretation["insights"].append(
                        f"Low volatility (CV={cv:.1f}%). Market is relatively stable."
                    )

        # Check for outliers
        if "normal_distribution" in ops:
            outlier_count = ops["normal_distribution"]["outliers"]["count"]
            if outlier_count > 0:
                interpretation["insights"].append(
                    f"Detected {outlier_count} outliers that may skew analysis"
                )
                interpretation["recommendations"].append(
                    "Review outlier projects for special circumstances or data quality issues"
                )

        # Compare mean vs median for skewness
        if "average" in ops and "median" in ops:
            mean_val = ops["average"]["value"]
            median_val = ops["median"]["value"]
            if mean_val > median_val * 1.1:
                interpretation["insights"].append(
                    "Right-skewed distribution: High-value outliers pulling average up"
                )
            elif mean_val < median_val * 0.9:
                interpretation["insights"].append(
                    "Left-skewed distribution: Low-value outliers pulling average down"
                )

        return interpretation

    def calculate_statistics(
        self,
        values: List[float],
        metric_name: str = "metric"
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for a list of values (legacy method maintained for compatibility)

        Args:
            values: List of numerical values
            metric_name: Name of the metric for labeling

        Returns:
            Dictionary with statistical measures
        """
        # Use the new comprehensive method with all operations
        return self.calculate_series_statistics(
            values=values,
            operations=["TOTAL", "AVERAGE", "MEDIAN", "MODE", "STD_DEV",
                       "VARIANCE", "PERCENTILE", "NORMAL_DIST"],
            metric_name=metric_name,
            context="general"
        )

    def aggregate_by_region(
        self,
        region: str,
        city: str,
        attribute_path: str,
        attribute_name: str
    ) -> Dict[str, Any]:
        """
        Aggregate a specific attribute across all projects in a region

        Args:
            region: Region/micromarket name
            city: City name
            attribute_path: Path to the attribute (e.g., "l1_attributes.projectSize")
            attribute_name: Human-readable name of the attribute

        Returns:
            Statistical summary + list of projects with values
        """
        # Get all projects in the region
        projects = self._get_projects_by_region(region, city)

        if not projects:
            return {
                "error": f"No projects found in {region}, {city}",
                "region": region,
                "city": city
            }

        # Extract values from each project
        values = []
        project_values = []

        for project in projects:
            value = self._extract_value_by_path(project, attribute_path)
            if value is not None:
                values.append(float(value))
                project_values.append({
                    "projectName": data_service.get_value(project.get("projectName")),
                    "projectId": str(data_service.get_value(project.get("projectId"))),
                    "value": float(value)
                })

        # Calculate statistics
        stats_result = self.calculate_statistics(values, attribute_name)

        return {
            "region": region,
            "city": city,
            "attribute": attribute_name,
            "statistics": stats_result,
            "projects": project_values,
            "project_count": len(project_values)
        }

    def get_top_n_projects(
        self,
        region: str,
        city: str,
        attribute_path: str,
        attribute_name: str,
        n: int = 5,
        ascending: bool = False
    ) -> Dict[str, Any]:
        """
        Get top N (or bottom N if ascending=True) projects by a specific attribute

        Args:
            region: Region/micromarket name
            city: City name
            attribute_path: Path to the attribute
            attribute_name: Human-readable name
            n: Number of projects to return
            ascending: If True, return bottom N (smallest values)

        Returns:
            List of top/bottom N projects with values
        """
        # Get all projects in the region
        projects = self._get_projects_by_region(region, city)

        if not projects:
            return {
                "error": f"No projects found in {region}, {city}",
                "region": region,
                "city": city
            }

        # Extract values
        project_values = []
        for project in projects:
            value = self._extract_value_by_path(project, attribute_path)
            if value is not None:
                project_values.append({
                    "projectName": data_service.get_value(project.get("projectName")),
                    "projectId": str(data_service.get_value(project.get("projectId"))),
                    "value": float(value),
                    "location": data_service.get_value(project.get("location")),
                    "city": data_service.get_value(project.get("city"))
                })

        # Sort
        sorted_projects = sorted(project_values, key=lambda x: x["value"], reverse=not ascending)

        # Take top N
        top_n = sorted_projects[:n]

        return {
            "region": region,
            "city": city,
            "attribute": attribute_name,
            "ranking_type": "bottom" if ascending else "top",
            "n": n,
            "projects": top_n,
            "total_projects": len(project_values)
        }

    def _get_projects_by_region(self, region: str, city: str) -> List[Dict]:
        """
        Get all projects in a specific region/city

        Args:
            region: Region/micromarket name (case-insensitive)
            city: City name (case-insensitive)

        Returns:
            List of project dictionaries
        """
        all_projects = data_service.get_all_projects()
        filtered = []

        region_lower = region.lower().strip()
        city_lower = city.lower().strip() if city else ""

        for project in all_projects:
            project_location = (data_service.get_value(project.get("location", "")) or "").lower().strip()
            project_micromarket = (data_service.get_value(project.get("microMarket", "")) or "").lower().strip()
            project_city = (data_service.get_value(project.get("city", "")) or "").lower().strip()

            # Match if region appears in location or micromarket
            # If city field is empty in project data, ignore city filter
            region_matches = (region_lower in project_location or region_lower in project_micromarket)
            city_matches = (not city_lower) or (not project_city) or (city_lower in project_city)

            if region_matches and city_matches:
                filtered.append(project)

        return filtered

    def _extract_value_by_path(self, project: Dict, path: str) -> Optional[float]:
        """
        Extract a value from a nested dictionary using dot notation

        Args:
            project: Project dictionary
            path: Dot-separated path (e.g., "l1_attributes.projectSize")

        Returns:
            The value if found, else None
        """
        keys = path.split(".")
        current = project

        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return None
            else:
                return None

        # Extract value using data_service if it's a nested dict
        if isinstance(current, dict):
            return data_service.get_value(current)
        else:
            return current


# Singleton instance
statistical_service = StatisticalService()


def get_statistical_service() -> StatisticalService:
    """Get the singleton statistical service instance"""
    return statistical_service
