"""
JSON Schema Analyzer for Dynamic Widget System

Analyzes JSON structures to detect patterns and extract metadata
for automatic widget generation.
"""

from typing import Any, Dict, List, Set
from dataclasses import dataclass


@dataclass
class StructureMetadata:
    """Metadata about a JSON structure"""
    data_type: str  # "dict", "list", "primitive", "nested"
    keys: List[str]  # Keys if dict
    patterns: List[str]  # Detected patterns
    cardinality: int  # Length if list, count if dict
    nesting_level: int
    has_numeric_values: bool
    has_nested_dicts: bool
    has_lists: bool


class SchemaAnalyzer:
    """Analyzes JSON structures and extracts metadata"""
    
    # Pattern detection keywords
    SCENARIO_KEYWORDS = {"baseCase", "optimisticCase", "stressCase", "scenario"}
    UNIT_MIX_KEYWORDS = {"1BHK", "2BHK", "3BHK"}
    METRIC_KEYWORDS = {"metric", "value", "unit", "dimension"}
    OPTIMIZATION_KEYWORDS = {"optimal_mix", "scenarios", "units_breakdown"}
    TIME_SERIES_KEYWORDS = {"annual", "monthly", "cashFlows", "timeline"}
    MARKET_KEYWORDS = {"oppsScore", "demandTrend", "recommendedMix"}
    
    def analyze(self, data: Any, path: str = "", level: int = 0) -> StructureMetadata:
        """
        Analyze JSON structure and return metadata
        
        Args:
            data: JSON data to analyze
            path: Current path in structure (for debugging)
            level: Nesting level
        
        Returns:
            StructureMetadata object
        """
        if isinstance(data, dict):
            return self._analyze_dict(data, path, level)
        elif isinstance(data, list):
            return self._analyze_list(data, path, level)
        else:
            return self._analyze_primitive(data, path, level)
    
    def _analyze_dict(self, data: Dict, path: str, level: int) -> StructureMetadata:
        """Analyze dictionary structure"""
        keys = list(data.keys())
        patterns = self._detect_patterns(set(keys))
        
        # Check for nested structures
        has_nested_dicts = any(isinstance(v, dict) for v in data.values())
        has_lists = any(isinstance(v, list) for v in data.values())
        has_numeric = any(isinstance(v, (int, float)) for v in data.values())
        
        return StructureMetadata(
            data_type="dict",
            keys=keys,
            patterns=patterns,
            cardinality=len(keys),
            nesting_level=level,
            has_numeric_values=has_numeric,
            has_nested_dicts=has_nested_dicts,
            has_lists=has_lists
        )
    
    def _analyze_list(self, data: List, path: str, level: int) -> StructureMetadata:
        """Analyze list structure"""
        if not data:
            return StructureMetadata(
                data_type="list",
                keys=[],
                patterns=[],
                cardinality=0,
                nesting_level=level,
                has_numeric_values=False,
                has_nested_dicts=False,
                has_lists=False
            )
        
        # Analyze first item to determine list type
        first_item = data[0]
        item_type = type(first_item).__name__
        
        patterns = []
        if isinstance(first_item, dict):
            patterns.append("list_of_dicts")
            # Check if items have scenario-like structure
            if any(key in self.SCENARIO_KEYWORDS for key in first_item.keys()):
                patterns.append("scenario_list")
        
        return StructureMetadata(
            data_type="list",
            keys=[],
            patterns=patterns,
            cardinality=len(data),
            nesting_level=level,
            has_numeric_values=isinstance(first_item, (int, float)),
            has_nested_dicts=isinstance(first_item, dict),
            has_lists=isinstance(first_item, list)
        )
    
    def _analyze_primitive(self, data: Any, path: str, level: int) -> StructureMetadata:
        """Analyze primitive value"""
        return StructureMetadata(
            data_type=type(data).__name__,
            keys=[],
            patterns=[],
            cardinality=1,
            nesting_level=level,
            has_numeric_values=isinstance(data, (int, float)),
            has_nested_dicts=False,
            has_lists=False
        )
    
    def _detect_patterns(self, keys: Set[str]) -> List[str]:
        """
        Detect patterns in dictionary keys
        
        Args:
            keys: Set of dictionary keys
        
        Returns:
            List of detected pattern names
        """
        patterns = []
        
        # Scenario comparison pattern
        scenario_overlap = keys & self.SCENARIO_KEYWORDS
        if len(scenario_overlap) >= 2:  # At least 2 scenario keys
            patterns.append("scenario_comparison")
        
        # Unit mix pattern
        if keys & self.UNIT_MIX_KEYWORDS:
            if len(keys & self.UNIT_MIX_KEYWORDS) >= 2:
                patterns.append("unit_mix")
        
        # Metric result pattern
        if keys & self.METRIC_KEYWORDS:
            if len(keys & self.METRIC_KEYWORDS) >= 3:
                patterns.append("metric_result")
        
        # Optimization result pattern
        if keys & self.OPTIMIZATION_KEYWORDS:
            if len(keys & self.OPTIMIZATION_KEYWORDS) >= 2:
                patterns.append("optimization_result")
        
        # Time series pattern
        if keys & self.TIME_SERIES_KEYWORDS:
            patterns.append("time_series")
        
        # Market opportunity pattern
        if keys & self.MARKET_KEYWORDS:
            if len(keys & self.MARKET_KEYWORDS) >= 2:
                patterns.append("market_opportunity")
        
        return patterns
