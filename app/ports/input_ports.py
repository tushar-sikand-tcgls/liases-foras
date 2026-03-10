"""
Input Ports - What the domain offers to the outside world

These are the "driving" ports - the use cases that external actors
(HTTP, gRPC, CLI) can invoke to interact with the domain.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from app.models.domain import Project


class QueryAttributePort(ABC):
    """Port for querying attributes (formulas and direct extraction)"""

    @abstractmethod
    def get_attribute(self, attribute_name: str) -> Optional[Dict]:
        """Get attribute definition by name"""
        pass

    @abstractmethod
    def search_attributes(self, query: str) -> List[Dict]:
        """Search attributes by natural language query"""
        pass

    @abstractmethod
    def list_all_attributes(self, layer: Optional[str] = None) -> List[Dict]:
        """List all available attributes, optionally filtered by layer"""
        pass


class CalculateFormulaPort(ABC):
    """Port for executing formula calculations"""

    @abstractmethod
    def calculate(
        self,
        attribute_name: str,
        project_data: Dict[str, Any]
    ) -> Optional[Dict]:
        """
        Calculate an attribute using its formula

        Args:
            attribute_name: Name of attribute to calculate
            project_data: Project data dictionary

        Returns:
            Calculation result with value, unit, formula, etc.
        """
        pass

    @abstractmethod
    def batch_calculate(
        self,
        attribute_names: List[str],
        project_data: Dict[str, Any]
    ) -> Dict[str, Optional[Dict]]:
        """Calculate multiple attributes at once"""
        pass


class ProjectQueryPort(ABC):
    """Port for querying project data"""

    @abstractmethod
    def get_project_by_id(self, project_id: str) -> Optional[Dict]:
        """Get project by ID"""
        pass

    @abstractmethod
    def get_project_by_name(self, project_name: str) -> Optional[Dict]:
        """Get project by name"""
        pass

    @abstractmethod
    def search_projects(
        self,
        location: Optional[str] = None,
        developer: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Search projects with filters"""
        pass

    @abstractmethod
    def list_all_projects(self) -> List[Dict]:
        """List all projects"""
        pass


class StatisticalAnalysisPort(ABC):
    """Port for statistical operations (average, mean, aggregation)"""

    @abstractmethod
    def calculate_average(
        self,
        attribute_name: str,
        projects: List[Dict]
    ) -> float:
        """Calculate average of an attribute across projects"""
        pass

    @abstractmethod
    def calculate_aggregation(
        self,
        attribute_name: str,
        aggregation_type: str,  # 'sum', 'mean', 'median', 'max', 'min'
        projects: List[Dict]
    ) -> float:
        """Calculate aggregation of an attribute"""
        pass

    @abstractmethod
    def calculate_percentile(
        self,
        attribute_name: str,
        percentile: float,  # 0-100
        projects: List[Dict]
    ) -> float:
        """Calculate percentile value"""
        pass


class DimensionValidationPort(ABC):
    """Port for validating dimensional consistency"""

    @abstractmethod
    def validate_dimension(
        self,
        query: str,
        response_value: Any,
        response_unit: str,
        response_dimension: Optional[str]
    ) -> tuple[bool, str]:
        """
        Validate that response dimension matches query expectation

        Returns:
            (is_valid, error_message)
        """
        pass

    @abstractmethod
    def extract_expected_dimension(self, query: str) -> Optional[str]:
        """Extract expected dimension from query text"""
        pass
