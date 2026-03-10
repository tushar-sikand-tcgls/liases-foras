"""
Vector DB Port - Interface for Attribute Schema Understanding

This port defines the contract for Vector DB operations.
Vector DB stores metadata about attributes (NOT actual data values).

Implementations: ChromaDB, Pinecone, Weaviate, etc.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class VectorDBPort(ABC):
    """Port for attribute schema understanding via vector embeddings"""

    @abstractmethod
    def search_attributes(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for top-k relevant attributes using semantic similarity

        Args:
            query: User's natural language query
            k: Number of top results to return

        Returns:
            List of attribute metadata dicts containing:
            - Target Attribute (canonical name)
            - Description (detailed explanation)
            - Formula/Derivation (calculation method)
            - Unit, Dimension
            - Sample Prompt, Variation in Prompt
            - Assumption in Prompt
            - Layer (L0, L1, L2, L3)
        """
        pass

    @abstractmethod
    def get_attribute_by_name(self, attribute_name: str) -> Optional[Dict]:
        """
        Get full metadata for a specific attribute by canonical name

        Args:
            attribute_name: Canonical attribute name (e.g., "Total Units")

        Returns:
            Attribute metadata dict or None if not found
        """
        pass

    @abstractmethod
    def get_all_attributes_by_layer(self, layer: str) -> List[Dict]:
        """
        Get all attributes in a specific layer

        Args:
            layer: Layer identifier (L0, L1, L2, or L3)

        Returns:
            List of attribute metadata dicts for that layer
        """
        pass

    @abstractmethod
    def get_attributes_by_dimension(self, dimension: str) -> List[Dict]:
        """
        Get all attributes with a specific dimension

        Args:
            dimension: Dimension identifier (e.g., "CF/U", "L^2", "T", etc.)

        Returns:
            List of attribute metadata dicts with that dimension
        """
        pass

    @abstractmethod
    def load_attributes_from_excel(self, excel_path: str) -> int:
        """
        Load attribute metadata from enriched Excel file and create embeddings

        Args:
            excel_path: Path to LF-Layers_FULLY_ENRICHED_ALL_36.xlsx

        Returns:
            Number of attributes loaded
        """
        pass
