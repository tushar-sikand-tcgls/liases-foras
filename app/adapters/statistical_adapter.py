"""
Statistical Analysis Adapter - Implements statistical operations

This adapter provides statistical analysis capabilities (average, aggregation,
percentiles) across projects using the hexagonal architecture ports.
"""

from typing import Dict, List, Optional
import statistics
from app.ports.input_ports import StatisticalAnalysisPort
from app.adapters.formula_adapter import FormulaServiceAdapter
from app.adapters.project_adapter import ProjectServiceAdapter


class StatisticalAnalysisAdapter(StatisticalAnalysisPort):
    """
    Adapter that implements statistical analysis operations

    Uses:
    - FormulaServiceAdapter to resolve attribute definitions
    - ProjectServiceAdapter to access project data

    Implements:
    - StatisticalAnalysisPort (input port for statistical operations)
    """

    def __init__(self):
        self.formula_adapter = FormulaServiceAdapter()
        self.project_adapter = ProjectServiceAdapter()

    def _extract_attribute_values(
        self,
        attribute_name: str,
        projects: List[Dict]
    ) -> List[float]:
        """
        Extract attribute values from a list of projects

        Handles both direct extraction (L0) and calculated (L1/L2) attributes
        """
        values = []

        for project in projects:
            # Use formula adapter to calculate/extract the attribute
            result = self.formula_adapter.calculate(attribute_name, project)

            if result and result.get('value') is not None:
                value = result['value']

                # Convert to float if possible
                try:
                    if isinstance(value, str):
                        # Remove commas and convert
                        value = float(value.replace(',', ''))
                    else:
                        value = float(value)

                    values.append(value)
                except (ValueError, TypeError):
                    # Skip non-numeric values
                    continue

        return values

    def calculate_average(
        self,
        attribute_name: str,
        projects: List[Dict]
    ) -> float:
        """
        Calculate average of an attribute across projects

        Args:
            attribute_name: Name of the attribute to average
            projects: List of project dictionaries

        Returns:
            Average value as float

        Raises:
            ValueError: If no valid values found or projects list is empty
        """
        if not projects:
            raise ValueError("Projects list cannot be empty")

        values = self._extract_attribute_values(attribute_name, projects)

        if not values:
            raise ValueError(f"No valid numeric values found for attribute '{attribute_name}'")

        return statistics.mean(values)

    def calculate_aggregation(
        self,
        attribute_name: str,
        aggregation_type: str,
        projects: List[Dict]
    ) -> float:
        """
        Calculate aggregation of an attribute

        Args:
            attribute_name: Name of the attribute
            aggregation_type: Type of aggregation ('sum', 'mean', 'median', 'max', 'min')
            projects: List of project dictionaries

        Returns:
            Aggregated value as float

        Raises:
            ValueError: If aggregation_type is invalid or no valid values found
        """
        if not projects:
            raise ValueError("Projects list cannot be empty")

        values = self._extract_attribute_values(attribute_name, projects)

        if not values:
            raise ValueError(f"No valid numeric values found for attribute '{attribute_name}'")

        aggregation_type = aggregation_type.lower()

        if aggregation_type == 'sum':
            return sum(values)
        elif aggregation_type == 'mean':
            return statistics.mean(values)
        elif aggregation_type == 'median':
            return statistics.median(values)
        elif aggregation_type == 'max':
            return max(values)
        elif aggregation_type == 'min':
            return min(values)
        else:
            raise ValueError(
                f"Invalid aggregation_type '{aggregation_type}'. "
                f"Must be one of: 'sum', 'mean', 'median', 'max', 'min'"
            )

    def calculate_percentile(
        self,
        attribute_name: str,
        percentile: float,
        projects: List[Dict]
    ) -> float:
        """
        Calculate percentile value for an attribute

        Args:
            attribute_name: Name of the attribute
            percentile: Percentile to calculate (0-100)
            projects: List of project dictionaries

        Returns:
            Percentile value as float

        Raises:
            ValueError: If percentile is out of range or no valid values found
        """
        if not projects:
            raise ValueError("Projects list cannot be empty")

        if not 0 <= percentile <= 100:
            raise ValueError(f"Percentile must be between 0 and 100, got {percentile}")

        values = self._extract_attribute_values(attribute_name, projects)

        if not values:
            raise ValueError(f"No valid numeric values found for attribute '{attribute_name}'")

        # Use statistics.quantiles for percentile calculation
        # quantiles divides data into n equal groups, so for percentile we use 100 groups
        if percentile == 0:
            return min(values)
        elif percentile == 100:
            return max(values)
        else:
            # Convert percentile to quantile (0-1 scale)
            return statistics.quantiles(values, n=100)[int(percentile) - 1]

    def get_statistics_summary(
        self,
        attribute_name: str,
        projects: List[Dict]
    ) -> Dict:
        """
        Get comprehensive statistical summary for an attribute

        Returns:
            Dictionary with mean, median, min, max, std_dev, percentiles
        """
        if not projects:
            raise ValueError("Projects list cannot be empty")

        values = self._extract_attribute_values(attribute_name, projects)

        if not values:
            raise ValueError(f"No valid numeric values found for attribute '{attribute_name}'")

        summary = {
            'attribute': attribute_name,
            'count': len(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
        }

        # Add standard deviation if we have more than 1 value
        if len(values) > 1:
            summary['std_dev'] = statistics.stdev(values)
        else:
            summary['std_dev'] = 0.0

        # Add common percentiles
        if len(values) >= 4:  # Need at least 4 values for quartiles
            try:
                summary['percentiles'] = {
                    'p25': self.calculate_percentile(attribute_name, 25, projects),
                    'p50': self.calculate_percentile(attribute_name, 50, projects),
                    'p75': self.calculate_percentile(attribute_name, 75, projects),
                    'p90': self.calculate_percentile(attribute_name, 90, projects),
                    'p95': self.calculate_percentile(attribute_name, 95, projects),
                }
            except Exception:
                # If percentile calculation fails, skip it
                summary['percentiles'] = {}
        else:
            summary['percentiles'] = {}

        return summary
