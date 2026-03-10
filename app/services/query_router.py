"""
Query Router: Routes MCP queries to appropriate layer handlers
"""
from typing import Dict, Tuple, Any, Optional
from datetime import datetime
import uuid
from app.models.requests import MCPQueryRequest
from app.models.domain import FinancialProjection
from app.calculators.layer0 import Layer0Handler
from app.calculators.layer1 import Layer1Calculator
from app.calculators.layer2 import Layer2Calculator
from app.calculators.layer3 import Layer3Optimizer
from app.calculators.layer4 import Layer4Calculator
from app.services.data_service import data_service
from app.services.statistical_service import statistical_service
from app.config.defaults import defaults
from app.services.prompt_router import prompt_router, LayerType


class QueryRouter:
    """Route MCP queries to appropriate layer handlers"""

    def __init__(self):
        self.layer0 = Layer0Handler()
        self.layer1 = Layer1Calculator()
        self.layer2 = Layer2Calculator()
        self.layer3 = Layer3Optimizer()
        self.layer4 = Layer4Calculator()

    def route(self, request: MCPQueryRequest) -> Tuple[Dict, Dict, Dict]:
        """
        Route query to appropriate layer handler

        Returns:
            Tuple of (result, provenance, lineage)
        """
        if request.layer == 0:
            return self._handle_layer0(request)
        elif request.layer == 1:
            return self._handle_layer1(request)
        elif request.layer == 2:
            return self._handle_layer2(request)
        elif request.layer == 3:
            return self._handle_layer3(request)
        elif request.layer == 4:
            return self._handle_layer4(request)
        else:
            raise ValueError(f"Invalid layer: {request.layer}")

    def route_from_prompt(self, prompt: str, context: Optional[Dict] = None) -> Tuple[Dict, Dict, Dict]:
        """
        Dynamically route a natural language prompt to the appropriate handler

        Args:
            prompt: Natural language query
            context: Optional context dictionary

        Returns:
            Tuple of (result, provenance, lineage)
        """
        # Analyze prompt to determine routing
        route_decision = prompt_router.analyze_prompt(prompt)

        # Create request based on routing decision
        request = MCPQueryRequest(
            queryType="calculation",  # Default, can be refined
            layer=route_decision.layer.value,
            capability=route_decision.capability,
            parameters={},  # Would need to be extracted from prompt
            context=context or {}
        )

        # Log routing decision for transparency
        routing_metadata = {
            "prompt": prompt,
            "routed_to": route_decision.capability,
            "layer": route_decision.layer.value,
            "confidence": route_decision.confidence,
            "reason": route_decision.reason,
            "requires_vector": route_decision.requires_vector_search
        }

        # Route to appropriate handler
        result, provenance, lineage = self.route(request)

        # Add routing metadata to provenance
        provenance["routing"] = routing_metadata

        return result, provenance, lineage

    def _handle_layer0(self, request: MCPQueryRequest) -> Tuple[Dict, Dict, Dict]:
        """Handle Layer 0 queries"""
        capability = request.capability
        params = request.parameters

        if capability == "get_project_dimensions":
            project_id = params.get("projectId")
            if not project_id:
                raise ValueError("projectId required for get_project_dimensions")

            project = data_service.get_project(project_id)
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            result = self.layer0.get_project_dimensions(project)

            provenance = {
                "inputDimensions": ["U", "L2", "T", "CF"],
                "calculationMethod": "Direct fetch from data source (Layer 0)",
                "lfSource": "Project master data",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "dataVersion": request.context.get("lfDataVersion", defaults.get_current_data_version()),
                "layer": 0
            }

            lineage = {"layer0_inputs": result["dimensions"]}

            return result, provenance, lineage

        else:
            raise ValueError(f"Unknown Layer 0 capability: {capability}")

    def _handle_layer1(self, request: MCPQueryRequest) -> Tuple[Dict, Dict, Dict]:
        """Handle Layer 1 queries"""
        capability = request.capability
        params = request.parameters

        if capability == "calculate_psf":
            result = self.layer1.calculate_psf(
                total_revenue=params["totalRevenue"],
                saleable_area=params["saleableArea"]
            )
            lf_source = "Pillar_1.1"

        elif capability == "calculate_asp":
            result = self.layer1.calculate_asp(
                total_revenue=params["totalRevenue"],
                total_units=params["totalUnits"]
            )
            lf_source = "Pillar_2.1"

        elif capability == "calculate_absorption_rate":
            result = self.layer1.calculate_absorption_rate(
                units_sold=params["unitsSold"],
                total_units=params["totalUnits"],
                months_elapsed=params["monthsElapsed"]
            )
            lf_source = "Pillar_1.2"

        elif capability == "calculate_sales_velocity":
            result = self.layer1.calculate_sales_velocity(
                units_sold=params["unitsSold"],
                months_elapsed=params["monthsElapsed"]
            )
            lf_source = "Pillar_1.2"

        else:
            # Try enriched Layer 1 calculator
            try:
                from app.services.enriched_calculator import get_enriched_calculator
                from app.services.enriched_layers_service import get_enriched_layers_service

                # Check if this is an enriched Layer 1 attribute
                enriched_service = get_enriched_layers_service()
                attr_name = capability.replace('calculate_', '').replace('_', ' ').title()
                attr = enriched_service.get_attribute(attr_name)

                if attr and not attr.requires_calculation:
                    # This is Layer 0 (direct extraction), not Layer 1 calculation
                    # Fall back to Layer 0 extraction from Neo4j
                    from app.services.layer0 import Layer0Service

                    layer0_service = Layer0Service()
                    project_name = params.get("projectName") or request.context.get("project_name")

                    if not project_name:
                        raise ValueError("projectName required for Layer 0 extraction")

                    # Map attribute name to Neo4j field
                    field_mapping = {
                        'Monthly Sales Velocity': 'monthlySalesVelocity',
                        'Sales Velocity': 'monthlySalesVelocity',
                    }

                    field_name = field_mapping.get(attr.target_attribute, attr.target_attribute.replace(' ', ''))
                    project_data = layer0_service.get_project_by_name(project_name)

                    if not project_data:
                        raise ValueError(f"Project '{project_name}' not found")

                    # Extract the field value
                    field_value = project_data.get(field_name, {})
                    if isinstance(field_value, dict):
                        value = field_value.get('value')
                        unit = field_value.get('unit', attr.unit)
                    else:
                        value = field_value
                        unit = attr.unit

                    # Format as standard result
                    result = {
                        "metric": attr.target_attribute,
                        "value": value,
                        "unit": unit,
                        "dimension": attr.dimension,
                        "formula": "Direct extraction from Neo4j",
                        "components": {}
                    }

                    # Create provenance for Layer 0 extraction
                    provenance = {
                        "metric": attr.target_attribute,
                        "inputDimensions": ["Layer 0 - Neo4j"],
                        "calculationMethod": "Direct extraction",
                        "lfSource": "Liases Foras Knowledge Graph",
                        "timestamp": datetime.now().isoformat(),
                        "dataVersion": request.context.get("lfDataVersion", "Q3_FY25"),
                        "layer": "Layer 0",
                        "description": attr.description
                    }

                    lineage = {"layer0_direct": True}

                    return result, provenance, lineage

                elif attr and attr.requires_calculation:
                    # Use enriched calculator
                    calculator = get_enriched_calculator()
                    project_name = params.get("projectName") or request.context.get("project_name")
                    project_id = params.get("projectId") or request.context.get("project_id")

                    if not project_name and not project_id:
                        raise ValueError("projectName or projectId required for enriched calculations")

                    calc_result = calculator.calculate(capability, project_name, project_id)

                    # Format as standard result
                    result = {
                        "metric": attr.target_attribute,
                        "value": calc_result["value"],
                        "unit": calc_result["unit"],
                        "dimension": calc_result["dimension"],
                        "formula": calc_result["formula"],
                        "components": {}  # Enriched calculations don't expose components
                    }

                    # Create provenance for enriched calculation
                    provenance = {
                        "metric": attr.target_attribute,
                        "inputDimensions": ["Enriched Layer 1"],
                        "calculationMethod": calc_result["formula"],
                        "lfSource": "Enriched Layers",
                        "timestamp": datetime.now().isoformat(),
                        "dataVersion": request.context.get("lfDataVersion", "enriched_v3"),
                        "layer": "Layer 1",
                        "description": calc_result.get("provenance", {}).get("description", "")
                    }

                    lineage = {"layer1_inputs": {"enriched": True}}

                    return result, provenance, lineage

                else:
                    raise ValueError(f"Unknown Layer 1 capability: {capability}")

            except ImportError:
                raise ValueError(f"Unknown Layer 1 capability: {capability}")

        provenance = self.layer1.create_provenance(
            metric_name=result["metric"],
            input_dimensions=list(result["components"].keys()),
            lf_source=lf_source,
            data_version=request.context.get("lfDataVersion", defaults.get_current_data_version())
        )

        lineage = {"layer1_inputs": result["components"]}

        return result, provenance, lineage

    def _handle_layer2(self, request: MCPQueryRequest) -> Tuple[Dict, Dict, Dict]:
        """Handle Layer 2 queries"""
        capability = request.capability
        params = request.parameters

        # Create projection from parameters using config defaults
        projection = FinancialProjection(
            initial_investment=params.get("initialInvestment",
                                        defaults.get_default("financial", "initial_investment")),
            annual_cash_flows=params.get("cashFlows", []),
            discount_rate=params.get("discountRate",
                                   defaults.get_default("financial", "discount_rate")),
            project_duration_years=len(params.get("cashFlows", []))
        )

        if capability == "calculate_npv":
            npv = self.layer2.calculate_npv(projection)
            result = {
                "metric": "NPV",
                "value": round(npv, 2),
                "unit": "INR",
                "dimension": "CF",
                "formula": "∑[CF_t / (1+r)^t] - Initial_Investment"
            }
            algorithm = "Direct calculation"

        elif capability == "calculate_irr":
            irr = self.layer2.calculate_irr(projection)
            result = {
                "metric": "IRR",
                "value": round(irr * 100, 2) if irr else None,
                "unit": "%/year",
                "dimension": "T^-1",
                "formula": "r where NPV(r) = 0"
            }
            algorithm = "Newton's method (scipy.optimize.newton)"

        elif capability == "calculate_payback_period":
            pbp = self.layer2.calculate_payback_period(projection)
            result = {
                "metric": "PaybackPeriod",
                "value": round(pbp, 2) if pbp else None,
                "unit": "years",
                "dimension": "T",
                "formula": "Time when cumulative CF = Initial_Investment"
            }
            algorithm = "Iterative accumulation"

        elif capability == "calculate_sensitivity_analysis":
            sensitivity = self.layer2.calculate_sensitivity_analysis(
                projection,
                absorption_range=params.get("absorptionRange",
                                          defaults.get_default("financial", "absorption_range")),
                price_range=params.get("priceRange",
                                      defaults.get_default("financial", "price_range"))
            )
            result = sensitivity
            algorithm = "Scenario modeling with parameter variation"

        elif capability == "calculate_statistics":
            # Statistical analysis of series data
            values = params.get("values", [])
            operations = params.get("operations")
            metric_name = params.get("metric_name", "metric")
            context = params.get("context", "real_estate")

            stats_result = statistical_service.calculate_series_statistics(
                values=values,
                operations=operations,
                metric_name=metric_name,
                context=context
            )

            result = {
                "capability": "calculate_statistics",
                "analysis": stats_result
            }
            algorithm = "Statistical analysis with scipy/numpy"

        elif capability == "aggregate_by_region":
            # Regional aggregation with statistics
            region = params.get("region")
            city = params.get("city")
            attribute_path = params.get("attribute_path")
            attribute_name = params.get("attribute_name")

            if not region or not attribute_path:
                raise ValueError("region and attribute_path required for aggregate_by_region")

            agg_result = statistical_service.aggregate_by_region(
                region=region,
                city=city,
                attribute_path=attribute_path,
                attribute_name=attribute_name
            )

            result = {
                "capability": "aggregate_by_region",
                "aggregation": agg_result
            }
            algorithm = "Regional aggregation with statistical summary"

        elif capability == "get_top_n_projects":
            # Top N projects by attribute
            region = params.get("region")
            city = params.get("city")
            attribute_path = params.get("attribute_path")
            attribute_name = params.get("attribute_name")
            n = params.get("n", 5)
            ascending = params.get("ascending", False)

            if not region or not city or not attribute_path:
                raise ValueError("region, city, and attribute_path required for get_top_n_projects")

            top_n_result = statistical_service.get_top_n_projects(
                region=region,
                city=city,
                attribute_path=attribute_path,
                attribute_name=attribute_name,
                n=n,
                ascending=ascending
            )

            result = {
                "capability": "get_top_n_projects",
                "ranking": top_n_result
            }
            algorithm = "Sorting and ranking algorithm"

        else:
            raise ValueError(f"Unknown Layer 2 capability: {capability}")

        provenance = self.layer2.create_provenance(
            metric_name=result.get("metric", capability),
            algorithm=algorithm,
            lf_source="Pillar_4.3",
            data_version=request.context.get("lfDataVersion", defaults.get_current_data_version())
        )

        lineage = {
            "layer0_inputs": {"initialInvestment": projection.initial_investment},
            "layer1_intermediates": ["cashFlows"],
            "layer2_dependencies": []
        }

        return result, provenance, lineage

    def _handle_layer3(self, request: MCPQueryRequest) -> Tuple[Dict, Dict, Dict]:
        """Handle Layer 3 queries"""
        capability = request.capability
        params = request.parameters

        if capability == "optimize_product_mix":
            location = params.get("location")  # No default - must be provided
            if not location:
                raise ValueError("location is required for optimize_product_mix")

            # Get market data
            market_data = data_service.get_market_data_for_optimization(location)

            # Get developer marketability from config
            developer_marketability = params.get("developerMarketability",
                                                defaults.get_default("optimization", "developer_marketability"))

            result = self.layer3.optimize_product_mix(
                total_units=params["totalUnits"],
                total_land_area_sqft=params["totalArea"],
                total_project_cost=params.get("totalProjectCost",
                                             defaults.get_default("financial", "total_project_cost")),
                project_duration_months=params.get("projectDuration_months",
                                                  defaults.get_default("financial", "project_duration_months")),
                market_data=market_data,
                developer_marketability=developer_marketability
            )

            provenance = self.layer3.create_provenance(
                capability="optimize_product_mix",
                lf_pillars=["2.1", "4.1", "4.3"],
                algorithm="scipy.optimize.minimize with SLSQP method",
                data_version=request.context.get("lfDataVersion", defaults.get_current_data_version())
            )

        elif capability == "market_opportunity_scoring":
            location = params.get("location")
            if not location:
                return {"error": "Location is required for market opportunity scoring"}
            unit_types = params.get("unitTypes", ["1BHK", "2BHK", "3BHK"])

            lf_market_data = data_service.get_lf_market_data(location)

            result = self.layer3.market_opportunity_scoring(
                location=location,
                unit_types=unit_types,
                lf_market_data=lf_market_data.get('micromarket_eval', {})
            )

            provenance = self.layer3.create_provenance(
                capability="market_opportunity_scoring",
                lf_pillars=["1.3", "3.3"],
                algorithm="OPPS scoring algorithm",
                data_version=request.context.get("lfDataVersion", defaults.get_current_data_version())
            )

        else:
            raise ValueError(f"Unknown Layer 3 capability: {capability}")

        lineage = {
            "layer0_inputs": {
                "totalUnits": params.get("totalUnits"),
                "totalArea": params.get("totalArea")
            },
            "layer1_intermediates": ["absorptionRates", "prices"],
            "layer2_dependencies": ["NPV", "IRR"]
        }

        return result, provenance, lineage

    def _handle_layer4(self, request: MCPQueryRequest) -> Tuple[Dict, Dict, Dict]:
        """Handle Layer 4 queries (Market Insights & Context)"""
        capability = request.capability
        params = request.parameters

        if capability == "get_market_insights":
            # Get comprehensive market insights for a location
            city = params.get("city")
            locality = params.get("locality")
            price_psf = params.get("pricePsf")
            project_type = params.get("projectType")

            if not city or not locality:
                raise ValueError("city and locality required for get_market_insights")

            insights = self.layer4.get_market_insights(
                city=city,
                locality=locality,
                price_psf=price_psf,
                project_type=project_type
            )

            result = {
                "capability": "get_market_insights",
                "city": city,
                "locality": locality,
                "insights": insights
            }

            provenance = {
                "layer": 4,
                "capability": "get_market_insights",
                "algorithm": "RAG (Retrieval-Augmented Generation) with semantic search",
                "vectorDB": "ChromaDB with sentence-transformers/all-MiniLM-L6-v2",
                "dataSource": "City market reports vector database",
                "chunksIndexed": 54,
                "cities": ["Mumbai", "Pune"],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            lineage = {
                "layer4_sources": {
                    "city_overview": insights.get("city_overview", {}).get("source"),
                    "locality_insights": len(insights.get("locality_insights", {}).get("related", [])),
                    "infrastructure": bool(insights.get("infrastructure")),
                    "future_outlook": bool(insights.get("future_outlook"))
                }
            }

        elif capability == "enrich_irr_calculation":
            # Enrich IRR calculation with market context
            irr_result = params.get("irrResult")
            city = params.get("city")
            locality = params.get("locality")

            if not irr_result or not city or not locality:
                raise ValueError("irrResult, city, and locality required for enrich_irr_calculation")

            enriched = self.layer4.enrich_irr_calculation(
                irr_result=irr_result,
                city=city,
                locality=locality
            )

            result = enriched

            provenance = {
                "layer": 4,
                "capability": "enrich_irr_calculation",
                "algorithm": "IRR enrichment with RAG market context",
                "vectorDB": "ChromaDB",
                "dataSource": "City market reports",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            lineage = {
                "layer2_inputs": {"irr": irr_result.get("value")},
                "layer4_enrichment": {
                    "city_context": bool(enriched.get("market_insights", {}).get("city_context")),
                    "locality_context": bool(enriched.get("market_insights", {}).get("locality_context")),
                    "comparables": len(enriched.get("market_insights", {}).get("comparable_projects", []))
                }
            }

        elif capability == "semantic_search":
            # Perform semantic search over city insights
            query = params.get("query")
            city = params.get("city")
            section_type = params.get("sectionType")
            n_results = params.get("nResults", 5)

            if not query:
                raise ValueError("query required for semantic_search")

            search_results = self.layer4.vector_db.semantic_search(
                query=query,
                city=city,
                section_type=section_type,
                n_results=n_results
            )

            result = {
                "capability": "semantic_search",
                "query": query,
                "city": city,
                "results": search_results,
                "resultsCount": len(search_results)
            }

            provenance = {
                "layer": 4,
                "capability": "semantic_search",
                "algorithm": "Cosine similarity search with embeddings",
                "vectorDB": "ChromaDB",
                "embeddingModel": "sentence-transformers/all-MiniLM-L6-v2",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            lineage = {
                "layer4_search": {
                    "query": query,
                    "filters": {"city": city, "section_type": section_type},
                    "results_retrieved": len(search_results)
                }
            }

        else:
            raise ValueError(f"Unknown Layer 4 capability: {capability}")

        return result, provenance, lineage


# Global query router instance
query_router = QueryRouter()
