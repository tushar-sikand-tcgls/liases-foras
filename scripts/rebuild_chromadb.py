"""
Rebuild ChromaDB Attribute Schema

This script forces ChromaDB to reload the attribute schema from the Excel file.
It clears the existing collection and rebuilds it with the latest attribute definitions.

Run this after:
- Updating the Excel schema file
- Adding new derived metrics
- Modifying attribute definitions
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.adapters.chroma_adapter import ChromaAdapter


def rebuild_chromadb():
    """
    Force rebuild ChromaDB attribute collection
    """
    print("=" * 80)
    print("CHROMADB REBUILD SCRIPT")
    print("=" * 80)

    # Path to Excel schema
    excel_path = "change-request/managed-rag/LF-Layers_FULLY_ENRICHED_ALL_36.xlsx"

    if not os.path.exists(excel_path):
        print(f"❌ ERROR: Excel file not found at {excel_path}")
        return False

    print(f"\n✅ Found Excel schema: {excel_path}\n")

    # Initialize ChromaAdapter
    print("📦 Initializing ChromaDB adapter...")
    adapter = ChromaAdapter()

    # Force reload from Excel
    print("\n🔄 Force reloading attributes from Excel...\n")
    count = adapter.load_attributes_from_excel(excel_path)

    print(f"\n{'=' * 80}")
    print(f"✅ REBUILD COMPLETE")
    print(f"{'=' * 80}")
    print(f"   Loaded {count} attributes into ChromaDB")
    print(f"   Collection: {adapter.collection_name}")

    # Verify "Sellout Efficiency" is loaded
    print(f"\n🔍 Verifying 'Sellout Efficiency' attribute...")
    sellout_efficiency = adapter.get_attribute_by_name("Sellout Efficiency")

    if sellout_efficiency:
        print(f"   ✅ Found: Sellout Efficiency")
        print(f"      Unit: {sellout_efficiency.get('Unit')}")
        print(f"      Layer: {sellout_efficiency.get('Layer')}")
        print(f"      Formula: {sellout_efficiency.get('Formula/Derivation')}")
        synonyms = sellout_efficiency.get('Variation in Prompt', '')
        if synonyms:
            print(f"      Synonyms: {synonyms}")
    else:
        print(f"   ❌ NOT FOUND: Sellout Efficiency")
        print(f"      This is a problem - check Excel file")

    print(f"\n{'=' * 80}")
    print("Next steps:")
    print("1. Restart any running backend services")
    print("2. Test query: 'What is the sellout efficiency of Sara City?'")
    print("3. Verify it returns 5.7% (not 47.52%)")
    print(f"{'=' * 80}\n")

    return True


if __name__ == "__main__":
    success = rebuild_chromadb()
    sys.exit(0 if success else 1)
