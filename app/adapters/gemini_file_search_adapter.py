"""
Gemini File Search Adapter - Vector DB Port Implementation

This adapter uses Gemini's Fully Managed RAG (File Search) for attribute resolution.
No local embeddings or vector DB - Gemini handles vector search on its side.

Files uploaded to File Search Store:
- LF-Layers_FULLY_ENRICHED_ALL_36.xlsx (attribute metadata with variations)
- Glossary.pdf (attribute definitions)
- Lf Capability Pitch Document.docx (domain knowledge)
"""

import os
from typing import List, Dict, Optional
from app.ports.vector_db_port import VectorDBPort

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None


class GeminiFileSearchAdapter(VectorDBPort):
    """
    Vector DB adapter using Gemini's File Search (Fully Managed RAG)

    Key Principle: Let Gemini do the vector search on its side using uploaded files.
    No local embeddings, no ChromaDB - pure Gemini File Search.
    """

    def __init__(self, api_key: Optional[str] = None, file_search_store_name: Optional[str] = None):
        """
        Initialize Gemini File Search adapter

        Args:
            api_key: Google API key (from env if not provided)
            file_search_store_name: File Search Store ID (from env if not provided)
        """
        # Get API key
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key required. Set GOOGLE_API_KEY environment variable.")

        if not GENAI_AVAILABLE:
            raise ImportError("google-genai package required. Install: pip install google-genai")

        # Initialize client
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.0-flash-exp"  # Fast model with File Search support

        # Get File Search store
        self.file_search_store_name = file_search_store_name or os.getenv("FILE_SEARCH_STORE_NAME")
        if not self.file_search_store_name:
            raise ValueError("FILE_SEARCH_STORE_NAME required. Set in environment variables.")

        print(f"✅ Gemini File Search Adapter initialized (model: {self.model})")
        print(f"   File Search Store: {self.file_search_store_name}")

    def search_attributes(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for top-k relevant attributes using Gemini File Search

        Args:
            query: User's natural language query (e.g., "efficiency ratio")
            k: Number of top results to return

        Returns:
            List of attribute metadata dicts containing:
            - Target Attribute (canonical name)
            - Variation in Prompt (synonyms)
            - Description, Formula/Derivation, Unit, Dimension, Layer
        """
        # Build prompt for Gemini to search attributes
        search_prompt = f"""You are an attribute resolution expert for real estate analytics.

USER QUERY: "{query}"

YOUR TASK:
Search the LF-Layers_FULLY_ENRICHED_ALL_36.xlsx file to find the top {k} attributes that match the user's query.

CRITICAL MATCHING RULES:
1. Check the "Variation in Prompt" column - these are synonyms/variations that users might say
2. If the user query matches ANY variation (case-insensitive), return that attribute
3. Also check "Target Attribute" and "Description" columns for semantic matches
4. Rank by relevance (exact variation match > partial variation match > semantic description match)

RETURN FORMAT (JSON array):
[
  {{
    "Target Attribute": "canonical attribute name",
    "Variation in Prompt": "synonym1 | synonym2 | synonym3",
    "Description": "attribute description",
    "Formula/Derivation": "calculation formula",
    "Unit": "unit of measurement",
    "Dimension": "dimensional unit",
    "Layer": "L0/L1/L2/L3"
  }},
  ...
]

EXAMPLE:
User query: "efficiency ratio"
→ Should match "Sellout Efficiency" because "Variation in Prompt" contains "efficiency ratio | sales efficiency | conversion rate"

Return ONLY the JSON array, no additional text."""

        try:
            # Use Gemini's Interactions API with File Search
            # This is the correct approach for File Search integration
            # File Search tool configured to search uploaded documents
            interaction = self.client.interactions.create(
                model=self.model,
                input=search_prompt,
                file_search_store=self.file_search_store_name,
                response_mime_type="application/json"
            )

            # Extract text response from interaction
            import json
            result_text = None

            for output in interaction.outputs:
                if hasattr(output, 'text') and output.text:
                    result_text = output.text.strip()
                    break

            if not result_text:
                print(f"⚠️  No text output from Gemini File Search")
                return []

            # Handle code block wrapping (if Gemini returns ```json ... ```)
            if result_text.startswith("```"):
                # Extract JSON from code block
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1])  # Remove first and last lines

            attributes = json.loads(result_text)

            # Ensure it's a list
            if isinstance(attributes, dict):
                attributes = [attributes]

            # Limit to k results
            return attributes[:k]

        except Exception as e:
            print(f"❌ Error in Gemini File Search: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_attribute_by_name(self, attribute_name: str) -> Optional[Dict]:
        """
        Get full metadata for a specific attribute by canonical name

        Args:
            attribute_name: Canonical attribute name (e.g., "Total Units")

        Returns:
            Attribute metadata dict or None if not found
        """
        # Search with exact attribute name
        results = self.search_attributes(query=attribute_name, k=1)

        if results and results[0].get("Target Attribute", "").lower() == attribute_name.lower():
            return results[0]

        return None

    def get_all_attributes_by_layer(self, layer: str) -> List[Dict]:
        """
        Get all attributes in a specific layer

        Args:
            layer: Layer identifier (L0, L1, L2, or L3)

        Returns:
            List of attribute metadata dicts for that layer
        """
        # Build prompt to get all attributes in layer
        search_prompt = f"""Search the LF-Layers_FULLY_ENRICHED_ALL_36.xlsx file and return ALL attributes where Layer = "{layer}".

Return as JSON array with fields: Target Attribute, Variation in Prompt, Description, Formula/Derivation, Unit, Dimension, Layer.

Return ONLY the JSON array, no additional text."""

        try:
            from google.genai.types import Tool

            file_search_tool = Tool(
                file_search_store=self.file_search_store_name
            )

            interaction = self.client.interactions.create(
                model=self.model,
                input=search_prompt,
                tools=[file_search_tool],
                response_mime_type="application/json"
            )

            import json
            result_text = None

            for output in interaction.outputs:
                if hasattr(output, 'text') and output.text:
                    result_text = output.text.strip()
                    break

            if not result_text:
                print(f"⚠️  No text output from Gemini File Search")
                return []

            # Handle code block wrapping
            if result_text.startswith("```"):
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1])

            attributes = json.loads(result_text)

            if isinstance(attributes, dict):
                attributes = [attributes]

            return attributes

        except Exception as e:
            print(f"❌ Error getting attributes by layer: {e}")
            return []

    def get_attributes_by_dimension(self, dimension: str) -> List[Dict]:
        """
        Get all attributes with a specific dimension

        Args:
            dimension: Dimension identifier (e.g., "CF/U", "L^2", "T", etc.)

        Returns:
            List of attribute metadata dicts with that dimension
        """
        # Build prompt to get all attributes with dimension
        search_prompt = f"""Search the LF-Layers_FULLY_ENRICHED_ALL_36.xlsx file and return ALL attributes where Dimension = "{dimension}".

Return as JSON array with fields: Target Attribute, Variation in Prompt, Description, Formula/Derivation, Unit, Dimension, Layer.

Return ONLY the JSON array, no additional text."""

        try:
            from google.genai.types import Tool

            file_search_tool = Tool(
                file_search_store=self.file_search_store_name
            )

            interaction = self.client.interactions.create(
                model=self.model,
                input=search_prompt,
                tools=[file_search_tool],
                response_mime_type="application/json"
            )

            import json
            result_text = None

            for output in interaction.outputs:
                if hasattr(output, 'text') and output.text:
                    result_text = output.text.strip()
                    break

            if not result_text:
                print(f"⚠️  No text output from Gemini File Search")
                return []

            # Handle code block wrapping
            if result_text.startswith("```"):
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1])

            attributes = json.loads(result_text)

            if isinstance(attributes, dict):
                attributes = [attributes]

            return attributes

        except Exception as e:
            print(f"❌ Error getting attributes by dimension: {e}")
            return []

    def load_attributes_from_excel(self, excel_path: str) -> int:
        """
        Load attribute metadata from enriched Excel file

        NOTE: For Gemini File Search, the file should already be uploaded to the File Search Store.
        This method is a no-op since Gemini manages the files on its side.

        Args:
            excel_path: Path to LF-Layers_FULLY_ENRICHED_ALL_36.xlsx

        Returns:
            Number of attributes (always returns 0 since loading happens on Gemini's side)
        """
        print(f"⚠️  Note: Gemini File Search uses files uploaded to File Search Store.")
        print(f"   Local file loading is not required - Gemini manages vector search on its side.")
        print(f"   To upload new files, use the Gemini File API or Google AI Studio.")
        return 0


# Singleton factory function
_gemini_file_search_adapter = None

def get_gemini_file_search_adapter() -> GeminiFileSearchAdapter:
    """Get singleton Gemini File Search adapter instance"""
    global _gemini_file_search_adapter

    if _gemini_file_search_adapter is None:
        _gemini_file_search_adapter = GeminiFileSearchAdapter()

    return _gemini_file_search_adapter
