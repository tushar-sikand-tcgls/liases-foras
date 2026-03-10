"""
Project Adapter - Wraps data_service to implement ports

This adapter makes data_service compatible with the hexagonal
architecture by implementing ProjectQueryPort and ProjectRepositoryPort.
"""

from typing import Dict, List, Optional
from app.ports.input_ports import ProjectQueryPort
from app.ports.output_ports import ProjectRepositoryPort
from app.services.data_service import data_service


class ProjectServiceAdapter(ProjectQueryPort, ProjectRepositoryPort):
    """
    Adapter that wraps data_service to implement project-related ports

    Implements:
    - ProjectQueryPort (input port for querying projects)
    - ProjectRepositoryPort (output port for project persistence)
    """

    def __init__(self):
        self.service = data_service

    # ProjectQueryPort implementation
    def get_project_by_id(self, project_id: str) -> Optional[Dict]:
        """Get project by ID"""
        return self.service.get_project(project_id)

    def get_project_by_name(self, project_name: str) -> Optional[Dict]:
        """Get project by name"""
        all_projects = self.service.get_all_projects()

        # Normalize search term
        normalized_search = ' '.join(project_name.lower().replace('\n', ' ').split())

        for proj in all_projects:
            # Extract project name from v4 nested format
            proj_name_obj = proj.get('projectName', {})
            if isinstance(proj_name_obj, dict):
                proj_name = proj_name_obj.get('value', '')
            else:
                proj_name = proj_name_obj or ''

            # Normalize project name
            normalized_proj_name = ' '.join(proj_name.lower().replace('\n', ' ').split())

            if normalized_proj_name == normalized_search:
                return proj

        return None

    def search_projects(
        self,
        location: Optional[str] = None,
        developer: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Search projects with filters"""
        all_projects = self.service.get_all_projects()
        results = []

        for proj in all_projects:
            # Location filter
            if location:
                proj_location = self.service.get_value(proj.get('location', ''))
                if not proj_location or location.lower() not in proj_location.lower():
                    continue

            # Developer filter
            if developer:
                proj_developer = self.service.get_value(proj.get('developerName', ''))
                if not proj_developer or developer.lower() not in proj_developer.lower():
                    continue

            # Custom filters
            if filters:
                skip_project = False
                for field, expected_value in filters.items():
                    actual_value = self.service.get_value(proj.get(field))
                    if actual_value != expected_value:
                        skip_project = True
                        break
                if skip_project:
                    continue

            results.append(proj)

        return results

    def list_all_projects(self) -> List[Dict]:
        """List all projects"""
        return self.service.get_all_projects()

    # ProjectRepositoryPort implementation
    def find_by_id(self, project_id: str) -> Optional[Dict]:
        """Find project by ID"""
        return self.get_project_by_id(project_id)

    def find_by_name(self, project_name: str) -> Optional[Dict]:
        """Find project by name"""
        return self.get_project_by_name(project_name)

    def find_all(self) -> List[Dict]:
        """Get all projects"""
        return self.list_all_projects()

    def find_by_location(self, location: str) -> List[Dict]:
        """Find projects by location"""
        return self.search_projects(location=location)
