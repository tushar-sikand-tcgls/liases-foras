"""
Knowledge Graph Port - Interface for Data Retrieval

This port defines the contract for Knowledge Graph operations.
KG is the SINGLE SOURCE OF TRUTH for all numeric/factual data.

Implementations: Neo4j, PostgreSQL with graph extensions, etc.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any


class KnowledgeGraphPort(ABC):
    """Port for knowledge graph data retrieval and aggregation"""

    @abstractmethod
    def fetch_attribute(self, project: str, attribute: str) -> Any:
        """
        Fetch specific attribute value for a project

        Args:
            project: Project name (canonical)
            attribute: Attribute name (canonical)

        Returns:
            Attribute value with proper type (int, float, str, etc.)

        Example:
            fetch_attribute("Sara City", "Total Units") ' 3018
        """
        pass

    @abstractmethod
    def fetch_multiple_attributes(self, project: str, attributes: List[str]) -> Dict[str, Any]:
        """
        Fetch multiple attributes for a single project

        Args:
            project: Project name (canonical)
            attributes: List of attribute names

        Returns:
            Dict mapping attribute names to values

        Example:
            fetch_multiple_attributes("Sara City", ["Total Units", "Sold %"])
            ' {"Total Units": 3018, "Sold %": 89}
        """
        pass

    @abstractmethod
    def aggregate(
        self,
        attribute: str,
        aggregation: str,  # "sum", "avg", "max", "min", "count"
        filters: Optional[Dict] = None
    ) -> float:
        """
        Aggregate attribute across multiple projects

        Args:
            attribute: Attribute name to aggregate
            aggregation: Aggregation function (sum, avg, max, min, count)
            filters: Optional filters (e.g., {"location": "Chakan"})

        Returns:
            Aggregated numeric value

        Example:
            aggregate("Total Units", "sum", filters={"location": "Chakan"})
            ' 15000.0
        """
        pass

    @abstractmethod
    def compare(
        self,
        projects: List[str],
        attribute: str
    ) -> List[Dict[str, Any]]:
        """
        Compare attribute values across multiple projects

        Args:
            projects: List of project names
            attribute: Attribute to compare

        Returns:
            List of dicts with project name and attribute value

        Example:
            compare(["Sara City", "The Urbana"], "Sold %")
            ' [
                {"project": "Sara City", "Sold %": 89},
                {"project": "The Urbana", "Sold %": 96}
              ]
        """
        pass

    @abstractmethod
    def resolve_project(self, project_name: str) -> Optional[str]:
        """
        Resolve fuzzy project name to canonical name using GraphRAG/fuzzy matching

        Args:
            project_name: User-provided project name (may have typos, case issues)

        Returns:
            Canonical project name or None if not found

        Example:
            resolve_project("sara city") ' "Sara City"
            resolve_project("Pradnyesh Shrinivas") ' "Pradnyesh\nShriniwas"
        """
        pass

    @abstractmethod
    def resolve_developer(self, developer_name: str) -> Optional[str]:
        """
        Resolve fuzzy developer name to canonical name

        Args:
            developer_name: User-provided developer name

        Returns:
            Canonical developer name or None if not found
        """
        pass

    @abstractmethod
    def resolve_location(self, location_name: str) -> Optional[str]:
        """
        Resolve fuzzy location name to canonical name

        Args:
            location_name: User-provided location name

        Returns:
            Canonical location name or None if not found
        """
        pass

    @abstractmethod
    def find_projects_by_filter(self, filters: Dict) -> List[str]:
        """
        Find projects matching filters

        Args:
            filters: Dict of filters (e.g., {"location": "Chakan", "developer": "Sara Builders"})

        Returns:
            List of matching project names

        Example:
            find_projects_by_filter({"location": "Chakan"})
            ' ["Sara City", "The Urbana", "Sara Nilaay"]
        """
        pass

    @abstractmethod
    def fetch_cash_flow_data(self, project: str) -> Dict[str, Any]:
        """
        Fetch cash flow proxies for financial calculations

        Args:
            project: Project name

        Returns:
            Dict with cash flow-related data:
            - annual_sales (Rs.Cr.)
            - total_investment (Rs.Cr.)
            - project_duration (months)
            - monthly_revenue_avg (Rs.Cr.)
            etc.

        Example:
            fetch_cash_flow_data("Sara City")
            ' {
                "annual_sales": 45.2,
                "total_investment": 350.0,
                "project_duration": 60,
                "monthly_revenue_avg": 3.77
              }
        """
        pass

    @abstractmethod
    def get_all_projects(self) -> List[str]:
        """
        Get list of all project names in the KG

        Returns:
            List of all project names

        Example:
            get_all_projects()
            ' ["Sara City", "Pradnyesh\nShriniwas", "The Urbana", ...]
        """
        pass

    @abstractmethod
    def get_project_metadata(self, project: str) -> Dict[str, Any]:
        """
        Get comprehensive metadata for a project

        Args:
            project: Project name

        Returns:
            Dict with project metadata:
            - projectId
            - projectName
            - developerName
            - location
            - launchDate
            etc.
        """
        pass

    @abstractmethod
    def find_projects_near(self, reference_project_name: str, radius_km: float) -> List[Dict]:
        """
        Find all projects within a specified radius of a reference project

        Args:
            reference_project_name: Name of the reference project
            radius_km: Maximum distance from reference project (kilometers)

        Returns:
            List of nearby projects with distance information, sorted by distance (closest first).
            Each project dict includes all original fields plus 'distance_km' field.

        Raises:
            ValueError: If reference project not found or has no coordinates

        Example:
            >>> kg.find_projects_near("Sara City", 2.0)
            [
                {'projectName': {...}, 'distance_km': 0.794, ...},
                {'projectName': {...}, 'distance_km': 1.523, ...}
            ]
        """
        pass

    @abstractmethod
    def get_value(self, field: Any) -> Any:
        """
        Extract value from nested structure {value, unit, dimension}

        Args:
            field: Field that may be a nested dict or plain value

        Returns:
            Extracted value or original field if not nested

        Example:
            >>> kg.get_value({'value': 'Sara City', 'unit': 'Text'})
            'Sara City'
            >>> kg.get_value('Plain String')
            'Plain String'
        """
        pass
