"""
Upload Managed RAG Documents to Gemini File Search

This script uploads the 3 managed RAG files to Google's Gemini File Search service:
1. LF-Layers_FULLY_ENRICHED_ALL_36.xlsx
2. Lf Capability Pitch Document.docx
3. Glossary.pdf

Usage:
    python scripts/upload_to_gemini_file_search.py

Environment Variables:
    GOOGLE_API_KEY or GEMINI_API_KEY: Required for authentication

Output:
    - Prints file_search_store name and file IDs
    - Stores FILE_SEARCH_STORE_NAME in .env for future use
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Try to import google-genai SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ ERROR: google-genai package not installed")
    print("\nInstall with:")
    print("  pip install google-genai")
    sys.exit(1)


class GeminiFileSearchUploader:
    """
    Uploader for Gemini File Search managed RAG system
    """

    def __init__(self, api_key: str):
        """
        Initialize uploader with API key

        Args:
            api_key: Google API key for Gemini
        """
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.file_search_store_name = None
        self.uploaded_files = []

    def create_file_search_store(self, display_name: str = "ATLAS Managed RAG Store") -> str:
        """
        Create a new File Search store for managed RAG

        Args:
            display_name: Human-readable name for the store

        Returns:
            File search store name (resource identifier)
        """
        print(f"\n{'='*80}")
        print(f"CREATING FILE SEARCH STORE: {display_name}")
        print(f"{'='*80}\n")

        try:
            # Create file search store (no parameters supported in current API)
            file_search_store = self.client.file_search_stores.create()

            self.file_search_store_name = file_search_store.name

            print(f"✅ File Search Store created successfully!")
            print(f"   Name: {file_search_store.name}")
            print(f"   Display Name: {file_search_store.display_name}")

            return file_search_store.name

        except Exception as e:
            print(f"❌ ERROR creating File Search Store: {e}")
            raise

    def upload_file(self, file_path: str, display_name: str = None) -> dict:
        """
        Upload a file to the File Search store

        Args:
            file_path: Path to file to upload
            display_name: Optional display name (defaults to filename)

        Returns:
            Dict with file metadata
        """
        if not self.file_search_store_name:
            raise ValueError("File Search Store not created yet. Call create_file_search_store() first.")

        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if display_name is None:
            display_name = file_path_obj.name

        print(f"\n📤 Uploading: {file_path_obj.name}")
        print(f"   Size: {file_path_obj.stat().st_size / 1024:.2f} KB")

        try:
            # Upload file to File Search store
            upload_op = self.client.file_search_stores.upload_to_file_search_store(
                file=str(file_path_obj),
                file_search_store_name=self.file_search_store_name
            )

            # Wait for upload to complete
            print(f"   ⏳ Waiting for upload and indexing to complete...")

            # Get the file metadata from the operation
            file_metadata = {
                "display_name": display_name,
                "file_path": str(file_path_obj),
                "operation": upload_op.name if hasattr(upload_op, 'name') else "unknown",
                "status": "uploaded"
            }

            self.uploaded_files.append(file_metadata)

            print(f"   ✅ Upload successful!")
            if hasattr(upload_op, 'name'):
                print(f"   Operation ID: {upload_op.name}")

            return file_metadata

        except Exception as e:
            print(f"   ❌ ERROR uploading file: {e}")
            raise

    def upload_managed_rag_files(self) -> dict:
        """
        Upload all 3 managed RAG files

        Returns:
            Dict with upload summary
        """
        # Define file paths
        base_dir = Path(__file__).parent.parent
        managed_rag_dir = base_dir / "change-request" / "managed-rag"

        files_to_upload = [
            {
                "path": managed_rag_dir / "LF-Layers_FULLY_ENRICHED_ALL_36.xlsx",
                "display_name": "LF Layers (Fully Enriched - All 36 Attributes)"
            },
            {
                "path": managed_rag_dir / "Lf Capability Pitch Document.docx",
                "display_name": "LF Capability Pitch Document"
            },
            {
                "path": managed_rag_dir / "Glossary.pdf",
                "display_name": "Real Estate Glossary"
            }
        ]

        print(f"\n{'='*80}")
        print(f"UPLOADING MANAGED RAG FILES")
        print(f"{'='*80}")
        print(f"Total files: {len(files_to_upload)}")
        print(f"Destination: {self.file_search_store_name}")

        # Upload each file
        uploaded_count = 0
        failed_count = 0

        for file_info in files_to_upload:
            try:
                self.upload_file(
                    file_path=str(file_info["path"]),
                    display_name=file_info["display_name"]
                )
                uploaded_count += 1
            except Exception as e:
                print(f"\n⚠️  Failed to upload {file_info['display_name']}: {e}")
                failed_count += 1

        # Summary
        print(f"\n{'='*80}")
        print(f"UPLOAD SUMMARY")
        print(f"{'='*80}")
        print(f"✅ Successfully uploaded: {uploaded_count}/{len(files_to_upload)}")
        if failed_count > 0:
            print(f"❌ Failed: {failed_count}")

        return {
            "file_search_store_name": self.file_search_store_name,
            "total_files": len(files_to_upload),
            "uploaded": uploaded_count,
            "failed": failed_count,
            "files": self.uploaded_files
        }

    def save_config_to_env(self):
        """
        Save file_search_store_name to .env file
        """
        env_file = Path(__file__).parent.parent / ".env"

        print(f"\n{'='*80}")
        print(f"SAVING CONFIGURATION")
        print(f"{'='*80}")

        # Read existing .env
        env_content = ""
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_content = f.read()

        # Check if FILE_SEARCH_STORE_NAME already exists
        if "FILE_SEARCH_STORE_NAME" in env_content:
            print("⚠️  FILE_SEARCH_STORE_NAME already exists in .env")
            print("   Please update manually if needed:")
        else:
            # Append to .env
            with open(env_file, 'a') as f:
                f.write(f"\n# Gemini File Search Store (Managed RAG)\n")
                f.write(f"FILE_SEARCH_STORE_NAME={self.file_search_store_name}\n")
            print("✅ Added FILE_SEARCH_STORE_NAME to .env")

        print(f"\nFile Search Store Name:")
        print(f"  {self.file_search_store_name}")


def main():
    """Main upload workflow"""
    print(f"\n{'#'*80}")
    print(f"# GEMINI FILE SEARCH UPLOAD UTILITY")
    print(f"# Upload Managed RAG Documents for ATLAS")
    print(f"{'#'*80}\n")

    # Get API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("❌ ERROR: GOOGLE_API_KEY or GEMINI_API_KEY not found in environment")
        print("\nPlease set one of these environment variables in your .env file:")
        print("  GOOGLE_API_KEY=your_api_key_here")
        print("  or")
        print("  GEMINI_API_KEY=your_api_key_here")
        sys.exit(1)

    print(f"✅ API Key found: ***************")

    # Create uploader
    uploader = GeminiFileSearchUploader(api_key=api_key)

    try:
        # Step 1: Create File Search Store
        uploader.create_file_search_store(
            display_name="ATLAS Managed RAG Store (Liases Foras Intelligence)"
        )

        # Step 2: Upload all managed RAG files
        summary = uploader.upload_managed_rag_files()

        # Step 3: Save configuration
        uploader.save_config_to_env()

        # Final summary
        print(f"\n{'#'*80}")
        print(f"# UPLOAD COMPLETE")
        print(f"{'#'*80}\n")

        if summary["failed"] == 0:
            print("✅ All files uploaded successfully!")
        else:
            print(f"⚠️  {summary['failed']} file(s) failed to upload")

        print(f"\nNext steps:")
        print(f"1. Add FILE_SEARCH_STORE_NAME to your .env file (if not auto-added)")
        print(f"2. Use this store name in your Gemini File Search adapter")
        print(f"3. Configure function calling with knowledge_graph_lookup tool")
        print(f"\nStore Name: {summary['file_search_store_name']}")

    except Exception as e:
        print(f"\n❌ UPLOAD FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
