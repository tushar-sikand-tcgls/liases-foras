"""
Data Service V4: Knowledge Graph Data Management
Uses v4_clean_nested_structure.json with proper {value, unit, dimension, relationships} format
"""
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.config import settings


class DataServiceV4:
    """Data service for v4 nested structure with explicit dimensional relationships"""

    def __init__(self):
        self.projects: List[Dict] = []
        self.unit_types: List[Dict] = []
        self.quarterly_summaries: List[Dict] = []
        self.lf_data: Dict = {}
        self._load_data()

    def _load_data(self):
        """Load all data from v4 nested JSON"""
        self._load_v4_nested_data()
        self._load_lf_data()

    def _load_v4_nested_data(self):
        """Load projects from v4_clean_nested_structure.json"""
        data_file = Path(settings.DATA_PATH) / "extracted" / "v4_clean_nested_structure.json"

        if not data_file.exists():
            print(f"Warning: {data_file} not found")
            return

        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.projects = data.get('page_2_projects', [])
        self.unit_types = data.get('page_5_unit_types', [])
        self.quarterly_summaries = data.get('page_8_quarterly_summary', [])

        print(f"✓ Loaded {len(self.projects)} projects from v4 nested format")
        print(f"✓ Format: {{value, unit, dimension, relationships}}")

    def _load_lf_data(self):
        """Load LF mock responses (unchanged)"""
        lf_dir = Path(settings.DATA_PATH) / "lf_mock_responses"

        if not lf_dir.exists():
            print(f"Warning: {lf_dir} not found")
            return

        pillars = ['pillar1_market', 'pillar2_product', 'pillar3_developer',
                   'pillar4_financial', 'pillar5_sales']

        for pillar in pillars:
            file_path = lf_dir / f"{pillar}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    self.lf_data[pillar] = json.load(f)

        print(f"✓ Loaded {len(self.lf_data)} LF pillar datasets")

    # ==================================================================
    # HELPER METHODS FOR NESTED STRUCTURE ACCESS
    # ==================================================================

    @staticmethod
    def get_value(attribute: Dict) -> Any:
        """
        Extract value from nested attribute

        Args:
            attribute: Nested dict with {value, unit, dimension, ...}

        Returns:
            The value field

        Example:
            >>> attr = {"value": 3996, "unit": "INR/sqft", "dimension": "C/L²"}
            >>> get_value(attr)
            3996
        """
        if isinstance(attribute, dict):
            return attribute.get('value')
        return attribute

    @staticmethod
    def get_unit(attribute: Dict) -> str:
        """Extract unit from nested attribute"""
        if isinstance(attribute, dict):
            return attribute.get('unit', '')
        return ''

    @staticmethod
    def get_dimension(attribute: Dict) -> str:
        """Extract dimension from nested attribute"""
        if isinstance(attribute, dict):
            return attribute.get('dimension', 'None')
        return 'None'

    @staticmethod
    def get_relationships(attribute: Dict) -> List[Dict]:
        """
        Extract dimensional relationships from nested attribute

        Returns:
            List of {type, target} relationships
            e.g., [{"type": "NUMERATOR", "target": "C"}, {"type": "DENOMINATOR", "target": "L²"}]
        """
        if isinstance(attribute, dict):
            return attribute.get('relationships', [])
        return []

    # ==================================================================
    # PROJECT QUERIES
    # ==================================================================

    def get_project(self, project_id: str) -> Optional[Dict]:
        """
        Get project by ID

        Returns:
            Project dict with nested attributes, or None
        """
        for project in self.projects:
            pid = self.get_value(project.get('projectId'))
            if str(pid) == str(project_id):
                return project
        return None

    def get_project_by_name(self, name: str) -> Optional[Dict]:
        """
        Get project by name with fuzzy matching.

        Handles:
        - Case-insensitive matching
        - Newlines (\n) treated as spaces
        - Extra whitespace normalization

        Args:
            name: Project name to search for

        Returns:
            Project dict or None if not found
        """
        # Normalize search term: lowercase, replace newlines with spaces, normalize whitespace
        normalized_search = ' '.join(name.lower().replace('\n', ' ').split())

        for project in self.projects:
            project_name = self.get_value(project.get('projectName'))
            if project_name:
                # Normalize project name from data: lowercase, replace newlines with spaces, normalize whitespace
                normalized_project_name = ' '.join(project_name.lower().replace('\n', ' ').split())

                if normalized_project_name == normalized_search:
                    return project

        return None

    def get_all_projects(self) -> List[Dict]:
        """Get all projects (nested format)"""
        return self.projects

    def get_projects_by_location(self, location: str) -> List[Dict]:
        """Get projects by location"""
        return [
            p for p in self.projects
            if self.get_value(p.get('location')) == location
        ]

    # ==================================================================
    # DIMENSIONAL QUERIES
    # ==================================================================

    def find_attributes_by_dimension(self, dimension: str, node_type: str = "project") -> List[Dict]:
        """
        Find all attributes with a specific dimension

        Args:
            dimension: Dimension formula (e.g., "U", "C/L²", "1/T")
            node_type: Type of node to search ("project", "unit_type", "quarterly")

        Returns:
            List of {nodeName, attribute, value, unit, dimension, relationships}
        """
        results = []

        nodes = {
            "project": self.projects,
            "unit_type": self.unit_types,
            "quarterly": self.quarterly_summaries
        }.get(node_type, self.projects)

        for node in nodes:
            node_name = self.get_value(node.get('projectName', node.get('flatType', 'Unknown')))

            for attr_name, attr_data in node.items():
                if isinstance(attr_data, dict) and self.get_dimension(attr_data) == dimension:
                    results.append({
                        'nodeName': node_name,
                        'attribute': attr_name,
                        'value': self.get_value(attr_data),
                        'unit': self.get_unit(attr_data),
                        'dimension': self.get_dimension(attr_data),
                        'relationships': self.get_relationships(attr_data)
                    })

        return results

    def find_attributes_by_relationship(self, rel_type: str, target_dimension: str) -> List[Dict]:
        """
        Find all attributes with a specific relationship type and target

        Args:
            rel_type: Relationship type ("IS", "NUMERATOR", "DENOMINATOR", "INVERSE_OF")
            target_dimension: Target dimension ("U", "L²", "T", "C")

        Returns:
            List of matching attributes

        Example:
            >>> find_attributes_by_relationship("NUMERATOR", "C")
            # Returns all attributes with C as numerator (price attributes)
        """
        results = []

        for project in self.projects:
            project_name = self.get_value(project.get('projectName'))

            for attr_name, attr_data in project.items():
                if not isinstance(attr_data, dict):
                    continue

                relationships = self.get_relationships(attr_data)
                for rel in relationships:
                    if rel.get('type') == rel_type and rel.get('target') == target_dimension:
                        results.append({
                            'nodeName': project_name,
                            'attribute': attr_name,
                            'value': self.get_value(attr_data),
                            'unit': self.get_unit(attr_data),
                            'dimension': self.get_dimension(attr_data),
                            'relationships': relationships
                        })
                        break

        return results

    # ==================================================================
    # LF DATA ACCESS (unchanged)
    # ==================================================================

    def get_lf_market_data(self, location: str) -> Dict:
        """Get LF Pillar 1 market data"""
        return self.lf_data.get('pillar1_market', {}).get('data', {})

    def get_lf_product_data(self, location: str) -> Dict:
        """Get LF Pillar 2 product data"""
        return self.lf_data.get('pillar2_product', {}).get('data', {})

    def get_lf_developer_rating(self, developer_id: str) -> Dict:
        """Get LF Pillar 3 developer ratings"""
        pillar3_data = self.lf_data.get('pillar3_developer', {})
        developers = pillar3_data.get('developers', [])

        developer = next((d for d in developers if d['developer_id'] == developer_id), None)
        return developer if developer else {}

    def get_lf_financial_benchmarks(self) -> Dict:
        """Get LF Pillar 4 financial benchmarks"""
        return self.lf_data.get('pillar4_financial', {}).get('benchmarks', {})

    def get_market_data_for_optimization(self, location: str) -> Dict:
        """
        Get market data formatted for Layer 3 optimization

        Returns pricing, area, and absorption rates by unit type
        """
        pillar2_data = self.get_lf_product_data(location)
        typology = pillar2_data.get('typology_performance', {})

        # Get reference project for pricing
        projects = self.get_projects_by_location(location)
        if not projects:
            raise ValueError(f"No projects found for location: {location}")

        # Use first project as reference - extract values from nested structure
        ref_project = projects[0]

        # Build market data dict (simplified for now)
        market_data = {
            '1BHK': {
                'price': self.get_value(ref_project.get('currentPricePSF', {})) * 500,  # Approximate
                'area': 500,
                'absorption': 0.03
            },
            '2BHK': {
                'price': self.get_value(ref_project.get('currentPricePSF', {})) * 700,
                'area': 700,
                'absorption': 0.04
            },
            '3BHK': {
                'price': self.get_value(ref_project.get('currentPricePSF', {})) * 1000,
                'area': 1000,
                'absorption': 0.025
            }
        }

        return market_data


# Global data service instance
data_service = DataServiceV4()
