"""
Layer 0 Handler: Raw Dimensions (Atomic Units)

Handles Layer 0 base dimensional units:
- U (Units): Count of housing units
- L² (Space): Area in sqft/sqm
- T (Time): Months/years
- C (Cash): INR - analogous to Voltage in MLTI system
"""
from typing import Dict, Optional
from app.models.domain import Project


class Layer0Handler:
    """Handle Layer 0 raw dimensional data"""

    @staticmethod
    def get_project_dimensions(project: Project) -> Dict:
        """
        Extract all Layer 0 dimensions from a project

        Returns all atomic dimensional units (U, L², T, C)
        """
        return {
            "projectId": project.projectId,
            "projectName": project.projectName,
            "dimensions": {
                "U": {
                    "name": "Units",
                    "value": project.totalUnits,
                    "unit": "count",
                    "description": "Total number of housing units",
                    "analogyToPhysics": "Mass"
                },
                "L2": {
                    "name": "Area",
                    "values": {
                        "totalLandArea": project.totalLandArea_sqft,
                        "totalSaleableArea": project.totalSaleableArea_sqft,
                        "totalCarpetArea": project.totalCarpetArea_sqft
                    },
                    "unit": "sqft",
                    "description": "Area dimensions",
                    "analogyToPhysics": "Length²"
                },
                "T": {
                    "name": "Time",
                    "value": project.projectDuration_months,
                    "unit": "months",
                    "description": "Project duration",
                    "analogyToPhysics": "Time"
                },
                "C": {
                    "name": "Cash",
                    "values": {
                        "totalProjectCost": project.totalProjectCost_inr,
                        "totalRevenue": project.total_revenue
                    },
                    "unit": "INR",
                    "description": "Cash values",
                    "analogyToPhysics": "Voltage"
                }
            },
            "unitBreakdown": [
                {
                    "unitType": unit.unitType,
                    "count": unit.count,
                    "areaPerUnit_sqft": unit.areaPerUnit_sqft,
                    "pricePerUnit_inr": unit.pricePerUnit_inr
                }
                for unit in project.units
            ]
        }

    @staticmethod
    def validate_dimensional_consistency(project: Project) -> Dict:
        """
        Validate dimensional consistency of project data

        Checks:
        - Total saleable area = sum of unit areas
        - Total revenue = sum of unit prices
        - All dimensions are positive
        """
        errors = []
        warnings = []

        # Check positive dimensions
        if project.totalUnits <= 0:
            errors.append("Total units (U) must be positive")

        if project.totalLandArea_sqft <= 0:
            errors.append("Total land area (L²) must be positive")

        if project.projectDuration_months <= 0:
            errors.append("Project duration (T) must be positive")

        if project.totalProjectCost_inr <= 0:
            errors.append("Total project cost (C) must be positive")

        # Check area consistency
        calculated_saleable_area = sum(
            unit.saleablePerUnit_sqft * unit.count
            for unit in project.units
        )
        area_diff_percent = abs(calculated_saleable_area - project.totalSaleableArea_sqft) / project.totalSaleableArea_sqft * 100

        if area_diff_percent > 5:  # Allow 5% tolerance
            warnings.append(
                f"Saleable area mismatch: declared={project.totalSaleableArea_sqft}, "
                f"calculated={calculated_saleable_area} ({area_diff_percent:.1f}% difference)"
            )

        # Check revenue consistency
        calculated_revenue = project.total_revenue
        if calculated_revenue <= 0:
            errors.append("Total revenue must be positive")

        # Check unit count consistency
        total_unit_count = sum(unit.count for unit in project.units)
        if total_unit_count != project.totalUnits:
            errors.append(
                f"Unit count mismatch: declared={project.totalUnits}, "
                f"calculated={total_unit_count}"
            )

        # Check land area utilization
        if project.totalSaleableArea_sqft > project.totalLandArea_sqft:
            errors.append(
                f"Saleable area ({project.totalSaleableArea_sqft}) exceeds land area ({project.totalLandArea_sqft})"
            )

        is_valid = len(errors) == 0

        return {
            "isValid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "dimensionalChecks": {
                "U_positive": project.totalUnits > 0,
                "L2_positive": project.totalLandArea_sqft > 0,
                "T_positive": project.projectDuration_months > 0,
                "C_positive": project.totalProjectCost_inr > 0,
                "area_consistency": area_diff_percent <= 5,
                "unit_count_consistency": total_unit_count == project.totalUnits
            }
        }
