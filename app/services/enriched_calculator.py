"""
Enriched Layer Calculator

Handles calculation of enriched Layer 1 metrics by:
1. Fetching project data from knowledge graph
2. Mapping Neo4j fields to enriched layer expectations
3. Executing Layer 1 formulas using enriched_layers_service
4. Formatting responses for API
"""

from typing import Dict, Optional, Any
import requests
from app.services.enriched_layers_service import get_enriched_layers_service, EnrichedAttribute


# Field mapping: enriched_layers_service field names → Neo4j field paths
FIELD_MAPPING = {
    # Units dimension (v4 nested format: add .value paths)
    'supply': ['totalSupplyUnits.value', 'totalSupplyUnits', 'projectSizeUnits.value', 'projectSizeUnits'],
    'total_units': ['totalSupplyUnits.value', 'totalSupplyUnits', 'projectSizeUnits.value', 'projectSizeUnits'],
    'annual_sales': ['annualSalesUnits.value', 'annualSalesUnits', 'annualSales.value', 'annualSales'],
    'sold_percent': ['soldPct.value', 'soldPct'],
    'unsold_percent': ['unsoldPct.value', 'unsoldPct'],
    'units': ['annualSalesUnits.value', 'annualSalesUnits', 'soldUnits.value', 'soldUnits'],  # For revenue calculations
    'soldUnits': ['soldUnits.value', 'soldUnits', 'projectSizeUnits.value', 'projectSizeUnits'],  # Sold units calculation

    # Cash dimension
    'value': ['annualSalesValueCr.value', 'annualSalesValueCr', 'totalRevenueCr.value', 'totalRevenueCr'],
    'totalRevenue': ['annualSalesValueCr.value', 'annualSalesValueCr'],
    'totalCost': ['l2_metrics.totalCostCr.value'],

    # Area dimension
    'size': ['unitSaleableSizeSqft.value', 'unitSaleableSizeSqft'],
    'avgUnitSize': ['unitSaleableSizeSqft.value', 'unitSaleableSizeSqft'],
    'totalArea': ['projectSizeAcres.value'],

    # Price (C/L²)
    'current_psf': ['currentPricePSF.value', 'currentPricePSF'],
    'launch_psf': ['launchPricePSF.value', 'launchPricePSF'],
    'currentPSF': ['currentPricePSF.value', 'currentPricePSF'],
    'launchPSF': ['launchPricePSF.value', 'launchPricePSF'],

    # Time dimension
    'launchDate': ['launchDate.value', 'launchDate'],
    'launch_date': ['launchDate.value', 'launchDate'],
    'possessionDate': ['possessionDate.value', 'possessionDate'],
    'possession_date': ['possessionDate.value', 'possessionDate'],
    'projectDuration': ['l2_metrics.projectDurationYears.value'],
    'project_duration': ['l2_metrics.projectDurationYears.value'],

    # Velocity
    'velocity_percent': ['monthlySalesVelocity.value', 'monthlySalesVelocity'],
    'monthlySalesVelocity': ['monthlySalesVelocity.value', 'monthlySalesVelocity'],

    # Calculated fields
    'monthly_units_sold': None,  # Will be calculated from annual_sales / 12
    'unsold': None,  # Will be calculated from supply × unsold_percent
    'monthly_sold': None,  # Alias for monthly_units_sold
}


class EnrichedLayerCalculator:
    """
    Calculator for enriched Layer 1 metrics

    Handles fetching project data and executing calculations
    using the enriched_layers_service.
    """

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        Initialize calculator

        Args:
            api_base_url: Base URL for the FastAPI backend
        """
        self.api_base_url = api_base_url
        self.enriched_service = get_enriched_layers_service()

    def calculate(self, capability: str, project_name: str, project_id: Optional[int] = None) -> Dict:
        """
        Execute enriched Layer 1 calculation

        Args:
            capability: Capability name (e.g., "calculate_sellout_time")
            project_name: Name of the project
            project_id: Optional project ID

        Returns:
            Calculation result dictionary

        Raises:
            ValueError: If attribute not found or calculation fails
        """
        # Extract attribute name from capability
        attr_name = self._parse_capability_name(capability)

        # Try exact match first
        attr = self.enriched_service.get_attribute(attr_name)

        # If not found, try fuzzy search with the parsed name (lowercase for better matching)
        if not attr:
            search_result = self.enriched_service.search_by_prompt(attr_name.lower())
            if search_result:
                attr, confidence = search_result
                # Use fuzzy match if confidence is reasonable
                if confidence < 0.3:
                    attr = None

        if not attr:
            raise ValueError(f"Attribute '{attr_name}' not found in enriched layers")

        if not attr.requires_calculation:
            raise ValueError(f"Attribute '{attr_name}' is Layer 0 (no calculation required)")

        # Fetch project data
        project_data = self._fetch_project_data(project_name, project_id)

        # Prepare data for calculation with field mapping
        mapped_data = self._map_fields(project_data)

        # Execute calculation
        result = self.enriched_service.execute_layer1_calculation(
            attr_name=attr.target_attribute,
            project_data=mapped_data
        )

        if not result:
            raise ValueError(f"Calculation failed for '{attr_name}'")

        # Format response
        return self._format_response(result, attr, project_name, project_data)

    def _parse_capability_name(self, capability: str) -> str:
        """
        Parse capability name to attribute name

        Examples:
        - "calculate_sellout_time" → "Sellout Time"
        - "calculate_months_of_inventory" → "Months Of Inventory"
        - "calculate_project_age_months" → "Project Age (Months)"
        """
        # Remove "calculate_" prefix
        name = capability.replace('calculate_', '')

        # Handle special cases with units in parentheses
        unit_mappings = {
            'project_age_months': 'Project Age (Months)',
            'time_to_possession_months': 'Time to Possession (Months)',
            'price_growth_percent': 'Price Growth (%)',  # FIXED: Was incorrectly mapped to "Price Growth Rate"
            'price_growth_rate': 'Price Growth Rate (% per Year)',  # Annual growth rate
        }

        if name in unit_mappings:
            return unit_mappings[name]

        # Replace underscores with spaces and title case
        name = name.replace('_', ' ').title()

        # Handle special cases
        replacements = {
            'Psf': 'PSF',
            'Asp': 'ASP',
            'Moi': 'MOI',
            'Npv': 'NPV',
            'Irr': 'IRR',
            'Roi': 'ROI',
        }

        for old, new in replacements.items():
            name = name.replace(old, new)

        return name

    def _fetch_project_data(self, project_name: str, project_id: Optional[int] = None) -> Dict:
        """
        Fetch project data from API

        Args:
            project_name: Project name
            project_id: Optional project ID

        Returns:
            Project data dictionary
        """
        try:
            # First, try to find project by name if ID not provided
            if not project_id:
                # Get all projects and find by name
                response = requests.get(f"{self.api_base_url}/api/projects", timeout=5)
                if response.status_code == 200:
                    projects = response.json()

                    # Normalize search term: lowercase, newlines to spaces, normalize whitespace
                    normalized_search = ' '.join(project_name.lower().replace('\n', ' ').split())

                    for proj in projects:
                        # Extract project name from v4 nested format
                        proj_name_obj = proj.get('projectName', {})
                        if isinstance(proj_name_obj, dict):
                            proj_name = proj_name_obj.get('value', '')
                        else:
                            proj_name = proj_name_obj or ''

                        # Normalize project name: lowercase, newlines to spaces, normalize whitespace
                        normalized_proj_name = ' '.join(proj_name.lower().replace('\n', ' ').split())

                        if normalized_proj_name == normalized_search:
                            # Extract project ID from v4 nested format
                            proj_id_obj = proj.get('projectId', {})
                            if isinstance(proj_id_obj, dict):
                                project_id = proj_id_obj.get('value')
                            else:
                                project_id = proj_id_obj
                            break

            # Fetch full project details
            if project_id:
                response = requests.get(f"{self.api_base_url}/api/projects/{project_id}", timeout=5)
                if response.status_code == 200:
                    return response.json()

            raise ValueError(f"Project '{project_name}' not found")

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to fetch project data: {e}")

    def _map_fields(self, project_data: Dict) -> Dict:
        """
        Map Neo4j field names to enriched layer field names

        Args:
            project_data: Raw project data from Neo4j/API

        Returns:
            Mapped data dictionary with enriched layer field names
        """
        mapped = {}

        for enriched_field, neo4j_paths in FIELD_MAPPING.items():
            if neo4j_paths is None:
                # This field will be calculated
                continue

            # Try each path until we find a value
            value = None
            for path in neo4j_paths:
                value = self._get_nested_value(project_data, path)
                if value is not None:
                    break

            if value is not None:
                mapped[enriched_field] = value

        # Calculate derived fields
        if 'annual_sales' in mapped and mapped['annual_sales']:
            mapped['monthly_units_sold'] = mapped['annual_sales'] / 12
            mapped['monthly_sold'] = mapped['monthly_units_sold']

        if 'supply' in mapped and 'unsold_percent' in mapped:
            mapped['unsold'] = mapped['supply'] * (mapped['unsold_percent'] / 100)
            mapped['unsoldUnits'] = mapped['unsold']

        if 'supply' in mapped and 'sold_percent' in mapped:
            mapped['sold'] = mapped['supply'] * (mapped['sold_percent'] / 100)
            # CRITICAL FIX: Also map to 'sold_units' for absorption rate calculation
            mapped['sold_units'] = mapped['sold']
            mapped['soldUnits'] = mapped['sold']

        # CRITICAL FIX: Calculate project_age_months for absorption rate and other calculations
        if 'launch_date' in mapped and mapped['launch_date']:
            from datetime import datetime
            from dateutil import parser

            try:
                # Parse launch date (format: "Nov 2007", "Apr 2023", etc.)
                launch_date = parser.parse(mapped['launch_date'])
                current_date = datetime.now()

                # Calculate duration in months
                months_diff = (current_date.year - launch_date.year) * 12 + (current_date.month - launch_date.month)

                mapped['project_age_months'] = months_diff
                mapped['duration_months'] = months_diff
                mapped['durationMonths'] = months_diff
            except Exception as e:
                # If parsing fails, don't set the value
                pass

        return mapped

    def _get_nested_value(self, data: Dict, path: str, default=None) -> Any:
        """
        Safely get nested dictionary value using dot notation

        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., "currentPricePSF.value")
            default: Default value if not found

        Returns:
            Value at path or default
        """
        keys = path.split('.')
        result = data

        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
                if result is None:
                    return default
            else:
                return default

        return result if result is not None else default

    def _format_response(self, result: Dict, attr: EnrichedAttribute,
                        project_name: str, raw_data: Dict) -> Dict:
        """
        Format calculation result for API response

        Args:
            result: Calculation result from enriched_layers_service
            attr: Attribute definition
            project_name: Project name
            raw_data: Raw project data (for reference)

        Returns:
            Formatted response dictionary
        """
        # Build calculation details string
        if attr.target_attribute.lower() == 'sellout time':
            supply = raw_data.get('totalSupplyUnits', {}).get('value', 0)
            annual_sales = raw_data.get('annualSalesUnits', {}).get('value', 0)
            calc_details = f"Supply ({supply}) / Annual Sales ({annual_sales}) = {result['value']:.2f} {result['unit']}"
        else:
            calc_details = f"{result['formula']} = {result['value']} {result['unit']}"

        return {
            'status': 'success',
            'project': project_name,
            'attribute': attr.target_attribute,
            'value': result['value'],
            'unit': result['unit'],
            'dimension': result['dimension'],
            'formula': result['formula'],
            'calculation_details': calc_details,
            'layer': 1,
            'source': 'Liases Foras',  # Source is LF data, even for calculated metrics
            'provenance': {
                'dataSource': 'Liases Foras',
                'layer': 'Layer 1',
                'calculationMethod': result['formula'],
                'description': attr.description[:150]
            }
        }


# Global instance
_enriched_calculator = None


def get_enriched_calculator(api_base_url: str = "http://localhost:8000") -> EnrichedLayerCalculator:
    """Get global enriched calculator instance"""
    global _enriched_calculator
    if _enriched_calculator is None:
        _enriched_calculator = EnrichedLayerCalculator(api_base_url)
    return _enriched_calculator
