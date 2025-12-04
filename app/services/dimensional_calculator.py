"""
Dimensional Calculator - Dimensional Analysis Engine
Implements all operations on knowledge graph with automatic layer detection

Key Innovation: Division creates new layers through dimensional analysis
- Layer 0: Raw dimensions (U, L², T, C)
- Layer 1: L0/L0 ratios (C/L² = PSF, C/U = ASP, U/T = Velocity)
- Layer 2: Complex operations on L1
- Layer 3: Optimization
"""

from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass


@dataclass
class Dimension:
    """Represents a dimensional quantity"""
    symbol: str  # U, L², T, C, or composite like "C/L²"
    value: Optional[float] = None
    unit: str = ""
    layer: int = 0
    formula: Optional[str] = None
    name: str = ""


class DimensionalCalculator:
    """
    Dimensional analysis engine that:
    1. Tracks dimensions through operations
    2. Automatically creates new layers for derived metrics
    3. Supports all mathematical and statistical operations
    """

    def __init__(self):
        # Base dimensions (Layer 0)
        self.base_dimensions = {
            'U': {'symbol': 'U', 'name': 'Units', 'unit': 'count', 'layer': 0},
            'L²': {'symbol': 'L²', 'name': 'Area', 'unit': 'sqft', 'layer': 0},
            'T': {'symbol': 'T', 'name': 'Time', 'unit': 'months', 'layer': 0},
            'C': {'symbol': 'C', 'name': 'Cash', 'unit': 'INR', 'layer': 0}
        }

        # Derived dimensions (Layer 1) - Created through division
        self.derived_dimensions = {
            'C/L²': {
                'symbol': 'C/L²',
                'name': 'PricePerSqft',
                'unit': 'INR/sqft',
                'formula': 'C ÷ L²',
                'layer': 1,
                'components': {'numerator': 'C', 'denominator': 'L²'}
            },
            'C/U': {
                'symbol': 'C/U',
                'name': 'AverageSellingPrice',
                'unit': 'INR/unit',
                'formula': 'C ÷ U',
                'layer': 1,
                'components': {'numerator': 'C', 'denominator': 'U'}
            },
            'U/T': {
                'symbol': 'U/T',
                'name': 'SalesVelocity',
                'unit': 'units/month',
                'formula': 'U ÷ T',
                'layer': 1,
                'components': {'numerator': 'U', 'denominator': 'T'}
            },
            '1/T': {
                'symbol': '1/T',
                'name': 'Rate',
                'unit': '1/month',
                'formula': '1 ÷ T',
                'layer': 1,
                'components': {'numerator': '1', 'denominator': 'T'}
            },
            'L²/U': {
                'symbol': 'L²/U',
                'name': 'AreaPerUnit',
                'unit': 'sqft/unit',
                'formula': 'L² ÷ U',
                'layer': 1,
                'components': {'numerator': 'L²', 'denominator': 'U'}
            },
            'C/T': {
                'symbol': 'C/T',
                'name': 'CashFlowRate',
                'unit': 'INR/month',
                'formula': 'C ÷ T',
                'layer': 1,
                'components': {'numerator': 'C', 'denominator': 'T'}
            }
        }

    # ============================================================================
    # A. BASIC MATH OPERATIONS
    # ============================================================================

    def add(self, dim1: Dimension, dim2: Dimension) -> Dimension:
        """
        Addition: Only works for same dimensions
        U + U = U (same layer)
        C/L² + C/L² = C/L² (same layer)
        """
        if dim1.symbol != dim2.symbol:
            raise ValueError(f"Cannot add different dimensions: {dim1.symbol} + {dim2.symbol}")

        return Dimension(
            symbol=dim1.symbol,
            value=(dim1.value or 0) + (dim2.value or 0),
            unit=dim1.unit,
            layer=dim1.layer,
            formula=f"({dim1.value} + {dim2.value})",
            name=dim1.name
        )

    def subtract(self, dim1: Dimension, dim2: Dimension) -> Dimension:
        """
        Subtraction: Only works for same dimensions
        C - C = C
        """
        if dim1.symbol != dim2.symbol:
            raise ValueError(f"Cannot subtract different dimensions: {dim1.symbol} - {dim2.symbol}")

        return Dimension(
            symbol=dim1.symbol,
            value=(dim1.value or 0) - (dim2.value or 0),
            unit=dim1.unit,
            layer=dim1.layer,
            formula=f"({dim1.value} - {dim2.value})",
            name=dim1.name
        )

    def multiply(self, dim1: Dimension, dim2: Dimension) -> Dimension:
        """
        Multiplication: Creates composite dimensions
        C × T = C·T (composite dimension)
        U × L² = U·L² (composite dimension)

        Note: Rarely used in real estate, but supported
        """
        new_symbol = f"{dim1.symbol}·{dim2.symbol}"
        new_unit = f"{dim1.unit}·{dim2.unit}"
        new_layer = max(dim1.layer, dim2.layer)  # Higher layer wins

        return Dimension(
            symbol=new_symbol,
            value=(dim1.value or 0) * (dim2.value or 0),
            unit=new_unit,
            layer=new_layer,
            formula=f"({dim1.symbol} × {dim2.symbol})",
            name=f"{dim1.name} times {dim2.name}"
        )

    def divide(self, numerator: Dimension, denominator: Dimension) -> Dimension:
        """
        Division: CREATES NEW LAYERS (Key operation!)

        Layer 0 ÷ Layer 0 → Layer 1:
        - C ÷ L² = PSF (Price per sqft)
        - C ÷ U = ASP (Average selling price)
        - U ÷ T = Sales Velocity

        Layer 1 ÷ Layer 0 → Layer 2:
        - (C/U) ÷ (L²/U) = C/L² = PSF (normalization)

        This is dimensional analysis in action!
        """
        if denominator.value == 0:
            raise ValueError("Division by zero")

        # Calculate new dimension symbol
        new_symbol = self._simplify_dimension_division(numerator.symbol, denominator.symbol)

        # Determine layer
        new_layer = self._determine_layer_from_division(numerator, denominator, new_symbol)

        # Get unit
        new_unit = self._calculate_unit(numerator.unit, denominator.unit, operation='divide')

        # Check if this is a known derived dimension
        derived_info = self.derived_dimensions.get(new_symbol, {})

        return Dimension(
            symbol=new_symbol,
            value=(numerator.value or 0) / (denominator.value or 0),
            unit=new_unit or derived_info.get('unit', f"{numerator.unit}/{denominator.unit}"),
            layer=new_layer,
            formula=f"({numerator.symbol} ÷ {denominator.symbol})",
            name=derived_info.get('name', f"{numerator.name} per {denominator.name}")
        )

    def _simplify_dimension_division(self, num_symbol: str, den_symbol: str) -> str:
        """
        Simplify dimensional division
        C/L² is already simplified
        (C/L²)/(U) = C/(L²·U) = C/L²U
        """
        # Handle simple cases
        if num_symbol == den_symbol:
            return '1'  # Dimensionless

        # Handle compound divisions
        if '/' in num_symbol and '/' not in den_symbol:
            # (A/B) / C = A/(B·C)
            parts = num_symbol.split('/')
            return f"{parts[0]}/{parts[1]}·{den_symbol}"
        elif '/' not in num_symbol and '/' in den_symbol:
            # A / (B/C) = A·C/B
            parts = den_symbol.split('/')
            return f"{num_symbol}·{parts[1]}/{parts[0]}"
        else:
            # Simple division
            return f"{num_symbol}/{den_symbol}"

    def _determine_layer_from_division(self, num: Dimension, den: Dimension, result_symbol: str) -> int:
        """
        Determine which layer a division result belongs to

        Rules:
        - L0 ÷ L0 → L1 (derived metric)
        - L1 ÷ L0 → L2 (complex metric)
        - L2 ÷ L1 → L3 (optimization metric)
        """
        # Check if result is a known Layer 1 derived dimension
        if result_symbol in self.derived_dimensions:
            return 1

        # General rule: max layer + 1 (capped at 3)
        new_layer = max(num.layer, den.layer) + 1
        return min(new_layer, 3)

    def _calculate_unit(self, unit1: str, unit2: str, operation: str) -> str:
        """Calculate resulting unit from operation"""
        if operation == 'divide':
            if unit1 == unit2:
                return ''  # Dimensionless
            return f"{unit1}/{unit2}"
        elif operation == 'multiply':
            return f"{unit1}·{unit2}"
        else:
            return unit1

    # ============================================================================
    # B. STATISTICAL OPERATIONS
    # ============================================================================

    def mean(self, values: List[Dimension]) -> Dimension:
        """Calculate mean (average) of dimensional values"""
        if not values:
            raise ValueError("Cannot calculate mean of empty list")

        # Check all same dimension
        base_dim = values[0]
        if not all(v.symbol == base_dim.symbol for v in values):
            raise ValueError("All values must have same dimension for mean")

        total = sum(v.value or 0 for v in values)
        count = len(values)

        return Dimension(
            symbol=base_dim.symbol,
            value=total / count,
            unit=base_dim.unit,
            layer=base_dim.layer,
            formula=f"mean({base_dim.symbol})",
            name=f"Mean {base_dim.name}"
        )

    def median(self, values: List[Dimension]) -> Dimension:
        """Calculate median of dimensional values"""
        if not values:
            raise ValueError("Cannot calculate median of empty list")

        base_dim = values[0]
        sorted_values = sorted([v.value or 0 for v in values])
        n = len(sorted_values)

        if n % 2 == 0:
            median_val = (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            median_val = sorted_values[n//2]

        return Dimension(
            symbol=base_dim.symbol,
            value=median_val,
            unit=base_dim.unit,
            layer=base_dim.layer,
            formula=f"median({base_dim.symbol})",
            name=f"Median {base_dim.name}"
        )

    def standard_deviation(self, values: List[Dimension]) -> Dimension:
        """Calculate standard deviation"""
        if not values or len(values) < 2:
            raise ValueError("Need at least 2 values for standard deviation")

        mean_val = self.mean(values)
        variance = sum((v.value - mean_val.value) ** 2 for v in values) / (len(values) - 1)
        stdev = variance ** 0.5

        base_dim = values[0]
        return Dimension(
            symbol=base_dim.symbol,
            value=stdev,
            unit=base_dim.unit,
            layer=base_dim.layer,
            formula=f"stdev({base_dim.symbol})",
            name=f"StdDev {base_dim.name}"
        )

    def quartiles(self, values: List[Dimension]) -> Dict[str, Dimension]:
        """Calculate Q1, Q2 (median), Q3"""
        if not values:
            raise ValueError("Cannot calculate quartiles of empty list")

        base_dim = values[0]
        sorted_values = sorted([v.value or 0 for v in values])
        n = len(sorted_values)

        def percentile(data, p):
            k = (n - 1) * p
            f = int(k)
            c = k - f
            if f + 1 < n:
                return data[f] + c * (data[f + 1] - data[f])
            return data[f]

        return {
            'Q1': Dimension(base_dim.symbol, percentile(sorted_values, 0.25), base_dim.unit, base_dim.layer),
            'Q2': Dimension(base_dim.symbol, percentile(sorted_values, 0.5), base_dim.unit, base_dim.layer),
            'Q3': Dimension(base_dim.symbol, percentile(sorted_values, 0.75), base_dim.unit, base_dim.layer)
        }

    # ============================================================================
    # C. SQL-LIKE OPERATIONS
    # ============================================================================

    def filter_where(self, values: List[Dimension], condition: str) -> List[Dimension]:
        """
        SQL WHERE clause equivalent
        condition: ">100", "<=50", "==200", "!=0", "BETWEEN 50 AND 200"
        """
        if not values:
            return []

        filtered = []

        # Parse BETWEEN clause
        if 'BETWEEN' in condition.upper():
            match = re.search(r'BETWEEN\s+(\d+\.?\d*)\s+AND\s+(\d+\.?\d*)', condition, re.IGNORECASE)
            if match:
                low, high = float(match.group(1)), float(match.group(2))
                filtered = [v for v in values if low <= (v.value or 0) <= high]
        else:
            # Parse comparison operators
            operators = {
                '>=': lambda x, y: x >= y,
                '<=': lambda x, y: x <= y,
                '>': lambda x, y: x > y,
                '<': lambda x, y: x < y,
                '==': lambda x, y: x == y,
                '!=': lambda x, y: x != y
            }

            for op_str, op_func in operators.items():
                if op_str in condition:
                    threshold = float(condition.replace(op_str, '').strip())
                    filtered = [v for v in values if op_func(v.value or 0, threshold)]
                    break

        return filtered

    def group_by(self, data: List[Dict], group_field: str, agg_field: str, agg_func: str = 'mean') -> Dict:
        """
        SQL GROUP BY equivalent

        Args:
            data: List of dicts with dimensions
            group_field: Field to group by (e.g., 'city')
            agg_field: Field to aggregate (e.g., 'totalUnits')
            agg_func: 'mean', 'sum', 'count', 'min', 'max'

        Returns:
            Dict[group_value] → aggregated Dimension
        """
        from collections import defaultdict

        grouped = defaultdict(list)

        # Group data
        for item in data:
            group_val = item.get(group_field)
            dim_val = item.get(agg_field)
            if group_val and dim_val:
                grouped[group_val].append(dim_val)

        # Aggregate each group
        result = {}
        for group_val, dims in grouped.items():
            if agg_func == 'mean':
                result[group_val] = self.mean(dims)
            elif agg_func == 'sum':
                result[group_val] = self.add(dims[0], dims[1]) if len(dims) > 1 else dims[0]
            elif agg_func == 'count':
                result[group_val] = Dimension('count', len(dims), 'count', 0)
            elif agg_func == 'min':
                result[group_val] = min(dims, key=lambda d: d.value or 0)
            elif agg_func == 'max':
                result[group_val] = max(dims, key=lambda d: d.value or 0)

        return result

    def having(self, grouped_data: Dict[str, Dimension], condition: str) -> Dict[str, Dimension]:
        """
        SQL HAVING clause (filter after GROUP BY)
        condition: Same as WHERE clause
        """
        result = {}

        # Convert to list for filtering
        for group_val, dim in grouped_data.items():
            filtered = self.filter_where([dim], condition)
            if filtered:
                result[group_val] = dim

        return result

    # ============================================================================
    # D. PROGRAMMING CONSTRUCTS
    # ============================================================================

    def if_then_else(self, condition: bool, if_dim: Dimension, else_dim: Dimension) -> Dimension:
        """
        If-then-else conditional
        Used for conditional calculations
        """
        return if_dim if condition else else_dim

    def loop_map(self, values: List[Dimension], operation: callable) -> List[Dimension]:
        """
        Map operation over list (functional loop)
        Example: Apply scaling factor to all values
        """
        return [operation(v) for v in values]

    def loop_reduce(self, values: List[Dimension], operation: callable, initial: Dimension) -> Dimension:
        """
        Reduce operation (fold)
        Example: Sum all values
        """
        result = initial
        for v in values:
            result = operation(result, v)
        return result

    # ============================================================================
    # LAYER DETECTION AND NAMING
    # ============================================================================

    def detect_layer_from_operation(self, operation: str, operands: List[Dimension]) -> int:
        """
        Automatically detect which layer an operation result belongs to

        Rules:
        - Operations on L0 only → L0 (sum of units)
        - L0 ÷ L0 → L1 (derived metric)
        - Operations on L1 → L2 (complex financial)
        - Operations on L2 → L3 (optimization)
        """
        if operation == 'divide':
            # Division creates new layer
            max_layer = max(op.layer for op in operands)
            return min(max_layer + 1, 3)
        else:
            # Other operations stay in same layer
            return max(op.layer for op in operands)

    def name_derived_dimension(self, symbol: str) -> str:
        """
        Automatically name derived dimensions

        Examples:
        - C/L² → "Price Per Sqft"
        - U/T → "Sales Velocity"
        - C/U → "Average Selling Price"
        """
        if symbol in self.derived_dimensions:
            return self.derived_dimensions[symbol]['name']

        # Generate name from components
        if '/' in symbol:
            num, den = symbol.split('/', 1)
            num_name = self.base_dimensions.get(num, {}).get('name', num)
            den_name = self.base_dimensions.get(den, {}).get('name', den)
            return f"{num_name} per {den_name}"

        return symbol


# =============================================================================
# CYPHER QUERY GENERATOR WITH DIMENSIONAL AWARENESS
# =============================================================================

class DimensionalCypherGenerator:
    """
    Generates Cypher queries with dimensional analysis

    Automatically detects:
    - Which layer to query
    - What operations to apply
    - How to handle derived dimensions
    """

    def __init__(self, calculator: DimensionalCalculator):
        self.calc = calculator

    def generate_division_query(self, numerator: str, denominator: str,
                                neo4j_num_field: str, neo4j_den_field: str) -> str:
        """
        Generate Cypher for division operation (creates Layer 1)

        Example:
        numerator='C', denominator='L²'
        → Creates PSF (Price Per Sqft)
        """
        return f"""
        MATCH (p:Project)
        WHERE p.{neo4j_num_field} IS NOT NULL AND p.{neo4j_den_field} IS NOT NULL
        WITH p,
             p.{neo4j_num_field} AS numerator_val,
             p.{neo4j_den_field} AS denominator_val,
             p.{neo4j_num_field} / p.{neo4j_den_field} AS derived_val
        RETURN p.projectName AS project,
               derived_val AS result,
               '{numerator}/{denominator}' AS dimension,
               collect(derived_val) AS all_values,
               avg(derived_val) AS mean,
               stdev(derived_val) AS stdev
        """

    def generate_statistical_query(self, dimension: str, neo4j_field: str,
                                   stat_operation: str) -> str:
        """
        Generate Cypher for statistical operations

        stat_operation: 'mean', 'median', 'stdev', 'quartiles'
        """
        if stat_operation == 'quartiles':
            return f"""
            MATCH (p:Project)
            WHERE p.{neo4j_field} IS NOT NULL
            RETURN percentileCont(p.{neo4j_field}, 0.25) AS Q1,
                   percentileCont(p.{neo4j_field}, 0.5) AS Q2,
                   percentileCont(p.{neo4j_field}, 0.75) AS Q3,
                   collect(p.{neo4j_field}) AS values
            """
        else:
            agg_map = {
                'mean': 'avg',
                'median': 'percentileCont(p.{}, 0.5)',
                'stdev': 'stdev'
            }
            agg_func = agg_map.get(stat_operation, 'avg')

            return f"""
            MATCH (p:Project)
            WHERE p.{neo4j_field} IS NOT NULL
            RETURN {agg_func}(p.{neo4j_field}) AS result,
                   '{dimension}' AS dimension,
                   count(p) AS count,
                   collect(p.{neo4j_field}) AS values
            """
