#!/usr/bin/env python3
"""
Manual Script to Index City Reports into ChromaDB
Run this script once or when new documents are added

Usage:
    python scripts/index_city_reports.py
    python scripts/index_city_reports.py --force  # Re-index all documents
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.document_vector_service import DocumentVectorService


def main():
    parser = argparse.ArgumentParser(description='Index city reports into ChromaDB')
    parser.add_argument('--force', action='store_true', help='Force re-index all documents')
    parser.add_argument('--reports-dir', default='docs/city-reports', help='Path to city reports directory')
    args = parser.parse_args()

    print("=" * 60)
    print("City Reports Vectorization Script")
    print("=" * 60)

    # Initialize the service
    service = DocumentVectorService()

    # Check if already indexed
    current_count = service.collection.count()
    if current_count > 0 and not args.force:
        print(f"\n⚠ ChromaDB already contains {current_count} document chunks.")
        print("Use --force to re-index all documents.")
        response = input("\nDo you want to continue and add more documents? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return

    # If force re-index, clear existing data
    if args.force and current_count > 0:
        print(f"\n🗑 Clearing existing {current_count} document chunks...")
        # Delete the collection and recreate
        service.client.delete_collection("city_reports")
        service.collection = service.client.create_collection(
            name="city_reports",
            metadata={"description": "City and region intelligence reports"}
        )
        print("✓ Collection cleared")

    # Index all documents
    print(f"\n📄 Indexing documents from: {args.reports_dir}")
    service.index_all_documents(base_path=args.reports_dir)

    # Summary
    print("\n" + "=" * 60)
    print("✅ Indexing Complete!")
    print("=" * 60)
    print(f"Total document chunks in ChromaDB: {service.collection.count()}")
    print("\nYou can now query city insights via the API or frontend.")
    print("=" * 60)


if __name__ == "__main__":
    main()
