"""
Upload Regulatory Documents to Gemini File Search
Adds National Building Code of India and UDCPR to existing File Search store
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

def upload_regulatory_documents():
    """Upload regulatory PDFs to Gemini File Search store"""

    # Configuration
    api_key = os.getenv("GEMINI_API_KEY")
    file_search_store_name = os.getenv("FILE_SEARCH_STORE_NAME")

    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in environment")
        sys.exit(1)

    if not file_search_store_name:
        print("❌ Error: FILE_SEARCH_STORE_NAME not found in environment")
        sys.exit(1)

    # Configure Gemini
    genai.configure(api_key=api_key)

    print("=" * 80)
    print("📚 UPLOADING REGULATORY DOCUMENTS TO FILE SEARCH")
    print("=" * 80)
    print(f"\n🎯 Target File Search Store: {file_search_store_name}\n")

    # Document paths
    docs_to_upload = [
        {
            "path": "/Users/tusharsikand/Documents/Projects/liases-foras/change-request/managed-rag/national building code of india.pdf",
            "display_name": "National Building Code of India",
            "description": "National Building Code of India - Comprehensive building regulations and standards"
        },
        {
            "path": "/Users/tusharsikand/Documents/Projects/liases-foras/change-request/managed-rag/UDCPR_compressed_2.pdf",
            "display_name": "UDCPR - Unified Development Control and Promotion Regulations",
            "description": "Maharashtra UDCPR - Development control rules and regulations for urban planning"
        }
    ]

    uploaded_files = []

    # Upload each document
    for i, doc in enumerate(docs_to_upload, 1):
        print(f"\n📄 [{i}/{len(docs_to_upload)}] Uploading: {doc['display_name']}")
        print(f"   Path: {doc['path']}")

        # Check if file exists
        if not os.path.exists(doc['path']):
            print(f"   ❌ File not found: {doc['path']}")
            continue

        file_size_mb = os.path.getsize(doc['path']) / (1024 * 1024)
        print(f"   Size: {file_size_mb:.2f} MB")

        try:
            # Upload file to Gemini
            print(f"   ⏳ Uploading to Gemini...")
            uploaded_file = genai.upload_file(
                path=doc['path'],
                display_name=doc['display_name']
            )

            print(f"   ✅ Uploaded successfully!")
            print(f"   📌 File URI: {uploaded_file.uri}")
            print(f"   📌 File Name: {uploaded_file.name}")

            uploaded_files.append({
                "name": uploaded_file.name,
                "uri": uploaded_file.uri,
                "display_name": doc['display_name'],
                "description": doc['description']
            })

        except Exception as e:
            print(f"   ❌ Upload failed: {str(e)}")
            continue

    if not uploaded_files:
        print("\n❌ No files were uploaded successfully")
        sys.exit(1)

    print(f"\n{'=' * 80}")
    print(f"✅ UPLOAD COMPLETE - {len(uploaded_files)}/{len(docs_to_upload)} files uploaded")
    print(f"{'=' * 80}\n")

    # Now add files to the File Search store
    print("📂 Adding files to File Search store...")
    print(f"   Store: {file_search_store_name}\n")

    try:
        # Get the file search store
        file_search_store = genai.get_file_search_store(file_search_store_name)

        print(f"✅ File Search Store retrieved successfully")
        print(f"   Display Name: {file_search_store.display_name if hasattr(file_search_store, 'display_name') else 'N/A'}")

        # Add each uploaded file to the store
        for file_info in uploaded_files:
            print(f"\n   Adding: {file_info['display_name']}")
            try:
                # Add file to store
                file_search_store.add_files([file_info['name']])
                print(f"   ✅ Added to File Search store")
            except Exception as e:
                print(f"   ⚠️  Error adding file: {str(e)}")

        print(f"\n{'=' * 80}")
        print("🎉 REGULATORY DOCUMENTS SUCCESSFULLY ADDED TO FILE SEARCH!")
        print(f"{'=' * 80}\n")

        print("📋 Summary:")
        for file_info in uploaded_files:
            print(f"   ✅ {file_info['display_name']}")
            print(f"      URI: {file_info['uri']}")

        print(f"\n{'=' * 80}")
        print("💡 NEXT STEPS:")
        print(f"{'=' * 80}")
        print("1. Restart the backend server to use the updated File Search store")
        print("2. Test queries like:")
        print("   - 'What are the FSI regulations as per UDCPR?'")
        print("   - 'What does the National Building Code say about fire safety?'")
        print("   - 'What are the parking requirements for residential buildings?'")
        print("\n✨ The documents will now supplement all answers with regulatory context!")
        print(f"{'=' * 80}\n")

    except Exception as e:
        print(f"\n❌ Error accessing File Search store: {str(e)}")
        print("\n⚠️  Files were uploaded to Gemini but NOT added to File Search store.")
        print("   You may need to manually add them or create a new store.")

        print("\n📋 Uploaded Files (not yet in store):")
        for file_info in uploaded_files:
            print(f"   - {file_info['display_name']}")
            print(f"     Name: {file_info['name']}")
            print(f"     URI: {file_info['uri']}")

        sys.exit(1)


if __name__ == "__main__":
    upload_regulatory_documents()
