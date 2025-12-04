"""
Q&A Service: Simple Question Answering from Nested JSON Knowledge Graph

Handles basic factual queries about projects by extracting data from
nested JSON structure with L0 (dimensions), L1 (attributes), L2 (metrics).
"""

import re
from typing import Dict, Any, Optional, List
from app.services.data_service import data_service


class QAService:
    """
    Simple Q&A routing for basic project questions from nested JSON

    Routes queries to appropriate data layer:
    - Metadata: Project name, location, developer, dates, RERA
    - L1 Attributes: Numeric values with dimensions (units, area, price, etc.)
    - L2 Metrics: Calculated financials (NPV, IRR, ROI, revenue, etc.)
    """

    def __init__(self):
        # Question patterns for metadata and L1 attributes
        # IMPORTANT: More specific patterns must come FIRST to match correctly
        self.question_patterns = {
            # L1 - Units (U dimension) - CHECK FIRST before location pattern
            r"(how\s+many|number\s+of|total)\s+units": ("totalSupplyUnits", "units"),
            r"sold\s+units": ("soldUnits", "units"),
            r"annual\s+sales\s+units": ("annualSalesUnits", "units"),

            # L1 - Percentages - CHECK BEFORE generic patterns
            r"sold\s+(percent|percentage|%)": ("soldPct", "percentage"),
            r"unsold\s+(percent|percentage|%)": ("unsoldPct", "percentage"),
            r"(monthly\s+)?sales\s+velocity": ("monthlySalesVelocity", "percentage_per_month"),

            # L1 - Price (C/L² dimension)
            r"(current|saleable)\s+price": ("currentPricePSF", "price_psf"),
            r"launch\s+price": ("launchPricePSF", "price_psf"),

            # L1 - Cash Flow (C dimension)
            r"annual\s+sales\s+value": ("annualSalesValueCr", "currency_cr"),

            # L1 - Area (L² dimension)
            r"project\s+size": ("projectSizeAcres", "area_acres"),
            r"(unit|average)\s+size": ("unitSaleableSizeSqft", "area_sqft_per_unit"),

            # L2 Metrics - CHECK BEFORE generic patterns
            r"(total\s+)?revenue": ("totalRevenueCr", "currency_cr_l2"),
            r"npv|net\s+present\s+value": ("npvCr", "currency_cr_l2"),
            r"irr|internal\s+rate\s+of\s+return": ("irrPct", "percentage_l2"),
            r"roi|return\s+on\s+investment": ("roiPct", "percentage_l2"),
            r"payback\s+period": ("paybackPeriodYears", "duration_years_l2"),
            r"profitability\s+index": ("profitabilityIndex", "ratio_l2"),
            r"absorption\s+rate": ("absorptionRatePctPerYear", "percentage_per_year_l2"),

            # Project metadata - LESS SPECIFIC, check AFTER specific patterns
            r"(project\s+)?name": ("projectName", "text"),
            r"project\s+id": ("projectId", "text"),
            r"developer(\s+name)?": ("developerName", "text"),
            r"what\s+is\s+(the\s+)?(city|location)": ("location", "text"),  # More specific
            r"launch\s+date": ("launchDate", "date"),
            r"possession\s+date": ("possessionDate", "date"),
            r"rera": ("reraRegistered", "text"),
        }

    def _extract_project_name_from_question(self, question: str) -> Optional[str]:
        """
        Extract project name from question text

        Examples:
            "What is the sales velocity of 'The Urbana'?" -> "The Urbana"
            "How many units does Sara City have?" -> "Sara City"
            "What is the price of Gulmohar City" -> "Gulmohar City"
        """
        # Common project name patterns
        patterns = [
            r"(?:of|for|in)\s+['\"]([^'\"]+)['\"]",  # quoted names: "of 'The Urbana'"
            r"(?:of|for|in)\s+([A-Z][a-zA-Z\s]+?)(?:\?|$|have|has|is)",  # Capitalized names: "of Sara City?"
        ]

        for pattern in patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                project_name = match.group(1).strip()
                return project_name

        return None

    def _find_project_by_name(self, project_name: str) -> Optional[Dict]:
        """Find project by name (case-insensitive partial match)"""
        projects = data_service.get_all_projects()

        project_name_lower = project_name.lower()

        # First try exact match
        for project in projects:
            name = data_service.get_value(project.get('projectName', ''))
            if name and name.lower() == project_name_lower:
                return project

        # Then try partial match
        for project in projects:
            name = data_service.get_value(project.get('projectName', ''))
            if name and project_name_lower in name.lower():
                return project

        return None

    def answer_question(
        self,
        question: str,
        project: Optional[Dict] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer a basic question about a project from nested JSON

        Args:
            question: Question text (e.g., "How many units?", "What is location?", "What is total revenue?")
            project: Project dict (nested JSON format, optional)
            project_id: Project ID to look up (optional)

        Returns:
            Dictionary with answer, source layer, and metadata
        """
        # Get project if not provided
        if not project:
            if project_id:
                project = data_service.get_project(project_id)
                if not project:
                    return {
                        "answer": f"Project '{project_id}' not found",
                        "status": "error",
                        "question": question
                    }
            else:
                # Try to extract project name from question
                project_name_from_question = self._extract_project_name_from_question(question)

                if project_name_from_question:
                    # Find project by name
                    project = self._find_project_by_name(project_name_from_question)

                    if not project:
                        return {
                            "answer": f"Project '{project_name_from_question}' not found in knowledge graph",
                            "status": "error",
                            "question": question
                        }
                else:
                    # Try to get the first available project (for demo)
                    projects = data_service.get_all_projects()
                    if not projects:
                        return {
                            "answer": "No projects available",
                            "status": "error",
                            "question": question
                        }
                    project = projects[0]

        # Normalize question
        q_lower = question.lower().strip().rstrip("?!")

        # Check question patterns
        for pattern, (field_name, value_type) in self.question_patterns.items():
            if re.search(pattern, q_lower, re.IGNORECASE):
                # Determine layer and extract value
                if value_type.endswith("_l2"):
                    # L2 metric
                    value, unit, layer = self._extract_l2_metric(project, field_name)
                else:
                    # Metadata or L1 attribute
                    value, unit, layer = self._extract_field(project, field_name)

                if value is None:
                    answer = f"Information not available for {field_name}"
                else:
                    # Format answer
                    answer = self._format_answer(
                        field_name,
                        value,
                        unit,
                        value_type,
                        data_service.get_value(project.get('projectName'))
                    )

                return {
                    "answer": answer,
                    "status": "success",
                    "layer": layer,
                    "field": field_name,
                    "value": value,
                    "unit": unit,
                    "question": question,
                    "project": {
                        "projectId": str(data_service.get_value(project.get('projectId'))),
                        "projectName": data_service.get_value(project.get('projectName'))
                    }
                }

        # No match found
        return {
            "answer": f"I don't understand the question: '{question}'. Try asking about location, units, price, revenue, NPV, IRR, etc.",
            "status": "unmatched",
            "question": question,
            "project": {
                "projectId": str(data_service.get_value(project.get('projectId'))),
                "projectName": data_service.get_value(project.get('projectName'))
            }
        }

    def _extract_field(self, project: Dict, field_name: str) -> tuple:
        """
        Extract field from nested JSON project

        Returns:
            (value, unit, layer) tuple
        """
        # Check if it's a metadata field (non-nested)
        if field_name in project and not isinstance(project[field_name], dict):
            # Simple metadata field
            return (project[field_name], None, "Metadata")

        # Check if it's a nested field (L1 attribute)
        if field_name in project and isinstance(project[field_name], dict):
            field_data = project[field_name]
            value = data_service.get_value(field_data)
            unit = data_service.get_unit(field_data)
            return (value, unit, "L1 (Attributes)")

        # Not found
        return (None, None, None)

    def _extract_l2_metric(self, project: Dict, metric_name: str) -> tuple:
        """
        Extract L2 metric from nested JSON project

        Returns:
            (value, unit, layer) tuple
        """
        l2_metrics = project.get('l2_metrics', {})
        if metric_name in l2_metrics and isinstance(l2_metrics[metric_name], dict):
            metric_data = l2_metrics[metric_name]
            value = data_service.get_value(metric_data)
            unit = data_service.get_unit(metric_data)
            return (value, unit, "L2 (Calculated Metrics)")

        # Not found
        return (None, None, None)

    def _format_answer(
        self,
        field_name: str,
        value: Any,
        unit: Optional[str],
        value_type: str,
        project_name: str
    ) -> str:
        """Format answer in natural language"""

        # Handle different value types
        if value_type == "text":
            return f"{value}"

        elif value_type == "date":
            return f"{value}"

        elif value_type == "units":
            # Integer units (no decimal)
            return f"{int(value):,}"

        elif value_type == "area_acres":
            # Area in acres
            if isinstance(value, int):
                return f"{value:,} acres"
            else:
                return f"{value:,.2f} acres"

        elif value_type == "area_sqft_per_unit":
            # Area per unit
            if isinstance(value, int):
                return f"{value:,} sqft/unit"
            else:
                return f"{value:,.2f} sqft/unit"

        elif value_type == "price_psf":
            # Price per sqft (C/L²)
            if isinstance(value, int):
                return f"₹{value:,}/sqft"
            else:
                return f"₹{value:,.2f}/sqft"

        elif value_type == "currency_cr":
            # Currency in crores (L1)
            if isinstance(value, int):
                return f"₹{value:,} Crore"
            else:
                return f"₹{value:,.2f} Crore"

        elif value_type == "currency_cr_l2":
            # Currency in crores (L2)
            if isinstance(value, int):
                return f"₹{value:,} Crore"
            else:
                return f"₹{value:,.2f} Crore"

        elif value_type == "percentage":
            # Percentage (no decimal if integer)
            if isinstance(value, int):
                return f"{value}%"
            else:
                return f"{value:.2f}%"

        elif value_type == "percentage_per_month":
            # Percentage per month
            if isinstance(value, int):
                return f"{value}%/month"
            else:
                return f"{value:.2f}%/month"

        elif value_type == "percentage_l2":
            # L2 percentage
            if isinstance(value, int):
                return f"{value}%"
            else:
                return f"{value:.2f}%"

        elif value_type == "percentage_per_year_l2":
            # L2 percentage per year
            if isinstance(value, int):
                return f"{value}%/year"
            else:
                return f"{value:.2f}%/year"

        elif value_type == "duration_years_l2":
            # Duration in years (L2)
            if isinstance(value, int):
                return f"{value} years"
            else:
                return f"{value:.2f} years"

        elif value_type == "ratio_l2":
            # Ratio (L2)
            if isinstance(value, int):
                return f"{value}"
            else:
                return f"{value:.2f}"

        else:
            # Default formatting with unit
            if unit:
                return f"{value} {unit}"
            else:
                return f"{value}"


# Singleton instance
_qa_service_instance: Optional[QAService] = None

def get_qa_service() -> QAService:
    """Get or create QAService singleton instance"""
    global _qa_service_instance
    if _qa_service_instance is None:
        _qa_service_instance = QAService()
    return _qa_service_instance
