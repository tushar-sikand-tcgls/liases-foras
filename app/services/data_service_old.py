"""
Data Service: In-memory data management for projects and LF data
"""
import json
from pathlib import Path
from typing import List, Optional, Dict
from app.models.domain import Project
from app.config import settings


class DataService:
    """In-memory data service for mock data"""

    def __init__(self):
        self.projects: List[Project] = []
        self.lf_data: Dict = {}
        self._load_data()

    def _load_data(self):
        """Load all data from JSON files"""
        self._load_projects()
        self._load_lf_data()

    def _load_projects(self):
        """Load sample projects"""
        projects_file = Path(settings.DATA_PATH) / "sample_projects.json"

        if not projects_file.exists():
            print(f"Warning: {projects_file} not found")
            return

        with open(projects_file, 'r') as f:
            data = json.load(f)

        self.projects = [Project(**p) for p in data]
        print(f"✓ Loaded {len(self.projects)} projects")

    def _load_lf_data(self):
        """Load LF mock responses"""
        lf_dir = Path(settings.DATA_PATH) / "lf_mock_responses"

        if not lf_dir.exists():
            print(f"Warning: {lf_dir} not found")
            return

        pillars = ['pillar1_market', 'pillar2_product', 'pillar3_developer',
                   'pillar4_financial', 'pillar5_sales']

        for pillar in pillars:
            file_path = lf_dir / f"{pillar}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    self.lf_data[pillar] = json.load(f)

        print(f"✓ Loaded {len(self.lf_data)} LF pillar datasets")

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        return next((p for p in self.projects if p.projectId == project_id), None)

    def get_all_projects(self) -> List[Project]:
        """Get all projects"""
        return self.projects

    def get_projects_by_location(self, city: str, micro_market: Optional[str] = None) -> List[Project]:
        """Get projects by location"""
        results = [p for p in self.projects if p.location.city == city]

        if micro_market:
            results = [p for p in results if p.location.microMarket == micro_market]

        return results

    def get_lf_market_data(self, location: str) -> Dict:
        """Get LF Pillar 1 market data"""
        return self.lf_data.get('pillar1_market', {}).get('data', {})

    def get_lf_product_data(self, location: str) -> Dict:
        """Get LF Pillar 2 product data"""
        return self.lf_data.get('pillar2_product', {}).get('data', {})

    def get_lf_developer_rating(self, developer_id: str) -> Dict:
        """Get LF Pillar 3 developer ratings"""
        pillar3_data = self.lf_data.get('pillar3_developer', {})
        developers = pillar3_data.get('developers', [])

        developer = next((d for d in developers if d['developer_id'] == developer_id), None)
        return developer if developer else {}

    def get_lf_financial_benchmarks(self) -> Dict:
        """Get LF Pillar 4 financial benchmarks"""
        return self.lf_data.get('pillar4_financial', {}).get('benchmarks', {})

    def get_market_data_for_optimization(self, location: str) -> Dict:
        """
        Get market data formatted for Layer 3 optimization

        Returns pricing, area, and absorption rates by unit type
        """
        pillar2_data = self.get_lf_product_data(location)
        typology = pillar2_data.get('typology_performance', {})

        # Get reference project for pricing
        projects = self.get_projects_by_location("Pune", "Chakan")
        if not projects:
            raise ValueError(f"No projects found for location: {location}")

        ref_project = projects[0]  # Use first project as reference

        # Build market data dict
        market_data = {}
        for unit in ref_project.units:
            unit_type = unit.unitType
            market_data[unit_type] = {
                'price': unit.pricePerUnit_inr,
                'area': unit.saleablePerUnit_sqft,
                'absorption': typology.get(unit_type, {}).get('absorption_rate_monthly', 0.03)
            }

        return market_data


# Global data service instance
data_service = DataService()
