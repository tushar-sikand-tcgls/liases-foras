"""
Simple Query Handler - Direct approach without complex LLM processing
Handles basic queries with pattern matching first, falls back to LLM if needed
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
import re
from app.services.semantic_query_matcher import SemanticQueryMatcher


@dataclass
class QueryResult:
    """Structured query result"""
    status: str
    layer: int
    dimension: str
    operation: str
    result: Dict
    calculation: Optional[Dict] = None
    provenance: Optional[Dict] = None


class SimpleQueryHandler:
    """
    Simple pattern-based query handler for common questions

    Handles:
    - "Calculate average of project size(s)" → Layer 0, U dimension, mean aggregation
    - "What is the PSF?" → Layer 1, CF/L² dimension, division
    - "Top N by X" → Filter operation
    """

    def __init__(self, data_service):
        """
        Args:
            data_service: DataService instance with access to project data
        """
        self.data_service = data_service
        self.semantic_matcher = SemanticQueryMatcher()

    def handle_query(self, query: str) -> QueryResult:
        """
        Handle query with SEMANTIC matching (NOT hardcoded keywords)

        Uses vector/string similarity to match queries flexibly.
        Handles variations: "calculate", "compute", "provide", "generate", "derive", etc.

        Priority:
        1. Check if query contains a specific project name (override pattern matching)
        2. Use semantic matcher to find best pattern match
        3. Route to appropriate handler based on match
        4. Return error if no match above threshold
        """

        # PRIORITY CHECK: If query contains a specific project name, route to specific_project handler
        # This prevents misrouting queries like "Sara City project size" to "average_project_size"
        project_name = self._extract_project_name(query)
        if project_name:
            # Query mentions a specific project - route directly to retrieval (bypass pattern matching)
            return self._get_specific_project(project_name, query=query)

        # Use semantic matching to find best pattern
        match = self.semantic_matcher.best_match(query)

        if not match:
            # No pattern matched above similarity threshold
            return QueryResult(
                status="error",
                layer=0,
                dimension="",
                operation="",
                result={"error": "Query pattern not recognized. Try: 'Calculate average project size' or 'What is the PSF?'"}
            )

        # Route to handler based on semantic match
        handler_name = match['handler']

        if handler_name == "get_specific_project":
            # Extract project name from query
            project_name = self._extract_project_name(query)
            return self._get_specific_project(project_name, query=query)

        elif handler_name == "calculate_average_project_size":
            return self._calculate_average_project_size()

        elif handler_name == "calculate_psf":
            return self._calculate_psf()

        elif handler_name == "calculate_asp":
            return self._calculate_asp()

        elif handler_name == "get_top_n":
            # Extract N and field from query
            n = self.semantic_matcher.extract_number_from_top_n(query) or 5
            field = self.semantic_matcher.extract_field_from_top_n(query) or 'revenue'
            return self._get_top_n_projects(n, field)

        elif handler_name == "calculate_total":
            # Extract field name from query (e.g., "annual sales" → "annualSalesUnits")
            field = self.semantic_matcher.extract_field_from_total_query(query)
            return self._calculate_total(field)

        elif handler_name == "calculate_standard_deviation":
            # Calculate standard deviation of project sizes (default field: projectSizeUnits)
            field = 'projectSizeUnits'  # Default to project size
            return self._calculate_standard_deviation(field)

        # Fallback (should not reach here if patterns are defined correctly)
        return QueryResult(
            status="error",
            layer=0,
            dimension="",
            operation="",
            result={"error": f"Handler '{handler_name}' not implemented"}
        )

    # OLD regex-based methods removed - now using SemanticQueryMatcher instead!

    def _calculate_average_project_size(self) -> QueryResult:
        """
        Calculate average project size (Layer 0, Dimension U)

        Formula: X = Σ(projectSizeUnits) / count(projects)

        Note: Uses projectSizeUnits (NOT totalSupplyUnits) for Project Size calculations
        """
        projects = self.data_service.get_all_projects()

        # Extract projectSizeUnits for each project
        units_values = []
        project_details = []

        for project in projects:
            units = self.data_service.get_value(project.get('projectSizeUnits'))
            project_name = self.data_service.get_value(project.get('projectName'))

            if units is not None and isinstance(units, (int, float)):
                units_values.append(units)
                project_details.append({
                    'projectName': project_name or 'Unknown',
                    'value': units
                })

        if not units_values:
            return QueryResult(
                status="error",
                layer=0,
                dimension="U",
                operation="AGGREGATION",
                result={"error": "No project size data available"}
            )

        # Calculate average
        total = sum(units_values)
        count = len(units_values)
        average = total / count

        return QueryResult(
            status="success",
            layer=0,
            dimension="U",
            operation="AGGREGATION",
            result={
                "value": round(average, 1),
                "unit": "Units",
                "text": f"{round(average, 1)} Units"
            },
            calculation={
                "formula": f"X = Σ U / {count}",
                "breakdown": project_details,
                "projectCount": count,
                "total": total,
                "scope_note": f"⚠️ Based on {count} projects (limited dataset). This is NOT the average for the entire region, only the top projects in the current dataset."
            },
            provenance={
                "dataSource": "Liases Foras",
                "layer": "Layer 0",
                "targetAttribute": "Project Size (projectSizeUnits)",
                "operation": "mean",
                "scope": f"Top {count} projects only (not entire region)"
            }
        )

    def _calculate_psf(self) -> QueryResult:
        """
        Calculate PSF (Price Per Sqft) - Layer 1, Dimension C/L²

        Formula: PSF = totalRevenue / totalSaleableArea
        """
        projects = self.data_service.get_all_projects()

        psf_values = []
        project_details = []

        for project in projects:
            # Try to get pre-calculated PSF first
            current_psf = self.data_service.get_value(project.get('currentPricePSF'))
            project_name = self.data_service.get_value(project.get('projectName'))

            if current_psf is not None and isinstance(current_psf, (int, float)):
                psf_values.append(current_psf)
                project_details.append({
                    'projectName': project_name or 'Unknown',
                    'value': current_psf
                })

        if not psf_values:
            return QueryResult(
                status="error",
                layer=1,
                dimension="C/L²",
                operation="DIVISION",
                result={"error": "No PSF data available"}
            )

        # Calculate average PSF
        average_psf = sum(psf_values) / len(psf_values)

        return QueryResult(
            status="success",
            layer=1,
            dimension="C/L²",
            operation="DIVISION",
            result={
                "value": round(average_psf, 2),
                "unit": "INR/sqft",
                "text": f"₹{round(average_psf, 2)}/sqft"
            },
            calculation={
                "formula": "PSF = C ÷ L²",
                "breakdown": project_details,
                "projectCount": len(psf_values),
                "scope_note": f"⚠️ Average of {len(psf_values)} projects (limited dataset). This is NOT the average PSF for the entire region, only the top projects in the current dataset."
            },
            provenance={
                "dataSource": "Liases Foras",
                "layer": "Layer 1",
                "dimension": "C/L² (Cash per Area)",
                "operation": "division",
                "scope": f"Top {len(psf_values)} projects only (not entire region)"
            }
        )

    def _calculate_asp(self) -> QueryResult:
        """Calculate ASP (Average Selling Price) - Layer 1, Dimension C/U"""
        # Similar to PSF but for units
        # Implementation would follow same pattern
        return QueryResult(
            status="success",
            layer=1,
            dimension="C/U",
            operation="DIVISION",
            result={"value": 0, "unit": "INR/unit", "text": "Not implemented yet"}
        )

    def _get_top_n_projects(self, n: int, field: str) -> QueryResult:
        """Get top N projects by specified field"""
        projects = self.data_service.get_all_projects()

        # Map query field to actual data field
        field_mapping = {
            'revenue': 'totalRevenueCr',
            'size': 'projectSizeUnits',  # Project Size = projectSizeUnits (NOT totalSupplyUnits)
            'units': 'projectSizeUnits',  # Project Size = projectSizeUnits (NOT totalSupplyUnits)
            'area': 'projectSizeAcres',
        }

        data_field = field_mapping.get(field, field)

        # Extract and sort
        project_list = []
        for project in projects:
            value = self.data_service.get_value(project.get(data_field))
            project_name = self.data_service.get_value(project.get('projectName'))

            if value is not None and isinstance(value, (int, float)):
                project_list.append({
                    'projectName': project_name or 'Unknown',
                    'value': value
                })

        # Sort descending and take top N
        sorted_projects = sorted(project_list, key=lambda x: x['value'], reverse=True)
        top_n_results = sorted_projects[:n]

        return QueryResult(
            status="success",
            layer=0,
            dimension="",
            operation="FILTER",
            result={
                "type": "table",
                "rows": top_n_results,
                "count": len(top_n_results)
            },
            provenance={
                "dataSource": "Liases Foras",
                "operation": f"top_{n}",
                "field": data_field
            }
        )

    def _calculate_total(self, field: str = 'projectSizeUnits') -> QueryResult:
        """
        Calculate total/sum for specified field

        Args:
            field: Field name to sum (projectSizeUnits, annualSalesUnits, totalRevenueCr, etc.)

        Returns:
            QueryResult with sum of specified field across all projects
        """
        projects = self.data_service.get_all_projects()

        # Field metadata: dimension, unit, display name
        field_metadata = {
            'projectSizeUnits': {
                'dimension': 'U',
                'unit': 'Units',
                'display_name': 'Project Size',
                'formula_symbol': 'U'
            },
            'totalSupplyUnits': {
                'dimension': 'U',
                'unit': 'Units',
                'display_name': 'Total Supply Units',
                'formula_symbol': 'U'
            },
            'annualSalesUnits': {
                'dimension': 'U/T',  # Units per Year
                'unit': 'Units/Year',
                'display_name': 'Annual Sales',
                'formula_symbol': 'U/T'
            },
            'annualSalesValueCr': {
                'dimension': 'C/T',  # Cash per Year (using C not CF!)
                'unit': 'INR Cr/Year',
                'display_name': 'Annual Revenue',
                'formula_symbol': 'C/T'
            },
            'totalRevenueCr': {
                'dimension': 'C',  # Cash (using C not CF!)
                'unit': 'INR Cr',
                'display_name': 'Total Revenue',
                'formula_symbol': 'C'
            },
            'projectSizeAcres': {
                'dimension': 'L²',
                'unit': 'Acres',
                'display_name': 'Project Area',
                'formula_symbol': 'L²'
            }
        }

        metadata = field_metadata.get(field, {
            'dimension': 'Unknown',
            'unit': 'Unknown',
            'display_name': field,
            'formula_symbol': '?'
        })

        # Calculate sum
        total_value = 0
        project_details = []

        for project in projects:
            value = self.data_service.get_value(project.get(field))
            project_name = self.data_service.get_value(project.get('projectName'))

            if value is not None and isinstance(value, (int, float)):
                total_value += value
                project_details.append({
                    'projectName': project_name or 'Unknown',
                    'value': value
                })

        if not project_details:
            return QueryResult(
                status="error",
                layer=0,
                dimension=metadata['dimension'],
                operation="AGGREGATION",
                result={"error": f"No data available for {field}"}
            )

        # Format value based on type
        formatted_value = round(total_value, 2) if isinstance(total_value, float) else total_value

        return QueryResult(
            status="success",
            layer=0,  # Aggregation stays at same layer as input
            dimension=metadata['dimension'],
            operation="AGGREGATION",
            result={
                "value": formatted_value,
                "unit": metadata['unit'],
                "text": f"{formatted_value} {metadata['unit']}"
            },
            calculation={
                "formula": f"Σ {metadata['formula_symbol']}",
                "breakdown": project_details,
                "projectCount": len(project_details),
                "field": field,
                "total": formatted_value,
                "scope_note": f"⚠️ Sum of {len(project_details)} projects (limited dataset). This is NOT the total for the entire region, only the top projects in the current dataset."
            },
            provenance={
                "dataSource": "Liases Foras",
                "layer": "Layer 0",
                "targetAttribute": metadata['display_name'],
                "operation": "sum",
                "field": field,
                "scope": f"Top {len(project_details)} projects only (not entire region)"
            }
        )

    def _calculate_standard_deviation(self, field: str = 'projectSizeUnits') -> QueryResult:
        """
        Calculate standard deviation for specified field

        Uses sample standard deviation formula: s = sqrt(Σ(Xi - X̄)² / (n-1))

        Args:
            field: Field name for calculation (projectSizeUnits, totalRevenueCr, etc.)

        Returns:
            QueryResult with standard deviation value
        """
        import math

        projects = self.data_service.get_all_projects()

        # Field metadata
        field_metadata = {
            'projectSizeUnits': {
                'dimension': 'U',
                'unit': 'Units',
                'display_name': 'Project Size',
                'formula_symbol': 'σ(U)'
            },
            'totalSupplyUnits': {
                'dimension': 'U',
                'unit': 'Units',
                'display_name': 'Total Supply Units',
                'formula_symbol': 'σ(U)'
            },
            'totalRevenueCr': {
                'dimension': 'C',
                'unit': 'INR Cr',
                'display_name': 'Total Revenue',
                'formula_symbol': 'σ(C)'
            },
            'projectSizeAcres': {
                'dimension': 'L²',
                'unit': 'Acres',
                'display_name': 'Project Area',
                'formula_symbol': 'σ(L²)'
            }
        }

        metadata = field_metadata.get(field, {
            'dimension': 'Unknown',
            'unit': 'Unknown',
            'display_name': field,
            'formula_symbol': 'σ(?)'
        })

        # Extract values
        values = []
        project_details = []

        for project in projects:
            value = self.data_service.get_value(project.get(field))
            project_name = self.data_service.get_value(project.get('projectName'))

            if value is not None and isinstance(value, (int, float)):
                values.append(value)
                project_details.append({
                    'projectName': project_name or 'Unknown',
                    'value': value
                })

        if len(values) < 2:
            return QueryResult(
                status="error",
                layer=0,
                dimension=metadata['dimension'],
                operation="AGGREGATION",
                result={"error": f"Need at least 2 data points to calculate standard deviation for {field}"}
            )

        # Calculate mean
        n = len(values)
        mean = sum(values) / n

        # Calculate variance (sample variance with n-1)
        squared_diffs = [(x - mean) ** 2 for x in values]
        variance = sum(squared_diffs) / (n - 1)  # Bessel's correction for sample std dev

        # Standard deviation
        std_dev = math.sqrt(variance)

        # Format value
        formatted_std_dev = round(std_dev, 2)

        return QueryResult(
            status="success",
            layer=0,
            dimension=metadata['dimension'],
            operation="AGGREGATION",
            result={
                "value": formatted_std_dev,
                "unit": metadata['unit'],
                "text": f"{formatted_std_dev} {metadata['unit']}"
            },
            calculation={
                "formula": f"s = √[Σ(Xi - X̄)² / (n-1)]",
                "breakdown": project_details,
                "projectCount": n,
                "mean": round(mean, 2),
                "variance": round(variance, 2),
                "stdDev": formatted_std_dev,
                "field": field,
                "scope_note": f"⚠️ Based on {n} projects (limited dataset). This is NOT the standard deviation for the entire region, only the top projects in the current dataset."
            },
            provenance={
                "dataSource": "Liases Foras",
                "layer": "Layer 0",
                "targetAttribute": metadata['display_name'],
                "operation": "standard_deviation",
                "field": field,
                "note": "Sample standard deviation (Bessel's correction applied)",
                "scope": f"Top {n} projects only (not entire region)"
            }
        )

    def _extract_project_name(self, query: str) -> str:
        """
        Extract project name from query using multiple strategies.

        Strategies:
        1. Check for "of [name]" pattern
        2. Check for "[name] project" pattern
        3. Match against known project names

        Args:
            query: User query

        Returns:
            Extracted project name or empty string
        """
        query_lower = query.lower()

        # Strategy 1: "of [project name]" pattern
        of_match = re.search(r'\bof\s+([a-zA-Z\s]+?)(?:\s*$|\s+project|\?)', query, re.IGNORECASE)
        if of_match:
            potential_name = of_match.group(1).strip()
            # Verify this is a real project
            project = self.data_service.get_project_by_name(potential_name)
            if project:
                return potential_name

        # Strategy 2: Check against all known project names
        all_projects = self.data_service.get_all_projects()
        for project in all_projects:
            project_name = self.data_service.get_value(project.get('projectName', ''))
            if project_name and project_name.lower() in query_lower:
                return project_name

        # Strategy 3: Extract capitalized words (likely project names)
        words = query.split()
        for i, word in enumerate(words):
            # Check 2-word combinations (e.g., "Sara City")
            if i < len(words) - 1:
                two_word = f"{word} {words[i+1]}"
                project = self.data_service.get_project_by_name(two_word)
                if project:
                    return two_word
            # Check single words
            project = self.data_service.get_project_by_name(word)
            if project:
                return word

        return ""

    def _get_specific_project(self, project_name: str, query: str = "") -> QueryResult:
        """
        Get specific project's data (Layer 0 retrieval).

        Returns all Layer 0 dimensions for the specified project.

        Args:
            project_name: Name of the project
            query: Original query (to determine which dimension to prioritize)

        Returns:
            QueryResult with project dimensions
        """
        if not project_name:
            return QueryResult(
                status="error",
                layer=0,
                dimension="U",
                operation="RETRIEVAL",
                result={"error": "Could not identify project name in query. Please specify the project name."}
            )

        # Find project
        project = self.data_service.get_project_by_name(project_name)

        if not project:
            return QueryResult(
                status="error",
                layer=0,
                dimension="U",
                operation="RETRIEVAL",
                result={"error": f"Project '{project_name}' not found in database"}
            )

        # Extract Layer 0 dimensions
        project_size_units = self.data_service.get_value(project.get('projectSizeUnits'))  # U dimension (actual project size)
        project_size_acres = self.data_service.get_value(project.get('projectSizeAcres'))  # L² dimension
        total_units = self.data_service.get_value(project.get('totalSupplyUnits'))  # U dimension

        # Sold/Unsold: Get percentages (since *Units columns don't exist)
        sold_pct = self.data_service.get_value(project.get('soldPct'))  # Dimensionless
        unsold_pct = self.data_service.get_value(project.get('unsoldPct'))  # Dimensionless

        # Calculate sold/unsold units from percentage if needed
        sold_units = None
        unsold_units = None
        if project_size_units and sold_pct is not None:
            sold_units = round(project_size_units * (sold_pct / 100))
        if project_size_units and unsold_pct is not None:
            unsold_units = round(project_size_units * (unsold_pct / 100))

        saleable_area = self.data_service.get_value(project.get('saleableAreaSqft'))
        unit_saleable_size = self.data_service.get_value(project.get('unitSaleableSizeSqft'))
        current_price_psf = self.data_service.get_value(project.get('currentPricePSF'))

        # Build result
        result_data = {
            "project_name": project_name,
            "dimensions": {}
        }

        # Determine primary dimension based on query context
        query_lower = query.lower()
        primary_dimension = None
        primary_value = None
        primary_unit = None
        primary_dim_label = None

        # Check what the query is asking for
        if "unsold" in query_lower:
            # Query asks for unsold: check if they want percentage or units
            if "percent" in query_lower or "%" in query_lower:
                # They want percentage (dimensionless)
                if unsold_pct is not None:
                    primary_value = unsold_pct
                    primary_unit = "%"
                    primary_dimension = "Dimensionless"
                    primary_dim_label = "unsold_percentage"
            else:
                # They want units (U dimension) - use calculated unsold units
                if unsold_units is not None:
                    primary_value = unsold_units
                    primary_unit = "Units"
                    primary_dimension = "U"
                    primary_dim_label = "unsold_units"
                elif unsold_pct is not None:
                    # Fallback: return percentage if units not calculable
                    primary_value = unsold_pct
                    primary_unit = "%"
                    primary_dimension = "Dimensionless"
                    primary_dim_label = "unsold_percentage"
        elif "sold" in query_lower and "unsold" not in query_lower:
            # Query asks for sold (not unsold): check if they want percentage or units
            if "percent" in query_lower or "%" in query_lower:
                # They want percentage (dimensionless)
                if sold_pct is not None:
                    primary_value = sold_pct
                    primary_unit = "%"
                    primary_dimension = "Dimensionless"
                    primary_dim_label = "sold_percentage"
            else:
                # They want units (U dimension) - use calculated sold units
                if sold_units is not None:
                    primary_value = sold_units
                    primary_unit = "Units"
                    primary_dimension = "U"
                    primary_dim_label = "sold_units"
                elif sold_pct is not None:
                    # Fallback: return percentage if units not calculable
                    primary_value = sold_pct
                    primary_unit = "%"
                    primary_dimension = "Dimensionless"
                    primary_dim_label = "sold_percentage"
        elif "project size" in query_lower or "size of" in query_lower:
            # "Project size" typically means project size in units (U dimension)
            if project_size_units is not None:
                primary_value = project_size_units
                primary_unit = "Units"
                primary_dimension = "U"
                primary_dim_label = "project_size"
        elif "total units" in query_lower or "how many units" in query_lower or "number of units" in query_lower:
            # Explicitly asking for unit count
            if total_units is not None:
                primary_value = total_units
                primary_unit = "Units"
                primary_dimension = "U"
                primary_dim_label = "total_units"
        else:
            # Default: return project size if available, otherwise total units
            if project_size_units is not None:
                primary_value = project_size_units
                primary_unit = "Units"
                primary_dimension = "U"
                primary_dim_label = "project_size"
            elif total_units is not None:
                primary_value = total_units
                primary_unit = "Units"
                primary_dimension = "U"
                primary_dim_label = "total_units"

        # Set primary answer
        if primary_value is not None:
            result_data["value"] = primary_value
            result_data["unit"] = primary_unit
            result_data["text"] = f"{primary_value} {primary_unit}"

        # Add all available dimensions to the result
        if project_size_units is not None:
            result_data["dimensions"]["project_size"] = {
                "value": project_size_units,
                "unit": "Units",
                "dimension": "L²",
                "description": "Project size (land area)"
            }

        if project_size_acres is not None:
            result_data["dimensions"]["project_size_acres"] = {
                "value": project_size_acres,
                "unit": "Acres",
                "dimension": "L²",
                "description": "Project size in acres"
            }

        if total_units is not None:
            result_data["dimensions"]["total_units"] = {
                "value": total_units,
                "unit": "Units",
                "dimension": "U",
                "description": "Total supply units"
            }

        if sold_units is not None:
            result_data["dimensions"]["sold_units"] = {
                "value": sold_units,
                "unit": "Units",
                "dimension": "U",
                "description": "Units sold"
            }

        if unsold_units is not None:
            result_data["dimensions"]["unsold_units"] = {
                "value": unsold_units,
                "unit": "Units",
                "dimension": "U",
                "description": "Units unsold"
            }

        if saleable_area is not None:
            result_data["dimensions"]["saleable_area"] = {
                "value": saleable_area,
                "unit": "sqft",
                "dimension": "L²",
                "description": "Total saleable area"
            }

        if unit_saleable_size is not None:
            result_data["dimensions"]["unit_saleable_size"] = {
                "value": unit_saleable_size,
                "unit": "sqft",
                "dimension": "L²",
                "description": "Average unit size"
            }

        if current_price_psf is not None:
            result_data["dimensions"]["current_price_psf"] = {
                "value": current_price_psf,
                "unit": "INR/sqft",
                "dimension": "CF/L²",
                "description": "Current price per sqft"
            }

        return QueryResult(
            status="success",
            layer=0,
            dimension=primary_dimension or "U",
            operation="RETRIEVAL",
            result=result_data,
            calculation={
                "formula": "Direct retrieval from Knowledge Graph (Layer 0)",
                "source": f"Layer 0 dimension: {primary_dim_label or 'project data'}"
            },
            provenance={
                "dataSource": "Liases Foras",
                "layer": "Layer 0",
                "targetAttribute": f"Project Dimensions ({primary_dim_label or 'all dimensions'})",
                "operation": "retrieval",
                "project": project_name
            }
        )


# FastAPI endpoint integration
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()


class SimpleQueryRequest(BaseModel):
    query: str


@router.post("/api/query/simple")
async def simple_query_handler(request: SimpleQueryRequest):
    """
    Simple pattern-based query handler

    Fast and accurate for common questions:
    - "Calculate average of project sizes"
    - "What is the PSF?"
    - "Top 5 projects by revenue"

    Falls back to unified processor for complex queries.
    """
    from app.services.data_service import data_service

    handler = SimpleQueryHandler(data_service)
    result = handler.handle_query(request.query)

    if result.status == "success":
        return {
            "status": "success",
            "query": request.query,
            "understanding": {
                "layer": result.layer,
                "dimension": result.dimension,
                "operation": result.operation
            },
            "result": result.result,
            "calculation": result.calculation,
            "provenance": result.provenance
        }
    else:
        return {
            "status": "error",
            "query": request.query,
            "error": result.result.get("error")
        }
