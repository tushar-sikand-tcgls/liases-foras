"""
DataService KG Adapter - Knowledge Graph Implementation

This adapter wraps the existing data_service.py to conform to the
KnowledgeGraphPort interface, allowing it to be used in the LangGraph orchestrator.

Reuses existing infrastructure:
- app.services.data_service for Neo4j/data access
- app.services.graphrag_orchestrator for entity resolution
"""

from typing import List, Dict, Optional, Any
from app.ports.knowledge_graph_port import KnowledgeGraphPort
from app.services.data_service import data_service, get_data_service
from app.services.graphrag_orchestrator import get_graphrag_orchestrator


# ============================================================================
# ATTRIBUTE NAME MAPPINGS
# Maps from natural language / Vector DB attribute names to actual KG fields
# ============================================================================

ATTRIBUTE_MAPPINGS = {
    # Project Size variations
    'Project Size': 'projectSizeUnits',
    'Total Units': 'projectSizeUnits',
    'project size': 'projectSizeUnits',
    'total units': 'projectSizeUnits',

    # Total Supply variations
    'Total Supply': 'totalSupplyUnits',
    'Total Supply (Units)': 'totalSupplyUnits',
    'total supply': 'totalSupplyUnits',

    # Sold percentage variations
    'Sold %': 'soldPct',
    'Sold (%)': 'soldPct',
    'Sold (%) - Total Supply': 'soldPct',
    'sold percentage': 'soldPct',
    'sold pct': 'soldPct',

    # Unsold percentage variations
    'Unsold %': 'unsoldPct',
    'Unsold (%)': 'unsoldPct',
    'unsold percentage': 'unsoldPct',
    'unsold pct': 'unsoldPct',

    # Annual Sales variations
    'Annual Sales (Units)': 'annualSalesUnits',
    'Annual Sales Units': 'annualSalesUnits',
    'annual sales': 'annualSalesUnits',

    # Annual Sales Value variations
    'Annual Sales Value': 'annualSalesValueCr',
    'Annual Sales Value (Rs.Cr.)': 'annualSalesValueCr',
    'annual sales value': 'annualSalesValueCr',

    # Unit Size variations
    'Unit Saleable Size': 'unitSaleableSizeSqft',
    'Unit Saleable Size (Sq.Ft.)': 'unitSaleableSizeSqft',
    'unit size': 'unitSaleableSizeSqft',
    'saleable size': 'unitSaleableSizeSqft',

    # Launch Price variations
    'Saleable Launch Price': 'launchPricePSF',
    'Saleable Launch Price (Rs/Psf)': 'launchPricePSF',
    'Launch PSF': 'launchPricePSF',
    'launch price': 'launchPricePSF',

    # Current Price variations
    'Saleable Price': 'currentPricePSF',
    'Saleable Price (Psf)': 'currentPricePSF',
    'Current PSF': 'currentPricePSF',
    'current price': 'currentPricePSF',
    'PSF': 'currentPricePSF',
    'Effective Realised PSF': 'currentPricePSF',  # Layer 1 calculated attribute
    'effective realised psf': 'currentPricePSF',

    # Sales Velocity variations
    'Monthly Sales Velocity': 'monthlySalesVelocity',
    'Sales Velocity': 'monthlySalesVelocity',
    'sales velocity': 'monthlySalesVelocity',

    # Project info variations
    'Project Name': 'projectName',
    'Developer': 'developerName',
    'Developer Name': 'developerName',
    'Location': 'location',
    'Launch Date': 'launchDate',
    'Possession Date': 'possessionDate',
    'RERA Registered': 'reraRegistered',
}


class DataServiceKGAdapter(KnowledgeGraphPort):
    """Knowledge Graph adapter wrapping existing data_service"""

    def __init__(self, city: str = "Pune"):
        """
        Initialize with data service for specified city

        Args:
            city: City name for location-aware data loading (default: "Pune")
        """
        self.city = city
        self.ds = get_data_service(city)
        print(f"📍 KG Adapter initialized for city: {city}")

        # Use GraphRAG for intelligent entity resolution
        try:
            self.graphrag = get_graphrag_orchestrator()
        except:
            self.graphrag = None  # Fallback if GraphRAG not available

    def set_city(self, city: str):
        """
        Switch to a different city's data service

        Args:
            city: City name (e.g., "Pune", "Kolkata")
        """
        if city != self.city:
            print(f"📍 KG Adapter: Switching from '{self.city}' to '{city}'")
            self.city = city
            self.ds = get_data_service(city)

    def fetch_attribute(self, project: str, attribute: str) -> Any:
        """
        Fetch specific attribute value for a project

        Args:
            project: Project name (canonical)
            attribute: Attribute name (canonical)

        Returns:
            Attribute value with proper type
        """
        # Get project data
        proj_data = self.ds.get_project_by_name(project)
        if not proj_data:
            return None

        # STEP 1: Try explicit mapping first (HIGHEST PRIORITY)
        if attribute in ATTRIBUTE_MAPPINGS:
            mapped_field = ATTRIBUTE_MAPPINGS[attribute]
            if mapped_field in proj_data:
                return self.ds.get_value(proj_data[mapped_field])

        # STEP 2: Try direct field access
        if attribute in proj_data:
            return self.ds.get_value(proj_data[attribute])

        # STEP 3: Try case-insensitive mapping lookup
        attribute_lower = attribute.lower()
        for mapping_key, mapped_field in ATTRIBUTE_MAPPINGS.items():
            if mapping_key.lower() == attribute_lower:
                if mapped_field in proj_data:
                    return self.ds.get_value(proj_data[mapped_field])

        # STEP 4: Try normalized field access (handle variations)
        normalized_attr = self._normalize_attribute_name(attribute)

        for key in proj_data.keys():
            key_normalized = self._normalize_attribute_name(key)
            if key_normalized == normalized_attr:
                return self.ds.get_value(proj_data[key])

        return None

    def fetch_multiple_attributes(self, project: str, attributes: List[str]) -> Dict[str, Any]:
        """
        Fetch multiple attributes for a single project

        Args:
            project: Project name (canonical)
            attributes: List of attribute names

        Returns:
            Dict mapping attribute names to values
        """
        result = {}
        for attribute in attributes:
            value = self.fetch_attribute(project, attribute)
            if value is not None:
                result[attribute] = value
        return result

    def aggregate(
        self,
        attribute: str,
        aggregation: str,
        filters: Optional[Dict] = None
    ) -> float:
        """
        Aggregate attribute across multiple projects

        Args:
            attribute: Attribute name to aggregate
            aggregation: Aggregation function (sum, avg, max, min, count)
            filters: Optional filters (e.g., {"location": "Chakan"})

        Returns:
            Aggregated numeric value
        """
        # Get all projects
        projects = self.ds.get_all_projects()

        # Apply filters if provided
        if filters:
            if 'location' in filters:
                location_filter = filters['location'].lower()
                projects = [
                    p for p in projects
                    if self.ds.get_value(p.get('location', '')).lower() == location_filter
                ]

            if 'developer' in filters:
                developer_filter = filters['developer'].lower()
                projects = [
                    p for p in projects
                    if self.ds.get_value(p.get('developerName', '')).lower() == developer_filter
                ]

        # Extract attribute values
        values = []
        for proj in projects:
            value = self.fetch_attribute(
                self.ds.get_value(proj.get('projectName')),
                attribute
            )
            if value is not None and isinstance(value, (int, float)):
                values.append(float(value))

        if not values:
            return 0.0

        # Apply aggregation
        if aggregation == 'sum':
            return sum(values)
        elif aggregation == 'avg' or aggregation == 'mean':
            return sum(values) / len(values)
        elif aggregation == 'max':
            return max(values)
        elif aggregation == 'min':
            return min(values)
        elif aggregation == 'count':
            return float(len(values))
        else:
            return sum(values) / len(values)  # Default to average

    def compare(
        self,
        projects: List[str],
        attribute: str
    ) -> List[Dict[str, Any]]:
        """
        Compare attribute values across multiple projects

        Args:
            projects: List of project names
            attribute: Attribute to compare

        Returns:
            List of dicts with project name and attribute value
        """
        results = []
        for project in projects:
            value = self.fetch_attribute(project, attribute)
            if value is not None:
                results.append({
                    'project': project,
                    'attribute': attribute,
                    'value': value
                })
        return results

    def filter_projects_by_range(
        self,
        attribute: str,
        target_value: float,
        tolerance_pct: float = 10.0,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter projects where attribute value is within tolerance of target

        Enables range-based queries like "Show projects with units around 600 sq.ft"

        Args:
            attribute: Attribute name (e.g., 'Unit Saleable Size')
            target_value: Target value (e.g., 600)
            tolerance_pct: Tolerance percentage (default 10% = ±10%)
            location: Optional location filter (e.g., 'Chakan')

        Returns:
            List of dicts with:
            - project: Project name
            - attribute: Attribute name
            - value: Actual value
            - unit: Unit of measurement
            - distance_from_target: Absolute difference from target
            - percentage_diff: Percentage difference from target

        Example:
            >>> kg.filter_projects_by_range("Unit Saleable Size", 600, 10.0, "Chakan")
            [
                {'project': 'Pradnyesh Shriniwas', 'value': 562, 'distance_from_target': 38},
                {'project': 'Sara Abhiruchi Tower', 'value': 635, 'distance_from_target': 35},
                ...
            ]
        """
        # Calculate range
        min_val = target_value * (1 - tolerance_pct / 100)
        max_val = target_value * (1 + tolerance_pct / 100)

        # Get field name from attribute mapping
        field_name = ATTRIBUTE_MAPPINGS.get(attribute, attribute)

        # Get projects (filtered by location if specified)
        if location:
            projects = self.ds.get_projects_by_location(location)
        else:
            projects = self.ds.get_all_projects()

        results = []

        for project in projects:
            project_name = self.ds.get_value(project.get('projectName'))

            # Get attribute value
            attr_obj = project.get(field_name, {})
            if not isinstance(attr_obj, dict):
                continue

            value = self.ds.get_value(attr_obj)

            # Check if value is numeric and in range
            if value is not None and isinstance(value, (int, float)):
                if min_val <= value <= max_val:
                    unit = self.ds.get_unit(attr_obj)
                    distance = abs(value - target_value)
                    pct_diff = (distance / target_value) * 100 if target_value != 0 else 0

                    results.append({
                        'project': project_name,
                        'attribute': attribute,
                        'value': value,
                        'unit': unit,
                        'distance_from_target': distance,
                        'percentage_diff': round(pct_diff, 2)
                    })

        # Sort by closest to target (ascending distance)
        results.sort(key=lambda x: x['distance_from_target'])

        return results

    def filter_projects_by_comparison(
        self,
        attribute: str,
        operator: str,
        value: float,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter projects using comparison operators (>, <, =, >=, <=)

        Enables queries like:
        - "Show projects with price greater than 4000"
        - "Find projects with units less than 100"
        - "List projects with absorption rate equal to 1.5"

        Args:
            attribute: Attribute name (e.g., 'Current PSF', 'Total Supply Units')
            operator: Comparison operator ('>', '<', '=', '>=', '<=', '==')
            value: Comparison value
            location: Optional location filter

        Returns:
            List of dicts with:
            - project: Project name
            - attribute: Attribute name
            - value: Actual value
            - unit: Unit of measurement
            - comparison: Human-readable comparison result

        Example:
            >>> kg.filter_projects_by_comparison("Current PSF", ">", 4000)
            [
                {'project': 'Sara Nilaay', 'value': 4569, 'comparison': '4569 > 4000 ✓'},
                {'project': 'Gulmohar City', 'value': 4330, 'comparison': '4330 > 4000 ✓'},
                ...
            ]
        """
        # Normalize operator
        operator = operator.strip()
        if operator == '==':
            operator = '='

        # Get field name from attribute mapping
        field_name = ATTRIBUTE_MAPPINGS.get(attribute, attribute)

        # Get projects (filtered by location if specified)
        if location:
            projects = self.ds.get_projects_by_location(location)
        else:
            projects = self.ds.get_all_projects()

        results = []

        for project in projects:
            project_name = self.ds.get_value(project.get('projectName'))

            # Get attribute value
            attr_obj = project.get(field_name, {})
            if not isinstance(attr_obj, dict):
                continue

            attr_value = self.ds.get_value(attr_obj)

            # Check if value is numeric
            if attr_value is None or not isinstance(attr_value, (int, float)):
                continue

            # Apply comparison
            match = False
            if operator == '>':
                match = attr_value > value
            elif operator == '>=':
                match = attr_value >= value
            elif operator == '<':
                match = attr_value < value
            elif operator == '<=':
                match = attr_value <= value
            elif operator == '=':
                match = abs(attr_value - value) < 0.01  # Floating point tolerance

            if match:
                unit = self.ds.get_unit(attr_obj)
                comparison_str = f"{attr_value} {operator} {value} ✓"

                results.append({
                    'project': project_name,
                    'attribute': attribute,
                    'value': attr_value,
                    'unit': unit,
                    'comparison': comparison_str
                })

        # Sort by value (descending for >, ascending for <)
        if operator in ['>', '>=']:
            results.sort(key=lambda x: x['value'], reverse=True)
        elif operator in ['<', '<=']:
            results.sort(key=lambda x: x['value'])
        else:  # '='
            results.sort(key=lambda x: x['project'])

        return results

    def filter_projects_by_between(
        self,
        attribute: str,
        min_value: float,
        max_value: float,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter projects where attribute value is between min and max (inclusive)

        Enables queries like "Show projects with units between 500 and 1000"

        Args:
            attribute: Attribute name
            min_value: Minimum value (inclusive)
            max_value: Maximum value (inclusive)
            location: Optional location filter

        Returns:
            List of dicts with project, attribute, value, unit

        Example:
            >>> kg.filter_projects_by_between("Unit Saleable Size", 500, 700)
            [
                {'project': 'Pradnyesh Shriniwas', 'value': 562},
                {'project': 'Sarangi Paradise', 'value': 568},
                ...
            ]
        """
        # Get field name from attribute mapping
        field_name = ATTRIBUTE_MAPPINGS.get(attribute, attribute)

        # Get projects (filtered by location if specified)
        if location:
            projects = self.ds.get_projects_by_location(location)
        else:
            projects = self.ds.get_all_projects()

        results = []

        for project in projects:
            project_name = self.ds.get_value(project.get('projectName'))

            # Get attribute value
            attr_obj = project.get(field_name, {})
            if not isinstance(attr_obj, dict):
                continue

            attr_value = self.ds.get_value(attr_obj)

            # Check if value is numeric and in range
            if attr_value is not None and isinstance(attr_value, (int, float)):
                if min_value <= attr_value <= max_value:
                    unit = self.ds.get_unit(attr_obj)

                    results.append({
                        'project': project_name,
                        'attribute': attribute,
                        'value': attr_value,
                        'unit': unit,
                        'range_str': f"{min_value} - {max_value}"
                    })

        # Sort by value (ascending)
        results.sort(key=lambda x: x['value'])

        return results

    def resolve_project(self, project_name: str) -> Optional[str]:
        """
        Resolve fuzzy project name to canonical name

        Args:
            project_name: User-provided project name (may have typos, case issues)

        Returns:
            Canonical project name or None if not found
        """
        # Use GraphRAG if available
        if self.graphrag:
            try:
                all_projects = self.get_all_projects()
                # Let GraphRAG/UltraThink handle fuzzy matching
                response = self.graphrag.query(
                    f"Which project matches: {project_name}?",
                    available_projects=all_projects
                )
                if response.project_used:
                    return response.project_used
            except:
                pass

        # Fallback to simple normalization
        project_normalized = project_name.replace('\n', ' ').strip().lower()

        all_projects = self.ds.get_all_projects()
        for proj in all_projects:
            proj_name_obj = proj.get('projectName', {})
            if isinstance(proj_name_obj, dict):
                proj_name = proj_name_obj.get('value', '')
            else:
                proj_name = str(proj_name_obj)

            proj_name_normalized = proj_name.replace('\n', ' ').strip().lower()

            # Exact match or containment
            if proj_name_normalized == project_normalized or \
               project_normalized in proj_name_normalized or \
               proj_name_normalized in project_normalized:
                return proj_name

        return None

    def resolve_developer(self, developer_name: str) -> Optional[str]:
        """
        Resolve fuzzy developer name to canonical name

        Args:
            developer_name: User-provided developer name

        Returns:
            Canonical developer name or None if not found
        """
        developer_normalized = developer_name.strip().lower()

        all_projects = self.ds.get_all_projects()
        developers = set()

        for proj in all_projects:
            dev_name = self.ds.get_value(proj.get('developerName', ''))
            if dev_name:
                developers.add(dev_name)

        for dev in developers:
            dev_normalized = dev.strip().lower()
            if dev_normalized == developer_normalized or \
               developer_normalized in dev_normalized or \
               dev_normalized in developer_normalized:
                return dev

        return None

    def resolve_location(self, location_name: str) -> Optional[str]:
        """
        Resolve fuzzy location name to canonical name

        Args:
            location_name: User-provided location name

        Returns:
            Canonical location name or None if not found
        """
        location_normalized = location_name.strip().lower()

        all_projects = self.ds.get_all_projects()
        locations = set()

        for proj in all_projects:
            loc_name = self.ds.get_value(proj.get('location', ''))
            if loc_name:
                locations.add(loc_name)

        for loc in locations:
            loc_normalized = loc.strip().lower()
            if loc_normalized == location_normalized or \
               location_normalized in loc_normalized or \
               loc_normalized in location_normalized:
                return loc

        return None

    def find_projects_by_filter(self, filters: Dict) -> List[str]:
        """
        Find projects matching filters

        Args:
            filters: Dict of filters (e.g., {"location": "Chakan", "developer": "Sara Builders"})

        Returns:
            List of matching project names
        """
        projects = self.ds.get_all_projects()

        # Apply location filter
        if 'location' in filters:
            location_filter = filters['location'].lower()
            projects = [
                p for p in projects
                if self.ds.get_value(p.get('location', '')).lower() == location_filter
            ]

        # Apply developer filter
        if 'developer' in filters:
            developer_filter = filters['developer'].lower()
            projects = [
                p for p in projects
                if self.ds.get_value(p.get('developerName', '')).lower() == developer_filter
            ]

        # Extract project names
        return [self.ds.get_value(p.get('projectName')) for p in projects]

    def fetch_cash_flow_data(self, project: str) -> Dict[str, Any]:
        """
        Fetch cash flow proxies for financial calculations

        Args:
            project: Project name

        Returns:
            Dict with cash flow-related data
        """
        proj_data = self.ds.get_project_by_name(project)
        if not proj_data:
            return {}

        # Extract cash flow-related fields
        annual_sales = self.fetch_attribute(project, 'Annual Sales Value')
        total_investment = self.fetch_attribute(project, 'Total Investment')
        project_duration = self.fetch_attribute(project, 'Project Duration')

        result = {}

        if annual_sales:
            result['annual_sales'] = float(annual_sales)
            result['monthly_revenue_avg'] = float(annual_sales) / 12.0

        if total_investment:
            result['total_investment'] = float(total_investment)

        if project_duration:
            result['project_duration'] = int(project_duration)

        return result

    def get_all_projects(self) -> List[str]:
        """
        Get list of all project names in the KG

        Returns:
            List of all project names
        """
        all_projects = self.ds.get_all_projects()
        return [
            self.ds.get_value(proj.get('projectName'))
            for proj in all_projects
            if proj.get('projectName')
        ]

    def get_project_metadata(self, project: str) -> Dict[str, Any]:
        """
        Get comprehensive metadata for a project

        Args:
            project: Project name

        Returns:
            Dict with project metadata
        """
        proj_data = self.ds.get_project_by_name(project)
        if not proj_data:
            return {}

        # Extract key metadata fields
        metadata = {}
        for key, value in proj_data.items():
            metadata[key] = self.ds.get_value(value)

        return metadata

    def find_projects_within_radius(self, center_project: str, radius_km: float) -> List[Dict[str, Any]]:
        """
        Find all projects within a given radius of a center project using Haversine formula

        Args:
            center_project: Name of the center project
            radius_km: Radius in kilometers

        Returns:
            List of projects within radius with distance information
        """
        import math

        # Get center project coordinates
        center_lat = self.fetch_attribute(center_project, 'latitude')
        center_lon = self.fetch_attribute(center_project, 'longitude')

        if not center_lat or not center_lon:
            print(f"⚠️  Center project '{center_project}' has no coordinates")
            return []

        # Convert to float if dict
        if isinstance(center_lat, dict):
            center_lat = center_lat.get('value')
        if isinstance(center_lon, dict):
            center_lon = center_lon.get('value')

        nearby_projects = []

        # Check all projects
        all_projects = self.get_all_projects()
        for project_name in all_projects:
            if project_name == center_project:
                continue  # Skip center project itself

            # Get project coordinates
            proj_lat = self.fetch_attribute(project_name, 'latitude')
            proj_lon = self.fetch_attribute(project_name, 'longitude')

            if not proj_lat or not proj_lon:
                continue  # Skip projects without coordinates

            # Convert to float if dict
            if isinstance(proj_lat, dict):
                proj_lat = proj_lat.get('value')
            if isinstance(proj_lon, dict):
                proj_lon = proj_lon.get('value')

            # Calculate distance using Haversine formula
            distance_km = self._calculate_distance(center_lat, center_lon, proj_lat, proj_lon)

            if distance_km <= radius_km:
                nearby_projects.append({
                    'project': project_name,
                    'distance_km': round(distance_km, 2),
                    'latitude': proj_lat,
                    'longitude': proj_lon
                })

        # Sort by distance
        nearby_projects.sort(key=lambda x: x['distance_km'])

        return nearby_projects

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula

        Args:
            lat1: Latitude of point 1 (degrees)
            lon1: Longitude of point 1 (degrees)
            lat2: Latitude of point 2 (degrees)
            lon2: Longitude of point 2 (degrees)

        Returns:
            Distance in kilometers
        """
        import math

        # Earth radius in kilometers
        R = 6371.0

        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return distance

    def find_projects_near(self, reference_project_name: str, radius_km: float) -> List[Dict]:
        """
        Find all projects within a specified radius of a reference project

        Args:
            reference_project_name: Name of the reference project
            radius_km: Maximum distance from reference project (kilometers)

        Returns:
            List of nearby projects with distance information, sorted by distance (closest first).
            Each project dict includes all original fields plus 'distance_km' field.

        Raises:
            ValueError: If reference project not found or has no coordinates
        """
        # Use the JSONDataStore's find_projects_near method
        return self.ds.find_projects_near(reference_project_name, radius_km)

    def get_value(self, field: Any) -> Any:
        """
        Extract value from nested structure {value, unit, dimension}

        Args:
            field: Field that may be a nested dict or plain value

        Returns:
            Extracted value or original field if not nested
        """
        # Use data_service's get_value method
        return self.ds.get_value(field)

    def _normalize_attribute_name(self, attribute_name: str) -> str:
        """
        Normalize attribute name for matching

        Args:
            attribute_name: Attribute name

        Returns:
            Normalized attribute name
        """
        # Remove spaces, parentheses, special characters, lowercase
        normalized = attribute_name.lower()
        normalized = normalized.replace(' ', '').replace('(', '').replace(')', '')
        normalized = normalized.replace('_', '').replace('-', '')
        normalized = normalized.replace('%', 'pct')
        normalized = normalized.replace('\n', '')
        return normalized


# Global singleton instance
_data_service_kg_adapter = None


def get_data_service_kg_adapter() -> DataServiceKGAdapter:
    """
    Get or create global DataService KG adapter instance

    Returns:
        DataServiceKGAdapter singleton instance
    """
    global _data_service_kg_adapter

    if _data_service_kg_adapter is None:
        _data_service_kg_adapter = DataServiceKGAdapter()
        print(" DataService KG adapter initialized")

    return _data_service_kg_adapter
