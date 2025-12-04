"""
Function Registry: Centralized catalog of all available functions for LLM routing

Provides Gemini-compatible function schemas for native function calling.
Maps function names to execution handlers across all layers.
"""

from typing import Dict, List, Any, Callable, Optional
from app.calculators.layer1 import Layer1Calculator
from app.calculators.layer2 import Layer2Calculator
from app.calculators.layer3 import Layer3Optimizer
from app.services.vector_db_service import VectorDBService
from app.services.context_service import ContextService
from app.services.data_service import data_service  # Import singleton instance
from app.services.statistical_service import StatisticalService
from app.models.domain import FinancialProjection


class FunctionRegistry:
    """
    Centralized registry of all available functions for LLM-driven routing

    Provides:
    - Gemini-compatible function schemas (for function calling)
    - Execution handlers for each function
    - Layer/category organization
    """

    def __init__(self):
        """Initialize function registry with all available functions"""
        self.data_service = data_service  # Use singleton instance
        self.vector_db = VectorDBService()
        self.context_service = ContextService()
        self.statistical_service = StatisticalService()

        # Function catalog organized by layer
        self._functions: Dict[str, Dict[str, Any]] = {}
        self._register_all_functions()

    def _register_all_functions(self):
        """Register all available functions across all layers"""
        # Layer 0: Raw Dimensions
        self._register_layer0_functions()

        # Layer 1: Derived Metrics
        self._register_layer1_functions()

        # Layer 2: Financial Metrics
        self._register_layer2_functions()

        # Layer 3: Optimization
        self._register_layer3_functions()

        # Layer 4: GraphRAG & Semantic Search
        self._register_layer4_functions()

        # Context & Enrichment Functions
        self._register_context_functions()

        # Data Retrieval Functions
        self._register_data_functions()

    # ==================== LAYER 0 FUNCTIONS ====================

    def _register_layer0_functions(self):
        """Register Layer 0 functions: Raw dimensions (U, L², T, CF)"""

        self._functions["get_project_dimensions"] = {
            "schema": {
                "name": "get_project_dimensions",
                "description": "Get raw dimensional data for a project (Units, Area, Time, Cash Flow). Returns Layer 0 atomic dimensions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "integer",
                            "description": "Project ID (1-3 for current dataset)"
                        }
                    },
                    "required": ["project_id"]
                }
            },
            "handler": self._handle_get_project_dimensions,
            "layer": 0,
            "category": "data_retrieval"
        }

        self._functions["get_project_by_name"] = {
            "schema": {
                "name": "get_project_by_name",
                "description": "Get project data by project name. Use this to find project ID from name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_name": {
                            "type": "string",
                            "description": "Name of the project (e.g., 'Sara City', 'VTP Pegasus', 'Megapolis Smart Homes 1')"
                        }
                    },
                    "required": ["project_name"]
                }
            },
            "handler": self._handle_get_project_by_name,
            "layer": 0,
            "category": "data_retrieval"
        }

    # ==================== LAYER 1 FUNCTIONS ====================

    def _register_layer1_functions(self):
        """Register Layer 1 functions: Derived metrics (PSF, ASP, Absorption, Velocity)"""

        self._functions["calculate_psf"] = {
            "schema": {
                "name": "calculate_psf",
                "description": "Calculate Price Per Square Foot (PSF = Revenue / Area). Dimension: C/L²",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "total_revenue": {
                            "type": "number",
                            "description": "Total revenue in INR"
                        },
                        "saleable_area": {
                            "type": "number",
                            "description": "Total saleable area in square feet"
                        }
                    },
                    "required": ["total_revenue", "saleable_area"]
                }
            },
            "handler": lambda params: Layer1Calculator.calculate_psf(**params),
            "layer": 1,
            "category": "calculator"
        }

        self._functions["calculate_asp"] = {
            "schema": {
                "name": "calculate_asp",
                "description": "Calculate Average Selling Price (ASP = Revenue / Units). Dimension: C/U",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "total_revenue": {
                            "type": "number",
                            "description": "Total revenue in INR"
                        },
                        "total_units": {
                            "type": "integer",
                            "description": "Total number of units"
                        }
                    },
                    "required": ["total_revenue", "total_units"]
                }
            },
            "handler": lambda params: Layer1Calculator.calculate_asp(**params),
            "layer": 1,
            "category": "calculator"
        }

        self._functions["calculate_absorption_rate"] = {
            "schema": {
                "name": "calculate_absorption_rate",
                "description": "Calculate Absorption Rate (% units sold per month). Dimension: (U/U_total)/T",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "units_sold": {
                            "type": "integer",
                            "description": "Number of units sold"
                        },
                        "total_units": {
                            "type": "integer",
                            "description": "Total number of units"
                        },
                        "months_elapsed": {
                            "type": "integer",
                            "description": "Number of months elapsed"
                        }
                    },
                    "required": ["units_sold", "total_units", "months_elapsed"]
                }
            },
            "handler": lambda params: Layer1Calculator.calculate_absorption_rate(**params),
            "layer": 1,
            "category": "calculator"
        }

        self._functions["calculate_sales_velocity"] = {
            "schema": {
                "name": "calculate_sales_velocity",
                "description": "Calculate Sales Velocity (units sold per month). Dimension: U/T",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "units_sold": {
                            "type": "integer",
                            "description": "Number of units sold"
                        },
                        "months_elapsed": {
                            "type": "integer",
                            "description": "Number of months elapsed"
                        }
                    },
                    "required": ["units_sold", "months_elapsed"]
                }
            },
            "handler": lambda params: Layer1Calculator.calculate_sales_velocity(**params),
            "layer": 1,
            "category": "calculator"
        }

        self._functions["calculate_density"] = {
            "schema": {
                "name": "calculate_density",
                "description": "Calculate project density (units per sqft of land). Dimension: U/L²",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "total_units": {
                            "type": "integer",
                            "description": "Total number of units"
                        },
                        "land_area": {
                            "type": "number",
                            "description": "Land area in square feet"
                        }
                    },
                    "required": ["total_units", "land_area"]
                }
            },
            "handler": lambda params: Layer1Calculator.calculate_density(**params),
            "layer": 1,
            "category": "calculator"
        }

    # ==================== LAYER 2 FUNCTIONS ====================

    def _register_layer2_functions(self):
        """Register Layer 2 functions: Financial metrics (NPV, IRR, Payback)"""

        self._functions["calculate_npv"] = {
            "schema": {
                "name": "calculate_npv",
                "description": "Calculate Net Present Value (NPV) of a project given cash flows and discount rate",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "initial_investment": {
                            "type": "number",
                            "description": "Initial investment in INR"
                        },
                        "annual_cash_flows": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "List of annual cash flows in INR (e.g., [12.5, 15, 17.5, 20, 22.5] for 5 years)"
                        },
                        "discount_rate": {
                            "type": "number",
                            "description": "Discount rate as decimal (e.g., 0.12 for 12%)"
                        }
                    },
                    "required": ["initial_investment", "annual_cash_flows", "discount_rate"]
                }
            },
            "handler": self._handle_calculate_npv,
            "layer": 2,
            "category": "calculator"
        }

        self._functions["calculate_irr"] = {
            "schema": {
                "name": "calculate_irr",
                "description": "Calculate Internal Rate of Return (IRR) using Newton's method. Returns the rate where NPV = 0.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "initial_investment": {
                            "type": "number",
                            "description": "Initial investment in INR"
                        },
                        "annual_cash_flows": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "List of annual cash flows in INR"
                        }
                    },
                    "required": ["initial_investment", "annual_cash_flows"]
                }
            },
            "handler": self._handle_calculate_irr,
            "layer": 2,
            "category": "calculator"
        }

        self._functions["calculate_payback_period"] = {
            "schema": {
                "name": "calculate_payback_period",
                "description": "Calculate payback period (time to recover initial investment)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "initial_investment": {
                            "type": "number",
                            "description": "Initial investment in INR"
                        },
                        "annual_cash_flows": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "List of annual cash flows in INR"
                        }
                    },
                    "required": ["initial_investment", "annual_cash_flows"]
                }
            },
            "handler": self._handle_calculate_payback_period,
            "layer": 2,
            "category": "calculator"
        }

        self._functions["calculate_statistics"] = {
            "schema": {
                "name": "calculate_statistics",
                "description": "Calculate statistical metrics (avg, min, max, std, median) for a set of projects or metrics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric_name": {
                            "type": "string",
                            "description": "Name of the metric to analyze (e.g., 'currentPricePSF', 'totalUnits', 'landAreaAcres')"
                        },
                        "location": {
                            "type": "string",
                            "description": "Optional location filter (city, region, or micromarket)"
                        }
                    },
                    "required": ["metric_name"]
                }
            },
            "handler": self._handle_calculate_statistics,
            "layer": 2,
            "category": "calculator"
        }

        self._functions["get_top_n_projects"] = {
            "schema": {
                "name": "get_top_n_projects",
                "description": "Get top N projects ranked by a specific metric (e.g., top 3 by PSF, top 5 by land area)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric_name": {
                            "type": "string",
                            "description": "Metric to rank by (e.g., 'currentPricePSF', 'totalUnits', 'landAreaAcres')"
                        },
                        "n": {
                            "type": "integer",
                            "description": "Number of top projects to return (default: 5)"
                        },
                        "location": {
                            "type": "string",
                            "description": "Optional location filter"
                        },
                        "order": {
                            "type": "string",
                            "enum": ["desc", "asc"],
                            "description": "Sort order: 'desc' for highest first (default), 'asc' for lowest first"
                        }
                    },
                    "required": ["metric_name"]
                }
            },
            "handler": self._handle_get_top_n_projects,
            "layer": 2,
            "category": "data_retrieval"
        }

    # ==================== LAYER 3 FUNCTIONS ====================

    def _register_layer3_functions(self):
        """Register Layer 3 functions: Optimization & scenario planning"""

        self._functions["optimize_product_mix"] = {
            "schema": {
                "name": "optimize_product_mix",
                "description": "Optimize unit mix (1BHK/2BHK/3BHK) to maximize IRR using SLSQP optimization. Returns optimal mix and scenarios.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "total_units": {
                            "type": "integer",
                            "description": "Total number of units to distribute"
                        },
                        "total_land_area_sqft": {
                            "type": "number",
                            "description": "Total land area in square feet"
                        },
                        "total_project_cost": {
                            "type": "number",
                            "description": "Total project cost in INR"
                        },
                        "project_duration_months": {
                            "type": "integer",
                            "description": "Project duration in months"
                        },
                        "market_data": {
                            "type": "object",
                            "description": "Market data with pricing, area, and absorption for each unit type (1BHK, 2BHK, 3BHK)"
                        }
                    },
                    "required": ["total_units", "total_land_area_sqft", "total_project_cost", "project_duration_months", "market_data"]
                }
            },
            "handler": lambda params: Layer3Optimizer.optimize_product_mix(**params),
            "layer": 3,
            "category": "optimizer"
        }

        self._functions["market_opportunity_scoring"] = {
            "schema": {
                "name": "market_opportunity_scoring",
                "description": "Calculate market opportunity score (OPPS) for a location using LF market data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location name (e.g., 'Chakan', 'Hinjewadi')"
                        },
                        "unit_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Unit types to consider (e.g., ['1BHK', '2BHK', '3BHK'])"
                        }
                    },
                    "required": ["location", "unit_types"]
                }
            },
            "handler": self._handle_market_opportunity_scoring,
            "layer": 3,
            "category": "optimizer"
        }

    # ==================== LAYER 4 FUNCTIONS (GraphRAG) ====================

    def _register_layer4_functions(self):
        """Register Layer 4 functions: GraphRAG & semantic search"""

        self._functions["semantic_search_market_insights"] = {
            "schema": {
                "name": "semantic_search_market_insights",
                "description": "Search city market reports using semantic search. Returns relevant insights from vector database.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (e.g., 'Chakan infrastructure development', 'Hinjewadi social amenities')"
                        },
                        "city": {
                            "type": "string",
                            "description": "City name to filter results (optional)"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)"
                        }
                    },
                    "required": ["query"]
                }
            },
            "handler": self._handle_semantic_search,
            "layer": 4,
            "category": "graphrag"
        }

        self._functions["get_city_overview"] = {
            "schema": {
                "name": "get_city_overview",
                "description": "Get executive summary and overview of a city's real estate market",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "City name (e.g., 'Mumbai', 'Pune')"
                        }
                    },
                    "required": ["city"]
                }
            },
            "handler": self._handle_get_city_overview,
            "layer": 4,
            "category": "graphrag"
        }

        self._functions["get_locality_insights"] = {
            "schema": {
                "name": "get_locality_insights",
                "description": "Get micro-market insights for a specific locality/region",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "locality": {
                            "type": "string",
                            "description": "Locality name (e.g., 'Chakan', 'Hinjewadi', 'Wakad')"
                        },
                        "city": {
                            "type": "string",
                            "description": "City name"
                        }
                    },
                    "required": ["locality", "city"]
                }
            },
            "handler": self._handle_get_locality_insights,
            "layer": 4,
            "category": "graphrag"
        }

    # ==================== CONTEXT FUNCTIONS ====================

    def _register_context_functions(self):
        """Register context enrichment functions (Google APIs)"""

        self._functions["get_location_context"] = {
            "schema": {
                "name": "get_location_context",
                "description": "Get comprehensive location context including maps, weather, photos, distances, air quality, and nearby places",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location_name": {
                            "type": "string",
                            "description": "Location or project name"
                        },
                        "city": {
                            "type": "string",
                            "description": "City name for better context"
                        }
                    },
                    "required": ["location_name"]
                }
            },
            "handler": self._handle_get_location_context,
            "layer": 0,
            "category": "context"
        }

    # ==================== DATA RETRIEVAL FUNCTIONS ====================

    def _register_data_functions(self):
        """Register data retrieval functions"""

        self._functions["get_projects_by_location"] = {
            "schema": {
                "name": "get_projects_by_location",
                "description": "Get all projects in a specific location (city, region, or micromarket)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location name (e.g., 'Pune', 'Chakan', 'Hinjewadi')"
                        }
                    },
                    "required": ["location"]
                }
            },
            "handler": self._handle_get_projects_by_location,
            "layer": 0,
            "category": "data_retrieval"
        }

        self._functions["compare_projects"] = {
            "schema": {
                "name": "compare_projects",
                "description": "Compare multiple projects across key metrics (PSF, units, land area, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "List of project IDs to compare"
                        },
                        "metrics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of metrics to compare (optional, defaults to key metrics)"
                        }
                    },
                    "required": ["project_ids"]
                }
            },
            "handler": self._handle_compare_projects,
            "layer": 2,
            "category": "data_retrieval"
        }

    # ==================== HANDLER IMPLEMENTATIONS ====================

    def _handle_get_project_dimensions(self, params: Dict) -> Dict:
        """Handler for get_project_dimensions"""
        project_id = params.get("project_id")
        project = self.data_service.get_project_by_id(project_id)
        if not project:
            return {"error": f"Project ID {project_id} not found"}
        return project

    def _handle_get_project_by_name(self, params: Dict) -> Dict:
        """Handler for get_project_by_name"""
        project_name = params.get("project_name")
        projects = self.data_service.get_all_projects()

        for project in projects:
            if project.get("projectName", {}).get("value", "").lower() == project_name.lower():
                return project

        return {"error": f"Project '{project_name}' not found"}

    def _handle_calculate_npv(self, params: Dict) -> Dict:
        """Handler for calculate_npv"""
        projection = FinancialProjection(
            initial_investment=params["initial_investment"],
            annual_cash_flows=params["annual_cash_flows"],
            discount_rate=params["discount_rate"],
            project_duration_years=len(params["annual_cash_flows"])
        )
        npv = Layer2Calculator.calculate_npv(projection)
        return {
            "metric": "NPV",
            "value": round(npv, 2),
            "unit": "INR",
            "dimension": "C",
            "inputs": params
        }

    def _handle_calculate_irr(self, params: Dict) -> Dict:
        """Handler for calculate_irr"""
        projection = FinancialProjection(
            initial_investment=params["initial_investment"],
            annual_cash_flows=params["annual_cash_flows"],
            discount_rate=0.12,  # Default discount rate for IRR calculation
            project_duration_years=len(params["annual_cash_flows"])
        )
        irr = Layer2Calculator.calculate_irr(projection)
        return {
            "metric": "IRR",
            "value": round(irr * 100, 2) if irr else None,
            "unit": "%",
            "dimension": "T^-1",
            "algorithm": "Newton's method (scipy)",
            "inputs": params
        }

    def _handle_calculate_payback_period(self, params: Dict) -> Dict:
        """Handler for calculate_payback_period"""
        projection = FinancialProjection(
            initial_investment=params["initial_investment"],
            annual_cash_flows=params["annual_cash_flows"],
            discount_rate=0.12,
            project_duration_years=len(params["annual_cash_flows"])
        )
        payback = Layer2Calculator.calculate_payback_period(projection)
        return {
            "metric": "PaybackPeriod",
            "value": round(payback, 2) if payback else None,
            "unit": "years",
            "dimension": "T",
            "inputs": params
        }

    def _handle_calculate_statistics(self, params: Dict) -> Dict:
        """Handler for calculate_statistics"""
        metric_name = params["metric_name"]
        location = params.get("location")

        # Get projects (optionally filtered by location)
        if location:
            projects = self.data_service.get_projects_by_location(location)
        else:
            projects = self.data_service.get_all_projects()

        # Extract metric values
        values = []
        for project in projects:
            value = project.get(metric_name, {}).get("value")
            if value is not None:
                values.append(float(value))

        if not values:
            return {"error": f"No values found for metric '{metric_name}'"}

        # Calculate statistics
        stats = self.statistical_service.calculate_series_statistics(values, metric_name)
        stats["location_filter"] = location
        stats["project_count"] = len(values)
        return stats

    def _handle_get_top_n_projects(self, params: Dict) -> Dict:
        """Handler for get_top_n_projects"""
        metric_name = params["metric_name"]
        n = params.get("n", 5)
        location = params.get("location")
        order = params.get("order", "desc")

        # Get projects (optionally filtered by location)
        if location:
            projects = self.data_service.get_projects_by_location(location)
        else:
            projects = self.data_service.get_all_projects()

        # Extract and sort
        project_values = []
        for project in projects:
            value = project.get(metric_name, {}).get("value")
            if value is not None:
                project_values.append({
                    "projectId": project.get("projectId", {}).get("value"),
                    "projectName": project.get("projectName", {}).get("value"),
                    "value": float(value),
                    "unit": project.get(metric_name, {}).get("unit", "")
                })

        # Sort
        reverse = (order == "desc")
        project_values.sort(key=lambda x: x["value"], reverse=reverse)

        # Take top N
        top_projects = project_values[:n]

        return {
            "metric": metric_name,
            "top_n": n,
            "order": order,
            "results": top_projects
        }

    def _handle_market_opportunity_scoring(self, params: Dict) -> Dict:
        """Handler for market_opportunity_scoring"""
        location = params["location"]
        unit_types = params["unit_types"]

        # Mock LF market data (in real implementation, fetch from LF API)
        lf_market_data = {
            "demand_score": 75,
            "supply_pressure": "medium",
            "competitive_intensity": "medium"
        }

        return Layer3Optimizer.market_opportunity_scoring(
            location=location,
            unit_types=unit_types,
            lf_market_data=lf_market_data
        )

    def _handle_semantic_search(self, params: Dict) -> Dict:
        """Handler for semantic_search_market_insights"""
        query = params["query"]
        city = params.get("city")
        n_results = params.get("n_results", 5)

        results = self.vector_db.semantic_search(
            query=query,
            city=city,
            n_results=n_results
        )

        return {
            "query": query,
            "city": city,
            "results": results
        }

    def _handle_get_city_overview(self, params: Dict) -> Dict:
        """Handler for get_city_overview"""
        city = params["city"]
        overview = self.vector_db.get_city_overview(city)
        return overview

    def _handle_get_locality_insights(self, params: Dict) -> Dict:
        """Handler for get_locality_insights"""
        locality = params["locality"]
        city = params["city"]

        insights = self.vector_db.get_locality_insights(
            locality=locality,
            city=city
        )
        return insights

    def _handle_get_location_context(self, params: Dict) -> Dict:
        """Handler for get_location_context"""
        location_name = params["location_name"]
        city = params.get("city")

        context = self.context_service.get_location_context(
            location_name=location_name,
            city=city
        )
        return context

    def _handle_get_projects_by_location(self, params: Dict) -> Dict:
        """Handler for get_projects_by_location"""
        location = params["location"]
        projects = self.data_service.get_projects_by_location(location)
        return {
            "location": location,
            "project_count": len(projects),
            "projects": projects
        }

    def _handle_compare_projects(self, params: Dict) -> Dict:
        """Handler for compare_projects"""
        project_ids = params["project_ids"]
        metrics = params.get("metrics", [
            "projectName", "currentPricePSF", "totalUnits",
            "landAreaAcres", "city", "region", "microMarket"
        ])

        comparison = []
        for project_id in project_ids:
            project = self.data_service.get_project_by_id(project_id)
            if project:
                project_data = {"projectId": project_id}
                for metric in metrics:
                    value_obj = project.get(metric, {})
                    if isinstance(value_obj, dict):
                        project_data[metric] = {
                            "value": value_obj.get("value"),
                            "unit": value_obj.get("unit", "")
                        }
                    else:
                        project_data[metric] = value_obj
                comparison.append(project_data)

        return {
            "comparison_count": len(comparison),
            "metrics": metrics,
            "projects": comparison
        }

    # ==================== PUBLIC API ====================

    def get_all_function_schemas(self) -> List[Dict]:
        """
        Get all function schemas in Gemini-compatible format

        Returns:
            List of function schema dictionaries
        """
        return [func["schema"] for func in self._functions.values()]

    def get_function_by_name(self, function_name: str) -> Optional[Dict]:
        """Get function metadata by name"""
        return self._functions.get(function_name)

    def execute_function(self, function_name: str, parameters: Dict) -> Any:
        """
        Execute a function by name with given parameters

        Args:
            function_name: Name of the function to execute
            parameters: Dictionary of parameters

        Returns:
            Function result

        Raises:
            ValueError: If function not found
        """
        function = self._functions.get(function_name)
        if not function:
            raise ValueError(f"Function '{function_name}' not found in registry")

        handler = function["handler"]

        # Execute handler
        try:
            result = handler(parameters)
            return result
        except Exception as e:
            return {
                "error": f"Error executing {function_name}: {str(e)}",
                "function": function_name,
                "parameters": parameters
            }

    def get_functions_by_layer(self, layer: int) -> List[str]:
        """Get all function names for a specific layer"""
        return [
            name for name, func in self._functions.items()
            if func["layer"] == layer
        ]

    def get_functions_by_category(self, category: str) -> List[str]:
        """Get all function names for a specific category"""
        return [
            name for name, func in self._functions.items()
            if func["category"] == category
        ]

    def get_function_count(self) -> int:
        """Get total number of registered functions"""
        return len(self._functions)

    def get_registry_summary(self) -> Dict:
        """Get summary of function registry"""
        summary = {
            "total_functions": len(self._functions),
            "by_layer": {},
            "by_category": {},
            "function_names": list(self._functions.keys())
        }

        # Count by layer
        for layer in range(5):
            count = len(self.get_functions_by_layer(layer))
            if count > 0:
                summary["by_layer"][f"layer{layer}"] = count

        # Count by category
        categories = set(func["category"] for func in self._functions.values())
        for category in categories:
            summary["by_category"][category] = len(self.get_functions_by_category(category))

        return summary


# Global singleton instance
_function_registry_instance = None

def get_function_registry() -> FunctionRegistry:
    """Get or create global function registry instance"""
    global _function_registry_instance
    if _function_registry_instance is None:
        _function_registry_instance = FunctionRegistry()
    return _function_registry_instance
