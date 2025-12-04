"""
Data Agent - Knowledge Graph L0 Access

Retrieves raw dimensions (U, C, T, L²) from Knowledge Graph
"""

from typing import Dict, Any, List
from app.services.graph_state import GraphState
from app.services.data_service import data_service


def extract_layer0_dimensions(projects: List[Dict]) -> Dict[str, Any]:
    """
    Extract Layer 0 dimensions from projects

    Args:
        projects: List of project dicts

    Returns:
        Dict with Layer 0 data structure
    """
    layer0_projects = []

    for project in projects:
        project_l0 = {
            "project_id": project.get("projectId", {}).get("value"),
            "project_name": project.get("projectName", {}).get("value"),
            "developer": project.get("developerName", {}).get("value"),
            "location": project.get("location", {}).get("value"),
            "region": project.get("region", {}).get("value"),
            "micromarket": project.get("microMarket", {}).get("value"),

            # U - Units (dimension)
            "total_units": project.get("totalUnits", {}).get("value"),
            "sold_units": project.get("soldUnits", {}).get("value"),
            "unsold_units": project.get("unsoldUnits", {}).get("value"),

            # L² - Area (dimension)
            "saleable_area_sqft": project.get("saleableAreaSqft", {}).get("value"),
            "land_area_acres": project.get("landAreaAcres", {}).get("value"),
            "carpet_area_sqft": project.get("carpetAreaSqft", {}).get("value"),

            # T - Time (dimension)
            "launch_date": project.get("launchDate", {}).get("value"),
            "possession_date": project.get("possessionDate", {}).get("value"),
            "project_duration_months": project.get("projectDurationMonths", {}).get("value"),

            # C - Cashflow (dimension)
            "current_price_psf": project.get("currentPricePSF", {}).get("value"),
            "launch_price_psf": project.get("launchPricePSF", {}).get("value"),
            "total_revenue": project.get("totalRevenue", {}).get("value"),
            "avg_selling_price": project.get("avgSellingPrice", {}).get("value"),
        }

        layer0_projects.append(project_l0)

    return {
        "total_projects": len(layer0_projects),
        "projects": layer0_projects
    }


def calculate_completeness(layer0_data: Dict[str, Any]) -> float:
    """
    Calculate data completeness score (0-1)

    Args:
        layer0_data: Layer 0 data dict

    Returns:
        Completeness score
    """
    projects = layer0_data.get("projects", [])

    if not projects:
        return 0.0

    # Key fields to check
    key_fields = [
        "total_units",
        "sold_units",
        "saleable_area_sqft",
        "current_price_psf"
    ]

    total_fields = len(key_fields) * len(projects)
    filled_fields = 0

    for project in projects:
        for field in key_fields:
            if project.get(field) is not None:
                filled_fields += 1

    return filled_fields / total_fields if total_fields > 0 else 0.0


def data_agent_node(state: GraphState) -> GraphState:
    """
    Data Agent Node - LangGraph node function

    Retrieves Layer 0 data from Knowledge Graph

    Args:
        state: Current graph state

    Returns:
        Updated state with layer0_data and completeness score
    """

    region = state.get("region")
    project_id = state.get("project_id")

    errors = []
    warnings = []
    layer0_data = None

    try:
        # Fetch data based on what's available
        if project_id:
            # Get specific project
            projects = data_service.get_project_by_id(project_id)
            if projects:
                projects = [projects]  # Wrap in list
            else:
                warnings.append(f"Project ID {project_id} not found")
                projects = []

        elif region:
            # Get all projects in region
            projects = data_service.get_projects_by_location(region)

            if not projects:
                warnings.append(f"No projects found in region: {region}")

        else:
            # No region or project_id, try to extract from query
            # For now, use empty data
            warnings.append("No region or project_id specified. Cannot retrieve Layer 0 data.")
            projects = []

        # Extract Layer 0 dimensions
        if projects:
            layer0_data = extract_layer0_dimensions(projects)

            # Calculate completeness
            completeness = calculate_completeness(layer0_data)

            # Add warning if incomplete
            if completeness < 0.5:
                warnings.append(
                    f"Data completeness: {completeness:.0%}. Many fields are null."
                )

        else:
            completeness = 0.0
            layer0_data = {"total_projects": 0, "projects": []}

    except Exception as e:
        errors.append(f"Error fetching Layer 0 data: {str(e)}")
        completeness = 0.0
        layer0_data = {"total_projects": 0, "projects": []}

    # Update state
    updated_state = {
        **state,
        "layer0_data": layer0_data,
        "completeness": completeness,
        "iteration": state["iteration"] + 1
    }

    # Add errors and warnings (will be appended to lists)
    if errors:
        updated_state["errors"] = errors
    if warnings:
        updated_state["warnings"] = warnings

    # Log tool call
    tool_call = {
        "tool": "get_layer0_data",
        "args": {"region": region, "project_id": project_id},
        "result_summary": f"{layer0_data.get('total_projects', 0)} projects retrieved",
        "completeness": completeness
    }
    updated_state["tool_calls"] = [tool_call]

    return updated_state
