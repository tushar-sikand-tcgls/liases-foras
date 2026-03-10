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
from app.services.quarterly_market_service import quarterly_market_service  # Quarterly market data
from app.models.domain import FinancialProjection


class FunctionRegistry:
    """
    Centralized registry of all available functions for LLM-driven routing

    Provides:
    - Gemini-compatible function schemas (for function calling)
    - Execution handlers for each function
    - Layer/category organization
    """

    def __init__(self, city: str = "Pune"):
        """
        Initialize function registry with all available functions

        Args:
            city: City name for data service (e.g., "Pune", "Kolkata"). Default: "Pune"
        """
        self.city = city
        # Get city-specific data service instead of using singleton
        from app.services.data_service import get_data_service
        self.data_service = get_data_service(city)
        self.vector_db = VectorDBService()
        self.context_service = ContextService()
        self.statistical_service = StatisticalService()
        self.quarterly_market_service = quarterly_market_service  # Quarterly market data service

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

        # Quarterly Market Data Functions (Time-Series Analysis)
        self._register_quarterly_market_functions()

        # Charting/Visualization Functions
        self._register_charting_functions()

        # Unit Size Range Analysis Functions (Product Performance - Pillar 2)
        self._register_unit_size_range_functions()

        # Unit Ticket Size Analysis Functions (Product Performance - Pillar 2)
        self._register_unit_ticket_size_functions()

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

        self._functions["find_projects_within_radius"] = {
            "schema": {
                "name": "find_projects_within_radius",
                "description": "Find all projects within a specified radius (in kilometers) of a center project using Haversine formula for great-circle distance calculation. Returns list of projects sorted by distance.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "center_project": {
                            "type": "string",
                            "description": "Name of the center project (e.g., 'Sara City', 'Gulmohar City')"
                        },
                        "radius_km": {
                            "type": "number",
                            "description": "Search radius in kilometers (e.g., 2 for 2 KM radius)"
                        }
                    },
                    "required": ["center_project", "radius_km"]
                }
            },
            "handler": self._handle_find_projects_within_radius,
            "layer": 0,
            "category": "data_retrieval"
        }

        self._functions["getDistanceFromProject"] = {
            "schema": {
                "name": "getDistanceFromProject",
                "description": "Calculate the Haversine distance (in kilometers) between two specific projects using their latitude and longitude coordinates. IMPORTANT: This function automatically retrieves the lat/long coordinates for both projects - you just need to provide the project names. Perfect for queries like 'Distance between Sara City and Gulmohar City' or 'How far is Project X from Project Y'. Returns the great-circle distance in kilometers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "source_project": {
                            "type": "string",
                            "description": "Name of the source/reference project (e.g., 'Sara City', 'Gulmohar City')"
                        },
                        "target_project": {
                            "type": "string",
                            "description": "Name of the target project to measure distance to (e.g., 'VTP Pegasus', 'Megapolis Smart Homes 1')"
                        }
                    },
                    "required": ["source_project", "target_project"]
                }
            },
            "handler": self._handle_get_distance_from_project,
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

        self._functions["generate_location_map_with_poi"] = {
            "schema": {
                "name": "generate_location_map_with_poi",
                "description": "Generate a comprehensive Google Maps visualization showing a project location with nearby important places marked with colored markers. POIs include: Hotels (blue), Petrol Pumps (green), Railway Stations (purple), Airports (orange), Metro Stations (yellow), Bus Stops (brown), Hospitals (pink), Schools (cyan), Shopping Malls (gray). Perfect for queries like 'Show me a map of Sara City with nearby places', 'Generate a map for Gulmohar City with POIs', 'Visualize project location with amenities'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_name": {
                            "type": "string",
                            "description": "Name of the project to visualize (e.g., 'Sara City', 'Gulmohar City', 'VTP Pegasus')"
                        },
                        "latitude": {
                            "type": "number",
                            "description": "Project latitude coordinate (e.g., 18.7381)"
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Project longitude coordinate (e.g., 73.9698)"
                        },
                        "city": {
                            "type": "string",
                            "description": "City name for context (default: 'Pune')"
                        },
                        "zoom": {
                            "type": "integer",
                            "description": "Map zoom level 1-20 (default: 14, where 14 shows ~2-3km radius)"
                        }
                    },
                    "required": ["project_name", "latitude", "longitude"]
                }
            },
            "handler": self._handle_generate_location_map_with_poi,
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

    def _handle_find_projects_within_radius(self, params: Dict) -> Dict:
        """Handler for find_projects_within_radius"""
        center_project = params.get("center_project")
        radius_km = params.get("radius_km")

        # Call the data service's proximity search function
        nearby_projects = self.data_service.find_projects_within_radius(
            center_project=center_project,
            radius_km=radius_km
        )

        if isinstance(nearby_projects, list) and len(nearby_projects) == 0:
            return {
                "center_project": center_project,
                "radius_km": radius_km,
                "found_count": 0,
                "projects": [],
                "message": f"No projects found within {radius_km} KM of {center_project}"
            }

        return {
            "center_project": center_project,
            "radius_km": radius_km,
            "found_count": len(nearby_projects),
            "projects": nearby_projects,
            "message": f"Found {len(nearby_projects)} project(s) within {radius_km} KM of {center_project}"
        }

    def _handle_get_distance_from_project(self, params: Dict) -> Dict:
        """Handler for getDistanceFromProject"""
        from app.utils.geospatial import get_distance_between_projects

        source_project = params.get("source_project")
        target_project = params.get("target_project")

        # Get all projects
        all_projects = self.data_service.get_all_projects()

        # Calculate distance
        distance_km = get_distance_between_projects(
            source_project=source_project,
            target_project=target_project,
            all_projects=all_projects
        )

        if distance_km is None:
            # Check which project(s) were not found
            from app.utils.geospatial import get_project_coordinates
            source_coords = get_project_coordinates(source_project, all_projects)
            target_coords = get_project_coordinates(target_project, all_projects)

            if source_coords is None and target_coords is None:
                error_msg = f"Both projects '{source_project}' and '{target_project}' not found or missing coordinates"
            elif source_coords is None:
                error_msg = f"Source project '{source_project}' not found or missing coordinates"
            else:
                error_msg = f"Target project '{target_project}' not found or missing coordinates"

            return {
                "source_project": source_project,
                "target_project": target_project,
                "distance_km": None,
                "error": error_msg
            }

        return {
            "source_project": source_project,
            "target_project": target_project,
            "distance_km": round(distance_km, 3),
            "unit": "kilometers",
            "message": f"Distance from {source_project} to {target_project} is {distance_km:.3f} km"
        }

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

    def _handle_generate_location_map_with_poi(self, params: Dict) -> Dict:
        """Handler for generate_location_map_with_poi"""
        project_name = params["project_name"]
        latitude = params["latitude"]
        longitude = params["longitude"]
        city = params.get("city", "Pune")
        zoom = params.get("zoom", 14)

        map_data = self.context_service.generate_location_map_with_poi(
            project_name=project_name,
            latitude=latitude,
            longitude=longitude,
            city=city,
            zoom=zoom
        )
        return map_data

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

    # ==================== QUARTERLY MARKET KNOWLEDGE GRAPH ====================

    def _register_quarterly_market_functions(self):
        """
        Register Quarterly Market Knowledge Graph function

        Each quarter is a first-class KG node with:
        - Layer 0: Raw dimensions (Sales Units, Sales Area, Supply Units, Supply Area)
        - Layer 1: Derived metrics (Absorption Rate, YoY Growth, QoQ Growth, Avg Unit Size)
        """

        self._functions["quarterly_market_lookup"] = {
            "schema": {
                "name": "quarterly_market_lookup",
                "description": """Query Quarterly Market Knowledge Graph for sales and supply data.

DEFAULT FUNCTION for market-level queries (no specific project mentioned).

Each quarter is a KG node with:
• Layer 0: Sales Units, Sales Area (mn sq ft), Supply Units, Supply Area (mn sq ft)
• Layer 1: Absorption Rate, YoY Growth, QoQ Growth, Average Unit Size

Query Types:
1. By fiscal year: {"year": 2024} → All quarters in FY 24-25
2. By year range: {"year_range": [2022, 2024]} → All quarters 2022-2024
3. By quarter ID: {"quarter_id": "Q1_FY24_25"} → Specific quarter
4. Recent quarters: {"recent": 8} → Last 8 quarters
5. All data: {} (empty filters) → All quarters from Q2 FY14-15 to Q2 FY25-26

Examples:
- "What is supply units for FY 24-25?" → {"year": 2024}
- "Show me sales in 2023" → {"year": 2023}
- "What are recent market trends?" → {"recent": 8}
- "Get Q1 2024 data" → {"quarter_id": "Q1_FY24_25"}

Returns: Quarter nodes with Layer 0 + Layer 1 data, location context, aggregated metrics.""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "integer",
                            "description": "Query by fiscal year (e.g., 2024 for FY 24-25). Returns all 4 quarters."
                        },
                        "year_range": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Query by year range [start_year, end_year]. Example: [2022, 2024]",
                            "minItems": 2,
                            "maxItems": 2
                        },
                        "quarter_id": {
                            "type": "string",
                            "description": "Specific quarter ID (e.g., 'Q1_FY24_25', 'Q3_FY23_24')"
                        },
                        "recent": {
                            "type": "integer",
                            "description": "Get N most recent quarters. Default: 8 (2 years)"
                        },
                        "quarter_num": {
                            "type": "integer",
                            "description": "Filter by quarter number (1-4). Example: 1 for all Q1 quarters across years"
                        }
                    }
                }
            },
            "handler": self._handle_quarterly_market_lookup,
            "layer": 0,
            "category": "market_data"
        }

        # Keep the old functions for backward compatibility (deprecated)
        self._functions["calculate_yoy_growth"] = {
            "schema": {
                "name": "calculate_yoy_growth",
                "description": "Calculate Year-over-Year (YoY) growth for sales or supply metrics. Compares each quarter with the same quarter in the previous year. Perfect for queries like 'What's the YoY growth in sales?', 'Show me year-over-year supply trends', 'Calculate annual growth rates'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric": {
                            "type": "string",
                            "description": "Metric to analyze: 'sales_units', 'sales_area_mn_sqft', 'supply_units', or 'supply_area_mn_sqft'",
                            "enum": ["sales_units", "sales_area_mn_sqft", "supply_units", "supply_area_mn_sqft"]
                        }
                    },
                    "required": ["metric"]
                }
            },
            "handler": self._handle_calculate_yoy_growth,
            "layer": 1,
            "category": "market_analysis"
        }

        self._functions["calculate_qoq_growth"] = {
            "schema": {
                "name": "calculate_qoq_growth",
                "description": "Calculate Quarter-over-Quarter (QoQ) growth for sales or supply metrics. Compares each quarter with the immediately previous quarter. Perfect for queries like 'What's the QoQ growth trend?', 'Show me quarterly momentum', 'Is supply increasing or decreasing quarter-to-quarter?'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric": {
                            "type": "string",
                            "description": "Metric to analyze: 'sales_units', 'sales_area_mn_sqft', 'supply_units', or 'supply_area_mn_sqft'",
                            "enum": ["sales_units", "sales_area_mn_sqft", "supply_units", "supply_area_mn_sqft"]
                        }
                    },
                    "required": ["metric"]
                }
            },
            "handler": self._handle_calculate_qoq_growth,
            "layer": 1,
            "category": "market_analysis"
        }

        self._functions["get_market_summary_statistics"] = {
            "schema": {
                "name": "get_market_summary_statistics",
                "description": "Calculate summary statistics (min, max, mean, median, total) for a sales or supply metric across all quarters. Perfect for queries like 'What are the overall market statistics?', 'Show me average quarterly sales', 'What's the peak supply recorded?'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric": {
                            "type": "string",
                            "description": "Metric to analyze: 'sales_units', 'sales_area_mn_sqft', 'supply_units', or 'supply_area_mn_sqft'",
                            "enum": ["sales_units", "sales_area_mn_sqft", "supply_units", "supply_area_mn_sqft"]
                        }
                    },
                    "required": ["metric"]
                }
            },
            "handler": self._handle_get_market_summary_statistics,
            "layer": 1,
            "category": "market_analysis"
        }

        self._functions["calculate_absorption_rate_trend"] = {
            "schema": {
                "name": "calculate_absorption_rate_trend",
                "description": "Calculate quarterly absorption rate trends: (Sales Units / Supply Units) × 100. This is a Layer 1 derived metric showing how quickly the market is absorbing available supply. Perfect for queries like 'What's the absorption rate trend?', 'How fast is the market absorbing supply?', 'Show me absorption rates over time'.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            "handler": self._handle_calculate_absorption_rate_trend,
            "layer": 1,
            "category": "market_analysis"
        }

    # ==================== QUARTERLY MARKET HANDLERS ====================

    def _handle_quarterly_market_lookup(self, params: Dict) -> Dict:
        """
        Handler for quarterly_market_lookup - Query Quarterly Market KG

        Parameters can include:
        - year: int (e.g., 2024 for FY 24-25)
        - year_range: [start, end] (e.g., [2022, 2024])
        - quarter_id: str (e.g., "Q1_FY24_25")
        - recent: int (e.g., 8 for last 8 quarters)
        - quarter_num: int (1-4, filter by Q1, Q2, etc.)
        """
        from app.services.quarterly_market_kg_service import get_quarterly_market_kg_service

        kg_service = get_quarterly_market_kg_service()
        metadata = kg_service.get_metadata()

        # Determine query type and fetch quarters
        quarter_nodes = []

        if "quarter_id" in params:
            # Specific quarter by ID
            quarter = kg_service.get_quarter_by_id(params["quarter_id"])
            quarter_nodes = [quarter] if quarter else []

        elif "year" in params:
            # All quarters in a specific fiscal year
            quarter_nodes = kg_service.get_quarters_by_year(params["year"])

        elif "year_range" in params:
            # All quarters in a year range
            start_year, end_year = params["year_range"]
            quarter_nodes = kg_service.get_quarters_by_year_range(start_year, end_year)

        elif "recent" in params:
            # N most recent quarters
            quarter_nodes = kg_service.get_recent_quarters(params["recent"])

        else:
            # Default: Get recent 8 quarters (2 years)
            quarter_nodes = kg_service.get_recent_quarters(8)

        # Optional filter by quarter number (Q1, Q2, Q3, Q4)
        if "quarter_num" in params:
            quarter_nodes = [q for q in quarter_nodes if q.quarter_num == params["quarter_num"]]

        # Convert quarter nodes to dicts with Layer 0 + Layer 1 structure
        quarters_data = [q.to_dict() for q in quarter_nodes]

        # Calculate aggregated metrics
        total_sales = sum(q.sales_units for q in quarter_nodes)
        total_supply = sum(q.supply_units for q in quarter_nodes)
        total_sales_area = sum(q.sales_area_mn_sqft for q in quarter_nodes)
        total_supply_area = sum(q.supply_area_mn_sqft for q in quarter_nodes)
        avg_sales_per_quarter = total_sales / len(quarter_nodes) if quarter_nodes else 0
        avg_supply_per_quarter = total_supply / len(quarter_nodes) if quarter_nodes else 0
        avg_absorption_rate = (total_sales / total_supply * 100) if total_supply > 0 else 0

        # Build location string from metadata
        location_info = metadata.get('location', {})
        region = location_info.get('region', 'Region')
        city = location_info.get('city', '')
        location_str = f"{region}, {city}" if city else region

        # Generate pre-computed insights for Gemini to use
        insights = self._generate_quarterly_insights(quarter_nodes, quarters_data, params)

        return {
            "quarters": quarters_data,
            "location": {
                "region": region,
                "city": city,
                "state": location_info.get('state', '')
            },
            "aggregated_metrics": {
                "total_sales_units": total_sales,
                "total_supply_units": total_supply,
                "total_sales_area_mn_sqft": round(total_sales_area, 2),
                "total_supply_area_mn_sqft": round(total_supply_area, 2),
                "average_sales_per_quarter": round(avg_sales_per_quarter, 0),
                "average_supply_per_quarter": round(avg_supply_per_quarter, 0),
                "overall_absorption_rate": round(avg_absorption_rate, 2)
            },
            "quarters_count": len(quarters_data),
            "query_params": params,
            "message": f"{location_str}: {len(quarters_data)} quarters (Total Supply: {total_supply:,} units, Total Sales: {total_sales:,} units)",
            "insights": insights  # Pre-computed insights that MUST be included in answer
        }

    def _generate_quarterly_insights(self, quarter_nodes: List, quarters_data: List[Dict], params: Dict) -> Dict:
        """
        Generate pre-computed insights for quarterly data that Gemini MUST include in response

        Returns insights including:
        - Trend analysis (increasing/decreasing)
        - Best/worst performing quarters
        - YoY and QoQ momentum
        - Market commentary and observations
        """
        if not quarter_nodes:
            return {"commentary": "No data available for analysis."}

        # Find best and worst quarters by supply/sales
        best_supply_q = max(quarter_nodes, key=lambda q: q.supply_units)
        worst_supply_q = min(quarter_nodes, key=lambda q: q.supply_units)
        best_sales_q = max(quarter_nodes, key=lambda q: q.sales_units)

        # Calculate YoY growth trend
        yoy_growths = [q.yoy_growth_supply for q in quarter_nodes if q.yoy_growth_supply is not None]
        yoy_trend = "accelerating" if len(yoy_growths) > 1 and yoy_growths[-1] > yoy_growths[0] else "decelerating" if len(yoy_growths) > 1 else "stable"

        # Calculate QoQ trend
        qoq_growths = [q.qoq_growth_supply for q in quarter_nodes if q.qoq_growth_supply is not None]
        qoq_trend = "increasing" if len(qoq_growths) > 1 and qoq_growths[-1] > 0 else "decreasing" if len(qoq_growths) > 1 and qoq_growths[-1] < 0 else "stable"

        # Build detailed commentary
        commentary_parts = []

        # Overall performance
        total_supply = sum(q.supply_units for q in quarter_nodes)
        total_sales = sum(q.sales_units for q in quarter_nodes)
        avg_absorption = (total_sales / total_supply * 100) if total_supply > 0 else 0

        commentary_parts.append(f"The market added a total of **{total_supply:,} supply units** across {len(quarter_nodes)} quarters with an overall absorption rate of **{avg_absorption:.2f}%**.")

        # Best/worst quarter analysis
        commentary_parts.append(f"**{best_supply_q.quarter}** recorded the highest supply with **{best_supply_q.supply_units:,} units**, while **{worst_supply_q.quarter}** had the lowest at **{worst_supply_q.supply_units:,} units**.")

        # YoY trend analysis
        if yoy_growths:
            first_yoy = yoy_growths[0]
            last_yoy = yoy_growths[-1] if len(yoy_growths) > 1 else first_yoy
            commentary_parts.append(f"Year-over-year growth showed a **{yoy_trend}** trend, starting at **{first_yoy:+.1f}%** and ending at **{last_yoy:+.1f}%**.")

        # QoQ momentum
        if qoq_growths:
            commentary_parts.append(f"Quarter-over-quarter momentum was **{qoq_trend}**, indicating {'strengthening' if qoq_trend == 'increasing' else 'weakening' if qoq_trend == 'decreasing' else 'stable'} supply additions.")

        # Distribution balance
        supply_variance = max(q.supply_units for q in quarter_nodes) - min(q.supply_units for q in quarter_nodes)
        avg_supply = sum(q.supply_units for q in quarter_nodes) / len(quarter_nodes)
        balance_ratio = (supply_variance / avg_supply * 100) if avg_supply > 0 else 0

        if balance_ratio < 10:
            commentary_parts.append(f"The quarterly distribution is **remarkably balanced** ({balance_ratio:.1f}% variance), suggesting well-planned inventory management.")
        elif balance_ratio < 25:
            commentary_parts.append(f"The quarterly distribution shows **moderate variation** ({balance_ratio:.1f}% variance), indicating planned seasonal adjustments.")
        else:
            commentary_parts.append(f"The quarterly distribution shows **high variation** ({balance_ratio:.1f}% variance), indicating significant seasonal or strategic supply changes.")

        # Absorption insights
        if avg_absorption < 5:
            commentary_parts.append(f"The absorption rate of **{avg_absorption:.2f}%** is quite low, suggesting potential oversupply or weak demand conditions.")
        elif avg_absorption < 15:
            commentary_parts.append(f"The absorption rate of **{avg_absorption:.2f}%** indicates moderate market absorption - healthy supply without oversupply.")
        else:
            commentary_parts.append(f"The absorption rate of **{avg_absorption:.2f}%** is strong, indicating healthy demand absorbing available supply efficiently.")

        return {
            "best_supply_quarter": f"{best_supply_q.quarter} ({best_supply_q.supply_units:,} units)",
            "worst_supply_quarter": f"{worst_supply_q.quarter} ({worst_supply_q.supply_units:,} units)",
            "best_sales_quarter": f"{best_sales_q.quarter} ({best_sales_q.sales_units:,} units)",
            "yoy_trend": yoy_trend,
            "qoq_trend": qoq_trend,
            "commentary": " ".join(commentary_parts),
            "MANDATORY_INSTRUCTION": "YOU MUST include the 'commentary' section above in your final answer. This provides essential market insights and trend analysis."
        }

    def _handle_get_all_quarterly_data(self, params: Dict) -> Dict:
        """Handler for get_all_quarterly_data"""
        data = self.quarterly_market_service.get_all_quarters()
        metadata = self.quarterly_market_service.get_metadata()
        return {
            "data": data,
            "metadata": metadata,
            "count": len(data),
            "message": f"Retrieved {len(data)} quarters of data from {metadata.get('date_range', {}).get('start')} to {metadata.get('date_range', {}).get('end')}"
        }

    def _handle_get_recent_quarters(self, params: Dict) -> Dict:
        """Handler for get_recent_quarters"""
        n = params.get("n", 8)
        data = self.quarterly_market_service.get_recent_quarters(n)
        return {
            "data": data,
            "count": len(data),
            "quarters_requested": n,
            "message": f"Retrieved most recent {len(data)} quarters"
        }

    def _handle_get_quarters_by_year_range(self, params: Dict) -> Dict:
        """Handler for get_quarters_by_year_range"""
        start_year = params.get("start_year")
        end_year = params.get("end_year")
        data = self.quarterly_market_service.get_quarters_by_year_range(start_year, end_year)

        # Calculate aggregated metrics for the year range
        total_sales = sum(q.get('sales_units', 0) for q in data)
        total_supply = sum(q.get('supply_units', 0) for q in data)
        avg_sales_per_quarter = total_sales / len(data) if data else 0
        avg_supply_per_quarter = total_supply / len(data) if data else 0
        avg_absorption_rate = (total_sales / total_supply * 100) if total_supply > 0 else 0

        # Get metadata for location info
        metadata = self.quarterly_market_service.get_metadata()
        location_info = metadata.get('location', {})

        # Build location string from metadata
        region = location_info.get('region', 'Region')
        city = location_info.get('city', '')
        location_str = f"{region}, {city}" if city else region

        return {
            "location": {
                "region": region,
                "city": city,
                "state": location_info.get('state', '')
            },
            "fiscal_year": f"FY {start_year}-{str(end_year)[-2:]}" if start_year == end_year else f"FY {start_year}-{str(start_year)[-2:]} to FY {end_year}-{str(end_year)[-2:]}",
            "quarterly_data": data,
            "aggregated_metrics": {
                "total_sales_units": total_sales,
                "total_supply_units": total_supply,
                "average_sales_per_quarter": round(avg_sales_per_quarter, 0),
                "average_supply_per_quarter": round(avg_supply_per_quarter, 0),
                "overall_absorption_rate": round(avg_absorption_rate, 2)
            },
            "quarters_count": len(data),
            "year_range": {"start": start_year, "end": end_year},
            "message": f"{location_str}: {len(data)} quarters from FY {start_year}-{str(start_year)[-2:]} (Total Supply: {total_supply:,} units, Total Sales: {total_sales:,} units)"
        }

    def _handle_calculate_yoy_growth(self, params: Dict) -> Dict:
        """Handler for calculate_yoy_growth"""
        metric = params.get("metric", "sales_units")
        growth_data = self.quarterly_market_service.calculate_yoy_growth(metric)
        return {
            "growth_data": growth_data,
            "count": len(growth_data),
            "metric": metric,
            "analysis_type": "Year-over-Year",
            "message": f"Calculated YoY growth for {metric} across {len(growth_data)} comparable quarters"
        }

    def _handle_calculate_qoq_growth(self, params: Dict) -> Dict:
        """Handler for calculate_qoq_growth"""
        metric = params.get("metric", "sales_units")
        growth_data = self.quarterly_market_service.calculate_qoq_growth(metric)
        return {
            "growth_data": growth_data,
            "count": len(growth_data),
            "metric": metric,
            "analysis_type": "Quarter-over-Quarter",
            "message": f"Calculated QoQ growth for {metric} across {len(growth_data)} quarters"
        }

    def _handle_get_market_summary_statistics(self, params: Dict) -> Dict:
        """Handler for get_market_summary_statistics"""
        metric = params.get("metric", "sales_units")
        stats = self.quarterly_market_service.get_summary_statistics(metric)
        return {
            "statistics": stats,
            "metric": metric,
            "message": f"Summary statistics for {metric} across all quarters"
        }

    def _handle_calculate_absorption_rate_trend(self, params: Dict) -> Dict:
        """Handler for calculate_absorption_rate_trend"""
        absorption_data = self.quarterly_market_service.calculate_absorption_rate_trend()
        return {
            "absorption_data": absorption_data,
            "count": len(absorption_data),
            "metric": "Absorption Rate (%)",
            "formula": "(Sales Units / Supply Units) × 100",
            "layer": "Layer 1 - Derived Metric",
            "dimension": "(U/U) × 100",
            "message": f"Calculated absorption rates for {len(absorption_data)} quarters"
        }

    # ==================== CHARTING/VISUALIZATION FUNCTIONS ====================

    def _register_charting_functions(self):
        """
        Register charting/visualization functions for Gemini to enhance user experience

        Gemini can invoke these functions to automatically generate charts when displaying
        tabular or multi-row data, improving visual comprehension of trends and patterns.
        """

        self._functions["generate_chart"] = {
            "schema": {
                "name": "generate_chart",
                "description": """**CRITICAL FUNCTION** - Generate a chart visualization for tabular data to enhance user experience.

⚠️ MANDATORY: YOU MUST CALL THIS FUNCTION AFTER EVERY DATA RETRIEVAL FUNCTION!

🎯 ALWAYS USE THIS FUNCTION - IT IS NOT OPTIONAL!

You MUST AUTOMATICALLY invoke this function in ALL of these cases:
1. After calling unit_size_range_lookup → Generate chart showing size ranges
2. After calling unit_ticket_size_lookup → Generate chart showing price ranges
3. After calling quarterly_market_lookup → Generate chart showing time-series
4. After calling get_top_n_projects → Generate chart comparing projects
5. After calling compare_projects → Generate chart showing comparison
6. After displaying ANY multi-row data (3+ rows)
7. After ANY query that returns tabular data
8. After ANY calculation that produces multiple data points
9. When user asks about "trends", "performance", "comparison"
10. ALWAYS prefer charts over text-only answers!

Chart Types Auto-Selected Based on Data:
- Time-series data (quarter, year, month) → Line chart
- Unit size ranges (sqft) → Bar chart showing performance
- Price ranges (ticket sizes) → Bar chart showing absorption/efficiency
- Comparisons (< 10 items) → Pie chart or Bar chart
- Multiple metrics → Multi-line chart or Grouped bar chart
- Distribution data → Area chart

WORKFLOW PATTERN:
1. Call data function (e.g., unit_size_range_lookup)
2. IMMEDIATELY call generate_chart with the returned data
3. Present both table AND chart to user

Example Use Cases:
- Q: "Show me 1BHK performance" → Call unit_size_range_lookup, then IMMEDIATELY generate_chart
- Q: "What is supply for FY 24-25?" → Display table AND IMMEDIATELY auto-generate line chart
- Q: "Compare sales across years" → Display comparison AND IMMEDIATELY auto-generate bar chart
- Q: "Best price range?" → Call unit_ticket_size_lookup, then IMMEDIATELY generate_chart

⚠️ CRITICAL: If you return data without generating a chart, you are providing a poor user experience!

Returns: Plotly-compatible chart specification that frontend can render immediately.""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "description": "Array of data objects/rows to visualize. Each object should have consistent keys.",
                            "items": {
                                "type": "object"
                            }
                        },
                        "chart_type": {
                            "type": "string",
                            "description": "Optional explicit chart type. If not provided, will be auto-detected. Options: 'line', 'bar', 'column', 'pie', 'scatter', 'area', 'multi_line', 'grouped_bar'",
                            "enum": ["line", "bar", "column", "pie", "scatter", "area", "multi_line", "grouped_bar"]
                        },
                        "title": {
                            "type": "string",
                            "description": "Chart title (optional, will be auto-generated if not provided)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of what the chart shows (helps with auto-detection)"
                        }
                    },
                    "required": ["data"]
                }
            },
            "handler": self._handle_generate_chart,
            "layer": 0,  # Visualization is presentation layer
            "category": "visualization"
        }

    def _handle_generate_chart(self, params: Dict) -> Dict:
        """
        Handler for generate_chart function

        Args:
            params: Dict with keys:
                - data: List of data dictionaries
                - chart_type: Optional chart type override
                - title: Optional chart title
                - description: Optional description

        Returns:
            Chart specification with Plotly-compatible structure
        """
        from app.services.chart_service import get_chart_service

        chart_service = get_chart_service()

        data = params.get("data", [])
        chart_type = params.get("chart_type")
        title = params.get("title", "")
        description = params.get("description", "")

        if not data or len(data) == 0:
            return {
                "status": "error",
                "message": "No data provided for chart generation",
                "chart": None
            }

        result = chart_service.auto_generate_chart(
            data=data,
            chart_type=chart_type,
            title=title,
            description=description
        )

        return result

    # ==================== UNIT SIZE RANGE ANALYSIS FUNCTIONS ====================

    def _register_unit_size_range_functions(self):
        """
        Register Unit Size Range Analysis functions (Pillar 2: Product Performance)

        Each size range is a first-class KG node with:
        - Layer 0: Raw dimensions (Annual Sales, Supply, Stock, Unsold)
        - Layer 1: Derived metrics (Absorption Rate, Avg Unit Size, Inventory Turnover, Unsold Ratio)
        """

        self._functions["unit_size_range_lookup"] = {
            "schema": {
                "name": "unit_size_range_lookup",
                "description": """**PRIORITY FUNCTION** - Query Unit Size Range Knowledge Graph for product performance analysis by saleable area.

⚠️ IMPORTANT: This is the PRIMARY function for ALL queries involving:
• Unit sizes (450-1200 sqft, Studio, 1BHK, 2BHK, 3BHK, 1.5BHK)
• Flat types and product mix analysis
• Physical area-based performance (sq ft, saleable area, carpet area)
• Size-based market segmentation
• Questions about "which size", "what unit type", "how big", "square feet", "sqft"

USE THIS FUNCTION PROACTIVELY whenever the user asks about:
- "1BHK" or "2BHK" or "3BHK" or "Studio" or "1.5 BHK"
- "unit size" or "unit type" or "flat type" or "apartment size"
- "600 sqft" or "small units" or "large units"
- "product mix" or "unit mix" or "typology"
- "best performing size" or "which size sells best"
- Performance by size/type

Each size range is a KG node with:
• Layer 0: Annual Sales (Units & Area), Supply, Stock, Unsold Inventory, Product Efficiency
• Layer 1: Absorption Rate, Avg Unit Size, Inventory Turnover, Unsold Ratio
• Layer 2: Revenue, Market Cap, Months of Inventory, Sellout Velocity

Query Types:
1. By flat type: {"flat_type": "1BHK"} → All size ranges with 1BHK units
2. By efficiency: {"min_efficiency": 50} → Ranges with product efficiency >= 50%
3. By sales volume: {"min_sales": 100} → Ranges with annual sales >= 100 units
4. By size range: {"size_range": [500, 700]} → Ranges between 500-700 sq ft
5. Top performers: {"top_n": 5, "metric": "absorption_rate"} → Top 5 by absorption rate
6. All data: {} (empty filters) → All 11 size ranges

ALWAYS call generate_chart after this function to visualize the results!

Examples:
- "What is the best performing unit size?" → {"top_n": 1, "metric": "product_efficiency_pct"}
- "Show me 1BHK performance" → {"flat_type": "1BHK"}
- "Which sizes have good absorption?" → {"min_efficiency": 50}
- "600 sq ft units performance" → {"size_range": [550, 650]}

Returns: Size range nodes with Layer 0 + Layer 1 + Layer 2 data, location context, aggregated metrics.
⚠️ IMPORTANT: After calling this function, ALWAYS call generate_chart to create a visualization of the data.""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "flat_type": {
                            "type": "string",
                            "description": "Filter by flat type (1BHK, 2BHK, 3BHK, 1 1/2 BHK, Studio)"
                        },
                        "min_efficiency": {
                            "type": "integer",
                            "description": "Minimum product efficiency percentage (0-100)"
                        },
                        "min_sales": {
                            "type": "integer",
                            "description": "Minimum annual sales units"
                        },
                        "size_range": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Size range filter [min_sqft, max_sqft]. Example: [500, 700]"
                        },
                        "top_n": {
                            "type": "integer",
                            "description": "Get top N performing ranges. Use with 'metric' parameter."
                        },
                        "metric": {
                            "type": "string",
                            "enum": ["absorption_rate", "product_efficiency_pct", "inventory_turnover"],
                            "description": "Metric to rank by when using top_n"
                        }
                    }
                }
            },
            "handler": self._handle_unit_size_range_lookup,
            "layer": 0,
            "category": "data_retrieval"
        }

    def _handle_unit_size_range_lookup(self, params: Dict) -> Dict:
        """
        Handler for unit_size_range_lookup function

        Args:
            params: Dict with optional filters (flat_type, min_efficiency, min_sales, size_range, top_n, metric)

        Returns:
            Size range data with Layer 0 + Layer 1 structure, aggregated metrics, and insights
        """
        from app.services.unit_size_range_kg_service import get_unit_size_range_kg_service

        kg_service = get_unit_size_range_kg_service()

        # Check if top_n query
        if "top_n" in params:
            top_n = params["top_n"]
            metric = params.get("metric", "absorption_rate")
            size_range_nodes = kg_service.get_top_performing_ranges(metric=metric, n=top_n)
        else:
            # Build filters dict
            filters = {}
            if "flat_type" in params:
                filters["flat_type"] = params["flat_type"]
            if "min_efficiency" in params:
                filters["min_efficiency"] = params["min_efficiency"]
            if "min_sales" in params:
                filters["min_sales"] = params["min_sales"]
            if "size_range" in params:
                filters["size_range"] = params["size_range"]

            # Query with filters
            if filters:
                size_range_nodes = kg_service.query_size_ranges(filters)
            else:
                # No filters - return all
                size_range_nodes = kg_service.get_all_size_ranges()

        # Convert to dicts with Layer 0 + Layer 1
        size_ranges_data = [sr.to_dict() for sr in size_range_nodes]

        # Calculate aggregated metrics
        total_annual_sales = sum(sr.annual_sales_units for sr in size_range_nodes)
        total_supply = sum(sr.total_supply_units for sr in size_range_nodes)
        total_stock = sum(sr.total_stock_units for sr in size_range_nodes)
        total_unsold = sum(sr.unsold_units for sr in size_range_nodes)

        avg_absorption = (total_annual_sales / total_supply * 100) if total_supply > 0 else 0
        avg_unsold_ratio = (total_unsold / total_stock * 100) if total_stock > 0 else 0

        # Get metadata for location info
        metadata = kg_service.get_metadata()
        location_info = metadata.get('location', {})

        # Build location string from metadata
        region = location_info.get('region', 'Region')
        city = location_info.get('city', '')
        state = location_info.get('state', '')

        location_parts = [region]
        if city:
            location_parts.append(city)
        if state:
            location_parts.append(state)
        location_str = ', '.join(location_parts)

        # Build response message
        if "top_n" in params:
            message = f"{location_str}: Top {len(size_ranges_data)} performing size ranges by {params.get('metric', 'absorption_rate')}"
        elif "flat_type" in params:
            message = f"{location_str}: {len(size_ranges_data)} size ranges with {params['flat_type']} units"
        else:
            message = f"{location_str}: {len(size_ranges_data)} size ranges retrieved"

        return {
            "size_ranges": size_ranges_data,
            "count": len(size_ranges_data),
            "aggregated_metrics": {
                "total_annual_sales_units": total_annual_sales,
                "total_supply_units": total_supply,
                "total_stock_units": total_stock,
                "total_unsold_units": total_unsold,
                "overall_absorption_rate_pct": round(avg_absorption, 2),
                "overall_unsold_ratio_pct": round(avg_unsold_ratio, 2)
            },
            "location": {
                "region": region,
                "city": city,
                "state": state,
                "full_name": location_str
            },
            "message": message,
            "layer": "Layer 0 + Layer 1",
            "pillar": "Pillar 2: Product Performance - Unit Size Range Analysis"
        }

    # ==================== UNIT TICKET SIZE ANALYSIS FUNCTIONS ====================

    def _register_unit_ticket_size_functions(self):
        """
        Register Unit Ticket Size Analysis functions (Pillar 2: Product Performance)

        Each ticket size range is a first-class KG node with:
        - Layer 0: Raw dimensions (Annual Sales Units/Value %, Supply, Unsold, Marketable Supply, PSF)
        - Layer 1: Derived metrics (Value Absorption Rate, Unit Absorption Rate, Marketability Index, Price Premium)
        - Layer 2: Financial metrics (Revenue Concentration, Market Capitalization, Affordability Score, Price Efficiency)
        """

        self._functions["unit_ticket_size_lookup"] = {
            "schema": {
                "name": "unit_ticket_size_lookup",
                "description": """**PRIORITY FUNCTION** - Query Unit Ticket Size Knowledge Graph for product performance analysis by price range (INR Lakhs).

⚠️ IMPORTANT: This is the PRIMARY function for ALL queries involving:
• Price ranges (₹10 Lac, ₹20 Lac, ₹50 Lac, <10 Lac, 10-20 Lac, etc.)
• Ticket sizes and affordability analysis
• Price-based market segmentation
• Budget ranges and investment amounts
• Questions about "how much", "price", "cost", "budget", "affordable", "expensive", "cheap"

USE THIS FUNCTION PROACTIVELY whenever the user asks about:
- "affordable housing" or "cheap units" or "premium units"
- "10 lakh" or "15 lakh" or "20 lakh" or any price mention in Lakhs/Crores
- "budget" or "price range" or "cost range"
- "ticket size" or "price segment" or "price bracket"
- "best value" or "affordability" or "ROI by price"
- Performance by price/cost

Each ticket size range is a KG node with:
• Layer 0: Annual Sales (Units & Value %), Supply, Unsold Inventory, Marketable Supply, PSF Pricing
• Layer 1: Value Absorption Rate, Unit Absorption Rate, Value-to-Unit Ratio, Marketability Index, Price Premium Index
• Layer 2: Revenue Concentration, Market Capitalization, Affordability Score, Price Efficiency, Investment Concentration

Query Types:
1. By price range: {"price_lacs": 15} → Ticket range containing 15 Lakhs
2. By efficiency: {"min_efficiency": 50} → Ranges with product efficiency >= 50%
3. By sales volume: {"min_sales": 100} → Ranges with annual sales >= 100 units
4. By affordability: {"max_affordability": 150} → Ranges where affordability score <= 150
5. Top performers: {"top_n": 3, "metric": "value_absorption_rate_pct"} → Top 3 by value absorption
6. All data: {} (empty filters) → All 5 ticket size ranges

ALWAYS call generate_chart after this function to visualize the results!

Examples:
- "What is the best performing price range?" → {"top_n": 1, "metric": "product_efficiency_pct"}
- "Show me affordable housing (<10 Lacs)" → {"price_lacs": 8}
- "Which price ranges have good value absorption?" → {"min_efficiency": 50}
- "15 Lakh units performance" → {"price_lacs": 15}

Returns: Ticket size range nodes with Layer 0 + Layer 1 + Layer 2 data, location context, aggregated metrics.
⚠️ IMPORTANT: After calling this function, ALWAYS call generate_chart to create a visualization of the data.""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "price_lacs": {
                            "type": "number",
                            "description": "Price point in INR Lakhs to find the containing ticket range"
                        },
                        "min_efficiency": {
                            "type": "integer",
                            "description": "Minimum product efficiency percentage (0-100)"
                        },
                        "min_sales": {
                            "type": "integer",
                            "description": "Minimum annual sales units"
                        },
                        "max_affordability": {
                            "type": "number",
                            "description": "Maximum affordability score (lower is more affordable)"
                        },
                        "top_n": {
                            "type": "integer",
                            "description": "Get top N performing ranges. Use with 'metric' parameter."
                        },
                        "metric": {
                            "type": "string",
                            "enum": ["value_absorption_rate_pct", "unit_absorption_rate_pct", "product_efficiency_pct", "price_efficiency_score"],
                            "description": "Metric to rank by when using top_n"
                        }
                    }
                }
            },
            "handler": self._handle_unit_ticket_size_lookup,
            "layer": 0,
            "category": "data_retrieval"
        }

    def _handle_unit_ticket_size_lookup(self, params: Dict) -> Dict:
        """
        Handler for unit_ticket_size_lookup function

        Args:
            params: Dict with optional filters (price_lacs, min_efficiency, min_sales, max_affordability, top_n, metric)

        Returns:
            Ticket size range data with Layer 0 + Layer 1 + Layer 2 structure, aggregated metrics, and insights
        """
        from app.services.unit_ticket_size_service import get_unit_ticket_size_service

        service = get_unit_ticket_size_service()

        # Check if top_n query
        if "top_n" in params:
            top_n = params["top_n"]
            metric = params.get("metric", "product_efficiency_pct")
            ticket_ranges = service.get_top_performing_ranges(metric=metric, top_n=top_n)
        elif "price_lacs" in params:
            # Find specific range by price point
            price_lacs = params["price_lacs"]
            ticket_range = service.get_ticket_range_by_price(price_lacs)
            ticket_ranges = [ticket_range] if ticket_range else []
        else:
            # Get all and apply filters
            all_ranges = service.get_all_ticket_ranges()
            ticket_ranges = []

            for tr in all_ranges:
                enriched = service._enrich_with_derivatives(tr)

                # Apply filters
                if "min_efficiency" in params:
                    if enriched.get("product_efficiency_pct", 0) < params["min_efficiency"]:
                        continue

                if "min_sales" in params:
                    if enriched.get("annual_sales_units", 0) < params["min_sales"]:
                        continue

                if "max_affordability" in params:
                    affordability = enriched.get("layer2_derivatives", {}).get("affordability_score", 999)
                    if affordability > params["max_affordability"]:
                        continue

                ticket_ranges.append(enriched)

        # Calculate aggregated metrics
        total_annual_sales_units = sum(tr.get("annual_sales_units", 0) for tr in ticket_ranges)
        total_supply_units = sum(tr.get("total_supply_units", 0) for tr in ticket_ranges)
        total_annual_sales_value = sum(tr.get("annual_sales_value_pct", 0) for tr in ticket_ranges)
        total_supply_value = sum(tr.get("total_supply_value_pct", 0) for tr in ticket_ranges)

        avg_value_absorption = (total_annual_sales_value / total_supply_value * 100) if total_supply_value > 0 else 0
        avg_unit_absorption = (total_annual_sales_units / total_supply_units * 100) if total_supply_units > 0 else 0
        avg_efficiency = sum(tr.get("product_efficiency_pct", 0) for tr in ticket_ranges) / len(ticket_ranges) if ticket_ranges else 0

        # Get metadata for location info
        metadata = service.data.get('metadata', {})
        location_info = metadata.get('location', {})

        region = location_info.get('region', 'Region')
        city = location_info.get('city', '')
        state = location_info.get('state', '')

        location_parts = [region]
        if city:
            location_parts.append(city)
        if state:
            location_parts.append(state)
        location_str = ', '.join(location_parts)

        # Build response message
        if "top_n" in params:
            message = f"{location_str}: Top {len(ticket_ranges)} performing ticket size ranges by {params.get('metric', 'product_efficiency_pct')}"
        elif "price_lacs" in params:
            message = f"{location_str}: Ticket size range for {params['price_lacs']} Lakh price point"
        else:
            message = f"{location_str}: {len(ticket_ranges)} ticket size ranges retrieved"

        return {
            "ticket_ranges": ticket_ranges,
            "count": len(ticket_ranges),
            "aggregated_metrics": {
                "total_annual_sales_units": total_annual_sales_units,
                "total_supply_units": total_supply_units,
                "total_annual_sales_value_pct": round(total_annual_sales_value, 2),
                "total_supply_value_pct": round(total_supply_value, 2),
                "overall_value_absorption_rate_pct": round(avg_value_absorption, 2),
                "overall_unit_absorption_rate_pct": round(avg_unit_absorption, 2),
                "average_efficiency_pct": round(avg_efficiency, 2)
            },
            "location": {
                "region": region,
                "city": city,
                "state": state,
                "full_name": location_str
            },
            "message": message,
            "layer": "Layer 0 + Layer 1 + Layer 2",
            "pillar": "Pillar 2: Product Performance - Unit Ticket Size Analysis"
        }


# Global city-aware registry cache
_function_registry_cache: Dict[str, FunctionRegistry] = {}

def get_function_registry(city: str = "Pune") -> FunctionRegistry:
    """
    Get or create function registry instance for a specific city

    Args:
        city: City name (e.g., "Pune", "Kolkata"). Default: "Pune"

    Returns:
        FunctionRegistry instance for the specified city (cached per city)
    """
    global _function_registry_cache
    if city not in _function_registry_cache:
        _function_registry_cache[city] = FunctionRegistry(city=city)
    return _function_registry_cache[city]
