"""
Output Ports - What the domain needs from the outside world

These are the "driven" ports - dependencies that the domain requires
from infrastructure (databases, file systems, external APIs).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class ProjectRepositoryPort(ABC):
    """Port for project data persistence/retrieval"""

    @abstractmethod
    def find_by_id(self, project_id: str) -> Optional[Dict]:
        """Find project by ID"""
        pass

    @abstractmethod
    def find_by_name(self, project_name: str) -> Optional[Dict]:
        """Find project by name"""
        pass

    @abstractmethod
    def find_all(self) -> List[Dict]:
        """Get all projects"""
        pass

    @abstractmethod
    def find_by_location(self, location: str) -> List[Dict]:
        """Find projects by location"""
        pass


class FormulaRepositoryPort(ABC):
    """Port for formula/attribute definitions storage"""

    @abstractmethod
    def find_by_name(self, attribute_name: str) -> Optional[Dict]:
        """Find attribute definition by name"""
        pass

    @abstractmethod
    def find_all(self) -> List[Dict]:
        """Get all attribute definitions"""
        pass

    @abstractmethod
    def find_by_layer(self, layer: str) -> List[Dict]:
        """Find attributes by layer (L0, L1, L2, etc.)"""
        pass


class VectorSearchPort(ABC):
    """Port for vector-based semantic search"""

    @abstractmethod
    def search_attributes(
        self,
        query: str,
        top_k: int = 5
    ) -> List[tuple[Dict, float]]:
        """
        Search attributes using vector similarity

        Returns:
            List of (attribute_dict, similarity_score) tuples
        """
        pass

    @abstractmethod
    def search_projects(
        self,
        query: str,
        top_k: int = 5
    ) -> List[tuple[Dict, float]]:
        """Search projects using vector similarity"""
        pass


class ExternalDataSourcePort(ABC):
    """Port for external data sources (Excel, APIs, etc.)"""

    @abstractmethod
    def load_excel_data(self, file_path: str) -> Dict[str, Any]:
        """Load data from Excel file"""
        pass

    @abstractmethod
    def fetch_market_data(self, location: str) -> Optional[Dict]:
        """Fetch market data from external API"""
        pass
