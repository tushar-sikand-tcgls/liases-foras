"""
City Reports Ingestion Script

Loads all city reports from docs/city-reports into the vector database.
Run this once or whenever reports are updated.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.services.vector_db_service import VectorDBService


def main():
    print("=" * 60)
    print("City Reports Vector Database Ingestion")
    print("=" * 60)

    # Initialize vector DB service
    vector_db = VectorDBService(persist_directory="data/chroma_db")

    # Ingest all reports
    reports_dir = "docs/city-reports"
    stats = vector_db.ingest_all_reports(reports_dir)

    # Print stats
    print("\n" + "=" * 60)
    print("Ingestion Complete!")
    print("=" * 60)

    total_chunks = sum(stats.values())
    for city, count in stats.items():
        print(f"  {city}: {count} chunks")

    print(f"\n  Total: {total_chunks} chunks indexed")
    print(f"  Collection size: {vector_db.collection.count()} documents")

    # Test some queries
    print("\n" + "=" * 60)
    print("Sample Queries (Testing Semantic Search)")
    print("=" * 60)

    test_queries = [
        ("Mumbai luxury real estate trends", "Mumbai"),
        ("Pune IT corridor price analysis", "Pune"),
        ("Best localities in Mumbai for families", "Mumbai"),
        ("Infrastructure development Pune", "Pune")
    ]

    for query, city in test_queries:
        print(f"\nQuery: '{query}' [City: {city}]")
        results = vector_db.semantic_search(query, city=city, n_results=2)

        for i, result in enumerate(results, 1):
            print(f"  Result {i} (Similarity: {result['similarity_score']:.3f}):")
            snippet = result['text'][:150].replace('\n', ' ')
            print(f"    {snippet}...")
            print(f"    Section: {result['metadata']['section']}")

    print("\n✓ Vector database ready for production use!")


if __name__ == "__main__":
    main()
