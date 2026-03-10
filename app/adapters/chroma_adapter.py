"""
ChromaDB Adapter - Vector DB Implementation for Attribute Schema Understanding

This adapter implements the VectorDBPort using ChromaDB for semantic search.
It stores metadata about attributes from the enriched Excel file.

Key Features:
- Loads 36 attributes from LF-Layers_FULLY_ENRICHED_ALL_36.xlsx
- Creates embeddings using SentenceTransformers
- Provides semantic search for attribute resolution
- Returns rich metadata for LLM context
"""

import chromadb
from sentence_transformers import SentenceTransformer
import pandas as pd
from typing import List, Dict, Optional
import os

from app.ports.vector_db_port import VectorDBPort


class ChromaAdapter(VectorDBPort):
    """ChromaDB implementation for attribute schema understanding"""

    def __init__(self, persist_directory: str = "./data/chroma_attributes_db"):
        """
        Initialize ChromaDB adapter

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        # Create persist directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)

        # Initialize ChromaDB client with persistence (new API)
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Collection name
        self.collection_name = "lf_attributes"

        # Try to get existing collection or create new
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f" Loaded existing ChromaDB collection: {self.collection_name}")
        except:
            # Create new collection with L2 distance for embeddings
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "LF attribute metadata for semantic search"}
            )
            print(f" Created new ChromaDB collection: {self.collection_name}")

        # Initialize embedding model (lightweight, fast, good for semantic search)
        # all-MiniLM-L6-v2: 384 dimensions, 80MB model, excellent for semantic similarity
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print(" Loaded SentenceTransformer embedding model: all-MiniLM-L6-v2")

        # Cache for loaded attributes
        self._attributes_cache = {}

    def search_attributes(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for top-k relevant attributes using semantic similarity

        Args:
            query: User's natural language query
            k: Number of top results to return

        Returns:
            List of attribute metadata dicts
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )

        # Extract metadata from results
        if not results or not results.get('metadatas') or len(results['metadatas']) == 0:
            return []

        # results['metadatas'][0] contains list of metadata dicts
        return results['metadatas'][0]

    def get_attribute_by_name(self, attribute_name: str) -> Optional[Dict]:
        """
        Get full metadata for a specific attribute by canonical name

        Args:
            attribute_name: Canonical attribute name (e.g., "Total Units")

        Returns:
            Attribute metadata dict or None if not found
        """
        # Check cache first
        if attribute_name in self._attributes_cache:
            return self._attributes_cache[attribute_name]

        # Query ChromaDB by ID (we use Target Attribute as ID)
        try:
            results = self.collection.get(
                ids=[attribute_name]
            )

            if results and results.get('metadatas') and len(results['metadatas']) > 0:
                metadata = results['metadatas'][0]
                self._attributes_cache[attribute_name] = metadata
                return metadata
        except:
            pass

        return None

    def get_all_attributes_by_layer(self, layer: str) -> List[Dict]:
        """
        Get all attributes in a specific layer

        Args:
            layer: Layer identifier (L0, L1, L2, or L3)

        Returns:
            List of attribute metadata dicts for that layer
        """
        # Query all documents and filter by layer
        all_docs = self.collection.get()

        if not all_docs or not all_docs.get('metadatas'):
            return []

        # Filter by layer
        return [
            metadata for metadata in all_docs['metadatas']
            if metadata.get('Layer') == layer
        ]

    def get_attributes_by_dimension(self, dimension: str) -> List[Dict]:
        """
        Get all attributes with a specific dimension

        Args:
            dimension: Dimension identifier (e.g., "CF/U", "L'", "T", etc.)

        Returns:
            List of attribute metadata dicts with that dimension
        """
        # Query all documents and filter by dimension
        all_docs = self.collection.get()

        if not all_docs or not all_docs.get('metadatas'):
            return []

        # Filter by dimension (normalize comparison)
        dimension_normalized = dimension.strip().lower()
        return [
            metadata for metadata in all_docs['metadatas']
            if metadata.get('Dimension', '').strip().lower() == dimension_normalized
        ]

    def load_attributes_from_excel(self, excel_path: str) -> int:
        """
        Load attribute metadata from enriched Excel file and create embeddings

        Args:
            excel_path: Path to LF-Layers_FULLY_ENRICHED_ALL_36.xlsx

        Returns:
            Number of attributes loaded
        """
        print(f"\n{'='*80}")
        print(f"LOADING ATTRIBUTES FROM EXCEL: {excel_path}")
        print(f"{'='*80}")

        # Read Excel file
        df = pd.read_excel(excel_path)
        print(f" Loaded {len(df)} rows from Excel")

        # Clear existing collection (reload fresh)
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "LF attribute metadata for semantic search"}
            )
            print(f" Cleared and recreated collection: {self.collection_name}")
        except:
            pass

        # Process each attribute
        ids = []
        embeddings = []
        metadatas = []
        documents = []

        for idx, row in df.iterrows():
            # Create rich embedding text from multiple fields
            embedding_text = f"""
Attribute: {row['Target Attribute']}
Description: {row['Description']}
Sample Questions: {row['Sample Prompt']}
Variations: {row['Variation in Prompt']}
Formula: {row['Formula/Derivation']}
Assumptions: {row['Assumption in Prompt']}
Unit: {row['Unit']}
Dimension: {row['Dimension']}
Layer: {row['Layer']}
            """.strip()

            # Generate embedding
            embedding = self.embedding_model.encode(embedding_text).tolist()

            # Prepare metadata (convert all to strings for ChromaDB)
            metadata = {
                'Target Attribute': str(row['Target Attribute']),
                'Unit': str(row['Unit']),
                'Dimension': str(row['Dimension']),
                'Description': str(row['Description']),
                'Sample Prompt': str(row['Sample Prompt']),
                'Variation in Prompt': str(row['Variation in Prompt']),
                'Assumption in Prompt': str(row['Assumption in Prompt']),
                'Formula/Derivation': str(row['Formula/Derivation']),
                'Sample Values': str(row['Sample Values']),
                'Expected Answer': str(row['Expected Answer']),
                'Layer': str(row['Layer'])
            }

            # Use Target Attribute as ID
            attribute_id = str(row['Target Attribute'])

            ids.append(attribute_id)
            embeddings.append(embedding)
            metadatas.append(metadata)
            documents.append(embedding_text)

            # Update cache
            self._attributes_cache[attribute_id] = metadata

        # Add to ChromaDB in batch
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )

        print(f" Loaded {len(ids)} attributes into ChromaDB")
        print(f" Embeddings dimension: {len(embeddings[0])}")
        print(f" Cache populated with {len(self._attributes_cache)} attributes")

        # Display sample attributes by layer
        for layer in ['L0', 'L1', 'L2', 'L3']:
            layer_attrs = [m for m in metadatas if m['Layer'] == layer]
            if layer_attrs:
                print(f"\n{layer} Attributes ({len(layer_attrs)}):")
                for attr in layer_attrs[:3]:  # Show first 3 per layer
                    print(f"  - {attr['Target Attribute']} ({attr['Dimension']}, {attr['Unit']})")

        print(f"\n{'='*80}")
        print(f"VECTOR DB READY FOR SEMANTIC SEARCH")
        print(f"{'='*80}\n")

        return len(ids)


# Global singleton instance
_chroma_adapter = None


def get_chroma_adapter(
    persist_directory: str = "./data/chroma_attributes_db",
    auto_load_excel: bool = True,
    excel_path: str = "change-request/enriched-layers/LF-Layers_FULLY_ENRICHED_ALL_36.xlsx"
) -> ChromaAdapter:
    """
    Get or create global ChromaDB adapter instance

    Args:
        persist_directory: Directory to persist ChromaDB data
        auto_load_excel: Whether to automatically load Excel on first initialization
        excel_path: Path to enriched Excel file

    Returns:
        ChromaAdapter singleton instance
    """
    global _chroma_adapter

    if _chroma_adapter is None:
        _chroma_adapter = ChromaAdapter(persist_directory=persist_directory)

        # Auto-load Excel if requested and collection is empty
        if auto_load_excel:
            try:
                count = _chroma_adapter.collection.count()
                if count == 0:
                    print(f"9  ChromaDB collection is empty. Auto-loading Excel...")
                    _chroma_adapter.load_attributes_from_excel(excel_path)
                else:
                    print(f"9  ChromaDB collection already has {count} attributes. Skipping Excel load.")
            except Exception as e:
                print(f"'  Error checking/loading Excel: {e}")

    return _chroma_adapter
