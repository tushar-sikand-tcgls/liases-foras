#!/usr/bin/env python3
"""
JSON Data Store with Dimensional Relationships
Clean, simple alternative to Neo4j that preserves nested structure

Author: Claude Code
Date: 2025-11-30
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Add scripts directory to import dimension_parser
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))
from dimension_parser import DimensionParser
from app.utils.fuzzy_matcher import FuzzyMatcher


class JSONDataStore:
    """
    Simple JSON-based data store that preserves nested {value, unit, dimension} structure
    Provides dimensional query capabilities without Neo4j complexity
    """

    def __init__(self, data_path: str = None):
        """Initialize data store from JSON file"""
        if data_path is None:
            data_path = Path(__file__).parent.parent.parent / "data" / "extracted" / "v4_clean_nested_structure.json"

        self.data_path = data_path
        self.parser = DimensionParser()
        self.data = self._load_data()

        # Build indexes for fast lookups
        self.projects_by_id = {}
        self.projects_by_name = {}  # Original name lookup
        self.projects_by_normalized_name = {}  # Normalized name lookup (handles newlines/spaces)
        self._build_indexes()

    def _load_data(self) -> Dict:
        """Load data from JSON file"""
        with open(self.data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _build_indexes(self):
        """Build lookup indexes for fast queries"""
        for project in self.data.get('page_2_projects', []):
            # Extract values (handle both nested dict structure and plain values)
            project_id_obj = project.get('projectId')
            project_name_obj = project.get('projectName')

            project_id = project_id_obj.get('value') if isinstance(project_id_obj, dict) else project_id_obj
            project_name = project_name_obj.get('value') if isinstance(project_name_obj, dict) else project_name_obj

            if project_id:
                self.projects_by_id[project_id] = project
            if project_name:
                # Store by original name
                self.projects_by_name[project_name] = project

                # Also store by normalized name (replaces newlines with spaces, lowercase, etc.)
                normalized_name = FuzzyMatcher.normalize(project_name)
                self.projects_by_normalized_name[normalized_name] = project

    def transform_to_nested_structure(self, node_data: Dict) -> Dict:
        """
        Transform from current structure to clean nested structure

        Input:
        {
            "projectName": "Sara City",
            "l1_attributes": {
                "currentPricePSF": {
                    "value": 3996,
                    "unit": "INR/sqft",
                    "dimension": "C/L²"
                }
            }
        }

        Output:
        {
            "projectName": {
                "value": "Sara City",
                "unit": "Text",
                "dimension": "None"
            },
            "currentPricePSF": {
                "value": 3996,
                "unit": "INR/sqft",
                "dimension": "C/L²"
            }
        }
        """
        nested = {}

        # Transform basic properties
        basic_props = {
            'projectId': ('Integer', 'None'),
            'projectName': ('Text', 'None'),
            'developerName': ('Text', 'None'),
            'location': ('Text', 'None'),
            'layer': ('Text', 'None'),
            'nodeType': ('Text', 'None'),
            'priorityWeight': ('Integer', 'None'),
            'extractionTimestamp': ('Text', 'None'),
            'priority_weight': ('Integer', 'None'),
            'extraction_timestamp': ('Text', 'None'),
            'flat_type': ('Text', 'None'),
            'quarter_label': ('Text', 'None'),
        }

        for prop, (unit, dimension) in basic_props.items():
            if prop in node_data:
                nested[prop] = {
                    "value": node_data[prop],
                    "unit": unit,
                    "dimension": dimension
                }

        # Transform L1 attributes (already in correct structure)
        l1_attrs = node_data.get('l1_attributes', {})
        for attr_name, attr_data in l1_attrs.items():
            nested[attr_name] = attr_data

        return nested

    def get_project_by_name(self, project_name: str) -> Optional[Dict]:
        """
        Get project with nested structure

        Tries multiple matching strategies:
        1. Exact match on original name
        2. Normalized match (handles newlines, spaces, case)
        """
        # Try exact match first
        project = self.projects_by_name.get(project_name)
        if project:
            return self.transform_to_nested_structure(project)

        # Try normalized match (handles "Sara\nAbhiruchi\nTower" matching "Sara Abhiruchi Tower")
        normalized_query = FuzzyMatcher.normalize(project_name)
        project = self.projects_by_normalized_name.get(normalized_query)
        if project:
            return self.transform_to_nested_structure(project)

        return None

    def get_project_by_id(self, project_id: int) -> Optional[Dict]:
        """Get project with nested structure"""
        project = self.projects_by_id.get(project_id)
        if project:
            return self.transform_to_nested_structure(project)
        return None

    def get_all_projects(self) -> List[Dict]:
        """Get all projects with nested structure"""
        return [self.transform_to_nested_structure(p) for p in self.data.get('page_2_projects', [])]

    def get_attribute_value(self, project_name: str, attribute: str) -> Optional[Dict]:
        """Get a specific attribute value with metadata"""
        project = self.get_project_by_name(project_name)
        if project and attribute in project:
            return project[attribute]
        return None

    def find_attributes_by_dimension(self, dimension_formula: str, node_type: str = "all") -> List[Dict]:
        """
        Find all attributes matching a dimensional formula

        Args:
            dimension_formula: e.g., "U", "C/L²", "1/T"
            node_type: "project", "unit_type", "quarterly", or "all"

        Returns:
            List of {nodeType, nodeName, attribute, value, unit, dimension}
        """
        results = []

        # Search projects
        if node_type in ["project", "all"]:
            for project in self.data.get('page_2_projects', []):
                nested = self.transform_to_nested_structure(project)
                for attr_name, attr_data in nested.items():
                    if attr_data.get('dimension') == dimension_formula:
                        results.append({
                            'nodeType': 'Project_L1',
                            'nodeName': project.get('projectName'),
                            'attribute': attr_name,
                            'value': attr_data.get('value'),
                            'unit': attr_data.get('unit'),
                            'dimension': attr_data.get('dimension')
                        })

        # Search unit types
        if node_type in ["unit_type", "all"]:
            for unit_type in self.data.get('page_5_unit_types', []):
                nested = self.transform_to_nested_structure(unit_type)
                for attr_name, attr_data in nested.items():
                    if attr_data.get('dimension') == dimension_formula:
                        results.append({
                            'nodeType': 'UnitType_L1',
                            'nodeName': unit_type.get('flat_type', 'Unknown'),
                            'attribute': attr_name,
                            'value': attr_data.get('value'),
                            'unit': attr_data.get('unit'),
                            'dimension': attr_data.get('dimension')
                        })

        # Search quarterly summaries
        if node_type in ["quarterly", "all"]:
            for quarter in self.data.get('page_8_quarterly_summary', []):
                nested = self.transform_to_nested_structure(quarter)
                for attr_name, attr_data in nested.items():
                    if attr_data.get('dimension') == dimension_formula:
                        results.append({
                            'nodeType': 'QuarterlySummary_L1',
                            'nodeName': quarter.get('quarter_label', 'Unknown'),
                            'attribute': attr_name,
                            'value': attr_data.get('value'),
                            'unit': attr_data.get('unit'),
                            'dimension': attr_data.get('dimension')
                        })

        return results

    def get_dimensional_profile(self, project_name: str) -> Dict[str, List[Dict]]:
        """
        Get dimensional profile of a project grouped by base dimensions

        Returns:
            {
                "U": [{attribute: "totalSupplyUnits", value: 1109, ...}, ...],
                "L²": [...],
                "T": [...],
                "C": [...],
                "Composite": [{attribute: "currentPricePSF", dimension: "C/L²", ...}],
                "Dimensionless": [...]
            }
        """
        project = self.get_project_by_name(project_name)
        if not project:
            return {}

        profile = {
            "U": [],
            "L²": [],
            "T": [],
            "C": [],
            "Composite": [],
            "Dimensionless": []
        }

        for attr_name, attr_data in project.items():
            dimension = attr_data.get('dimension', 'None')

            attr_info = {
                'attribute': attr_name,
                'value': attr_data.get('value'),
                'unit': attr_data.get('unit'),
                'dimension': dimension
            }

            # Parse dimension to determine category
            relationships = self.parser.parse_dimension(dimension)

            if not relationships:
                profile['Dimensionless'].append(attr_info)
            elif len(relationships) == 1 and relationships[0]['type'] == 'IS':
                # Simple dimension
                base_dim = relationships[0]['target']
                profile[base_dim].append(attr_info)
            else:
                # Composite dimension
                profile['Composite'].append(attr_info)

        return profile

    def compare_projects(self, project_names: List[str], attributes: List[str] = None) -> Dict:
        """
        Compare multiple projects on specific attributes

        Args:
            project_names: List of project names to compare
            attributes: List of attributes to compare (if None, compare all)

        Returns:
            {
                "totalSupplyUnits": {
                    "Sara City": {value: 1109, unit: "count"},
                    "The Urbana": {value: 150, unit: "count"}
                },
                ...
            }
        """
        comparison = {}

        for project_name in project_names:
            project = self.get_project_by_name(project_name)
            if not project:
                continue

            for attr_name, attr_data in project.items():
                if attributes and attr_name not in attributes:
                    continue

                if attr_name not in comparison:
                    comparison[attr_name] = {}

                comparison[attr_name][project_name] = {
                    'value': attr_data.get('value'),
                    'unit': attr_data.get('unit'),
                    'dimension': attr_data.get('dimension')
                }

        return comparison

    def find_projects_near(self, reference_project_name: str, radius_km: float) -> List[Dict]:
        """
        Find all projects within a specified radius of a reference project using geospatial distance.

        Args:
            reference_project_name: Name of the reference project
            radius_km: Maximum distance from reference project (kilometers)

        Returns:
            List of nearby projects with distance information, sorted by distance (closest first).
            Each project dict includes all original fields plus 'distance_km' field.

        Example:
            >>> store = JSONDataStore()
            >>> nearby = store.find_projects_near("Sara City", 2.0)
            >>> for proj in nearby:
            ...     print(f"{proj['projectName']['value']}: {proj['distance_km']:.2f} km")

        Raises:
            ValueError: If reference project not found or has no coordinates
        """
        from app.utils.geospatial import get_project_coordinates, find_projects_within_radius

        # Get coordinates of reference project
        all_projects = self.data.get('page_2_projects', [])
        coords = get_project_coordinates(reference_project_name, all_projects)

        if coords is None:
            raise ValueError(f"Reference project '{reference_project_name}' not found or has no geographic coordinates")

        ref_lat, ref_lon = coords

        # Find projects within radius
        nearby_projects = find_projects_within_radius(ref_lat, ref_lon, all_projects, radius_km)

        # Transform to nested structure for consistency with other methods
        # Preserve distance_km field which was added by find_projects_within_radius
        transformed_projects = []
        for proj in nearby_projects:
            transformed = self.transform_to_nested_structure(proj)
            transformed['distance_km'] = proj['distance_km']  # Preserve distance field
            transformed_projects.append(transformed)

        return transformed_projects

    def get_stats(self) -> Dict:
        """Get database statistics"""
        return {
            'projects': len(self.data.get('page_2_projects', [])),
            'unit_types': len(self.data.get('page_5_unit_types', [])),
            'quarterly_summaries': len(self.data.get('page_8_quarterly_summary', [])),
            'data_version': self.data.get('metadata', {}).get('architecture_version'),
            'extraction_timestamp': self.data.get('metadata', {}).get('extraction_timestamp')
        }


def demo():
    """Demonstrate JSON data store usage"""
    print("="*70)
    print("JSON DATA STORE - CLEAN NESTED STRUCTURE")
    print("="*70)

    store = JSONDataStore()

    # Demo 1: Get project with clean nested structure
    print("\n" + "="*70)
    print("DEMO 1: Sara City Project (Clean Nested Structure)")
    print("="*70)

    sara_city = store.get_project_by_name("Sara City")

    # Show a few attributes
    for attr in ['projectName', 'totalSupplyUnits', 'currentPricePSF', 'monthlySalesVelocity']:
        if attr in sara_city:
            data = sara_city[attr]
            print(f"\n{attr}:")
            print(f"  {json.dumps(data, indent=2)}")

    # Demo 2: Find all price attributes (C/L²)
    print("\n" + "="*70)
    print("DEMO 2: All Price Attributes (C/L²)")
    print("="*70)

    price_attrs = store.find_attributes_by_dimension("C/L²")
    for attr in price_attrs[:5]:
        print(f"  {attr['nodeName']:20s} | {attr['attribute']:25s} | {attr['value']} {attr['unit']}")

    # Demo 3: Dimensional profile
    print("\n" + "="*70)
    print("DEMO 3: Sara City Dimensional Profile")
    print("="*70)

    profile = store.get_dimensional_profile("Sara City")
    for dimension, attributes in profile.items():
        if attributes:
            print(f"\n{dimension}:")
            for attr in attributes[:3]:
                print(f"  • {attr['attribute']:25s}: {attr['value']} {attr['unit']}")

    # Demo 4: Compare projects
    print("\n" + "="*70)
    print("DEMO 4: Compare Projects on Key Metrics")
    print("="*70)

    comparison = store.compare_projects(
        ["Sara City", "The Urbana", "Gulmohar\nCity"],
        ["totalSupplyUnits", "currentPricePSF", "annualSalesUnits"]
    )

    for attr, projects in comparison.items():
        print(f"\n{attr}:")
        for project_name, data in projects.items():
            print(f"  {project_name:20s}: {data['value']} {data['unit']}")

    # Stats
    print("\n" + "="*70)
    print("DATABASE STATISTICS")
    print("="*70)
    stats = store.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    demo()
