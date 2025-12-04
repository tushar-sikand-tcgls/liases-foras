"""
V3.0.0 Data Refresh Service
===========================

Provides programmatic access to data refresh operations:
- Re-extract PDF data
- Reload L0+L1 to Neo4j
- Clear and refresh database

Exposes operations via FastAPI endpoint for UI button integration
"""

import os
import subprocess
from typing import Dict, List
from datetime import datetime


class DataRefreshService:
    """Service for refreshing Neo4j data from PDF extraction"""

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.scripts_dir = os.path.join(self.base_dir, "scripts")

    def run_script(self, script_name: str) -> Dict:
        """
        Run a Python script and capture output

        Args:
            script_name: Name of script file (e.g., "v3_extract_pdf_layer1_data.py")

        Returns:
            Dict with status, output, and error
        """
        script_path = os.path.join(self.scripts_dir, script_name)

        if not os.path.exists(script_path):
            return {
                "status": "error",
                "message": f"Script not found: {script_path}",
                "output": "",
                "error": f"File not found: {script_name}"
            }

        try:
            result = subprocess.run(
                ["python3", script_path],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )

            return {
                "status": "success" if result.returncode == 0 else "error",
                "message": f"Script {script_name} completed",
                "returncode": result.returncode,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else ""
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": f"Script {script_name} timed out after 120 seconds",
                "output": "",
                "error": "Timeout"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error running {script_name}: {str(e)}",
                "output": "",
                "error": str(e)
            }

    def refresh_all_data(self) -> Dict:
        """
        Complete data refresh pipeline:
        1. Extract PDF data directly to nested format (v4_extract_nested_pdf_data.py)

        Returns:
            Dict with pipeline status and step results
        """
        pipeline_start = datetime.now()
        results = []

        # Step 1: Extract PDF data to nested format
        print("Step 1/1: Extracting PDF data to nested format...")
        pdf_result = self.run_script("v4_extract_nested_pdf_data.py")
        results.append({
            "step": "PDF Extraction (Nested Format)",
            "script": "v4_extract_nested_pdf_data.py",
            **pdf_result
        })

        pipeline_status = "success" if pdf_result["status"] == "success" else "error"
        pipeline_end = datetime.now()

        return {
            "status": pipeline_status,
            "message": f"Data refresh pipeline {'completed successfully' if pipeline_status == 'success' else 'failed'}",
            "results": results,
            "duration_seconds": (pipeline_end - pipeline_start).total_seconds(),
            "timestamp": pipeline_end.isoformat()
        }

    def extract_pdf_only(self) -> Dict:
        """Run PDF extraction to nested format"""
        return self.run_script("v4_extract_nested_pdf_data.py")

    def get_data_status(self) -> Dict:
        """Get current data status (last extraction time, file sizes, etc.)"""
        json_file = os.path.join(
            self.base_dir,
            "data",
            "extracted",
            "v4_clean_nested_structure.json"
        )

        if os.path.exists(json_file):
            stat = os.stat(json_file)
            return {
                "status": "data_available",
                "last_extraction": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "file_size_bytes": stat.st_size,
                "file_path": json_file
            }
        else:
            return {
                "status": "no_data",
                "message": "No extracted data found. Run PDF extraction first."
            }


# Singleton instance
_data_refresh_service = None


def get_data_refresh_service() -> DataRefreshService:
    """Get singleton instance of DataRefreshService"""
    global _data_refresh_service
    if _data_refresh_service is None:
        _data_refresh_service = DataRefreshService()
    return _data_refresh_service
