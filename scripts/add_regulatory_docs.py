"""
Add Regulatory Documents to Existing File Search Store

Uploads:
1. National Building Code of India
2. UDCPR (Unified Development Control and Promotion Regulations)

To the existing File Search store for supplementing answers with regulatory context.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Import google-genai SDK
try:
    from google import genai
except ImportError:
    print("❌ ERROR: google-genai package not installed")
    print("\nInstall with:")
    print("  pip install google-genai")
    sys.exit(1)


def add_regulatory_documents():
    """Add regulatory PDFs to existing File Search store"""

    # Get configuration
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    file_search_store_name = os.getenv("FILE_SEARCH_STORE_NAME")

    if not api_key:
        print("❌ Error: GEMINI_API_KEY or GOOGLE_API_KEY not found in .env")
        sys.exit(1)

    if not file_search_store_name:
        print("❌ Error: FILE_SEARCH_STORE_NAME not found in .env")
        sys.exit(1)

    # Initialize client
    client = genai.Client(api_key=api_key)

    print("=" * 80)
    print("📚 ADDING REGULATORY DOCUMENTS TO FILE SEARCH")
    print("=" * 80)
    print(f"\n🎯 Target File Search Store: {file_search_store_name}\n")

    # Define regulatory documents
    base_dir = Path(__file__).parent.parent
    docs_to_upload = [
        {
            "path": base_dir / "change-request" / "managed-rag" / "national building code of india.pdf",
            "display_name": "National Building Code of India"
        },
        {
            "path": base_dir / "change-request" / "managed-rag" / "UDCPR_compressed_2.pdf",
            "display_name": "UDCPR - Unified Development Control and Promotion Regulations"
        }
    ]

    uploaded_count = 0
    failed_count = 0

    # Upload each document
    for i, doc in enumerate(docs_to_upload, 1):
        print(f"\n📄 [{i}/{len(docs_to_upload)}] {doc['display_name']}")
        print(f"   Path: {doc['path']}")

        # Check if file exists
        if not doc['path'].exists():
            print(f"   ❌ File not found!")
            failed_count += 1
            continue

        file_size_mb = doc['path'].stat().st_size / (1024 * 1024)
        print(f"   Size: {file_size_mb:.2f} MB")

        try:
            # Upload to File Search store
            print(f"   ⏳ Uploading to File Search store...")

            upload_op = client.file_search_stores.upload_to_file_search_store(
                file=str(doc['path']),
                file_search_store_name=file_search_store_name
            )

            print(f"   ✅ Upload successful!")
            if hasattr(upload_op, 'name'):
                print(f"   📌 Operation ID: {upload_op.name}")

            uploaded_count += 1

        except Exception as e:
            print(f"   ❌ Upload failed: {str(e)}")
            failed_count += 1

    # Summary
    print(f"\n{'=' * 80}")
    print(f"📊 UPLOAD SUMMARY")
    print(f"{'=' * 80}")
    print(f"✅ Uploaded: {uploaded_count}/{len(docs_to_upload)}")
    if failed_count > 0:
        print(f"❌ Failed: {failed_count}/{len(docs_to_upload)}")

    if uploaded_count > 0:
        print(f"\n{'=' * 80}")
        print("🎉 REGULATORY DOCUMENTS SUCCESSFULLY ADDED!")
        print(f"{'=' * 80}\n")

        print("📋 Documents Now in File Search:")
        print("   1. LF Layers (Fully Enriched - All 36 Attributes) [EXISTING]")
        print("   2. LF Capability Pitch Document [EXISTING]")
        print("   3. Real Estate Glossary [EXISTING]")
        print("   4. National Building Code of India [NEW] ✨")
        print("   5. UDCPR - Development Control Regulations [NEW] ✨")

        print(f"\n{'=' * 80}")
        print("💡 WHAT THIS ENABLES:")
        print(f"{'=' * 80}")
        print("🏗️  Regulatory Context: Answers now include building code compliance")
        print("📐 Development Rules: FSI, setbacks, parking requirements from UDCPR")
        print("🔥 Safety Standards: Fire safety, structural requirements from NBC")
        print("🏙️  Urban Planning: Development control rules for Maharashtra")
        print("✅ Compliance Checks: Verify if projects meet regulatory standards")

        print(f"\n{'=' * 80}")
        print("🧪 TEST QUERIES:")
        print(f"{'=' * 80}")
        print("Try asking:")
        print("   • 'What are the FSI regulations as per UDCPR?'")
        print("   • 'What does the National Building Code say about fire safety?'")
        print("   • 'What are parking requirements for residential buildings?'")
        print("   • 'What is the minimum setback for a 15-story building?'")
        print("   • 'Does this project comply with NBC fire safety norms?'")

        print(f"\n{'=' * 80}")
        print("⚡ NEXT STEPS:")
        print(f"{'=' * 80}")
        print("1. No backend restart needed - File Search updates automatically!")
        print("2. Test regulatory queries immediately")
        print("3. Answers will now be enriched with NBC & UDCPR context")
        print(f"{'=' * 80}\n")

    else:
        print("\n❌ No documents were uploaded successfully")
        sys.exit(1)


if __name__ == "__main__":
    add_regulatory_documents()
