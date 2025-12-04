"""
Calculator Agent - Python Functions L1/L2

Executes deterministic calculations using existing calculators
"""

from typing import Dict, Any, List
from app.services.graph_state import GraphState
from app.calculators.layer1 import Layer1Calculator
from app.calculators.layer2 import Layer2Calculator


def calculate_layer1_from_layer0(layer0_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate Layer 1 metrics from Layer 0 data

    Args:
        layer0_data: Layer 0 dimensions

    Returns:
        Dict with Layer 1 metrics
    """
    projects = layer0_data.get("projects", [])

    if not projects:
        return {"error": "No Layer 0 data available"}

    layer1_results = []
    calculator = Layer1Calculator()

    # Aggregate metrics
    psf_values = []
    asp_values = []
    absorption_rates = []
    velocities = []
    densities = []

    for project in projects:
        project_metrics = {
            "project_id": project.get("project_id"),
            "project_name": project.get("project_name"),
            "metrics": {}
        }

        # PSF (already in Layer 0 typically)
        psf = project.get("current_price_psf")
        if psf:
            project_metrics["metrics"]["PSF"] = {
                "value": psf,
                "unit": "INR/sqft",
                "dimension": "C/L²"
            }
            psf_values.append(psf)

        # ASP
        avg_selling_price = project.get("avg_selling_price")
        if avg_selling_price:
            project_metrics["metrics"]["ASP"] = {
                "value": avg_selling_price,
                "unit": "INR",
                "dimension": "C/U"
            }
            asp_values.append(avg_selling_price)

        # Absorption Rate (if data available)
        total_units = project.get("total_units")
        sold_units = project.get("sold_units")
        project_duration = project.get("project_duration_months")

        if total_units and sold_units and project_duration:
            absorption_rate = (sold_units / total_units) / project_duration * 100
            project_metrics["metrics"]["Absorption_Rate"] = {
                "value": absorption_rate,
                "unit": "%/month",
                "dimension": "(U_sold/U_total)/T"
            }
            absorption_rates.append(absorption_rate)

        # Sales Velocity
        if sold_units and project_duration:
            velocity = sold_units / project_duration
            project_metrics["metrics"]["Sales_Velocity"] = {
                "value": velocity,
                "unit": "units/month",
                "dimension": "U/T"
            }
            velocities.append(velocity)

        # Density
        land_area = project.get("land_area_acres")
        if total_units and land_area and land_area > 0:
            density = total_units / land_area
            project_metrics["metrics"]["Density"] = {
                "value": density,
                "unit": "units/acre",
                "dimension": "U/L²"
            }
            densities.append(density)

        layer1_results.append(project_metrics)

    # Calculate aggregates
    aggregates = {}

    if psf_values:
        aggregates["avg_psf"] = sum(psf_values) / len(psf_values)
        aggregates["min_psf"] = min(psf_values)
        aggregates["max_psf"] = max(psf_values)

    if asp_values:
        aggregates["avg_asp"] = sum(asp_values) / len(asp_values)

    if absorption_rates:
        aggregates["avg_absorption_rate"] = sum(absorption_rates) / len(absorption_rates)

    if velocities:
        aggregates["avg_sales_velocity"] = sum(velocities) / len(velocities)

    if densities:
        aggregates["avg_density"] = sum(densities) / len(densities)

    return {
        "project_metrics": layer1_results,
        "aggregates": aggregates,
        "total_projects": len(projects),
        "metrics_calculated": len([m for m in layer1_results if m.get("metrics")])
    }


def calculator_agent_node(state: GraphState) -> GraphState:
    """
    Calculator Agent Node - LangGraph node function

    Calculates Layer 1 and Layer 2 metrics from Layer 0 data

    Args:
        state: Current graph state

    Returns:
        Updated state with layer1_metrics and optionally layer2_insights
    """

    layer0_data = state.get("layer0_data")
    errors = []
    warnings = []
    layer1_metrics = None

    if not layer0_data or not layer0_data.get("projects"):
        warnings.append("No Layer 0 data available. Skipping calculations.")
        layer1_metrics = {"error": "No Layer 0 data"}

    else:
        try:
            # Calculate Layer 1 metrics
            layer1_metrics = calculate_layer1_from_layer0(layer0_data)

            # Check if any metrics were calculated
            if layer1_metrics.get("metrics_calculated", 0) == 0:
                warnings.append("Layer 1 metrics calculated but many fields were null")

        except Exception as e:
            errors.append(f"Error calculating Layer 1 metrics: {str(e)}")
            layer1_metrics = {"error": str(e)}

    # Update confidence based on metrics availability
    confidence = state.get("confidence", 0.0)
    if layer1_metrics and not layer1_metrics.get("error"):
        metrics_count = layer1_metrics.get("metrics_calculated", 0)
        total_projects = layer1_metrics.get("total_projects", 1)
        # Increase confidence if we have metrics
        confidence = min(confidence + 0.3, 0.9) if metrics_count > 0 else confidence

    # Update state
    updated_state = {
        **state,
        "layer1_metrics": layer1_metrics,
        "confidence": confidence,
        "iteration": state["iteration"] + 1
    }

    # Add errors and warnings
    if errors:
        updated_state["errors"] = errors
    if warnings:
        updated_state["warnings"] = warnings

    # Log tool call
    tool_call = {
        "tool": "calculate_layer1_metrics",
        "args": {"layer0_projects": layer0_data.get("total_projects", 0) if layer0_data else 0},
        "result_summary": f"{layer1_metrics.get('metrics_calculated', 0)} projects with metrics",
        "aggregates": layer1_metrics.get("aggregates", {}) if layer1_metrics else {}
    }
    updated_state["tool_calls"] = [tool_call]

    return updated_state
