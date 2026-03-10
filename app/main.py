"""
Main FastAPI Application
Liases Foras Real Estate Analytics MCP API
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from app.api import mcp_info, mcp_query, conversation
from app.services.data_service import data_service
from app.services.knowledge_graph_service import knowledge_graph_service
from app.services.llm_service import get_llm_service
from app.services.context_service import get_context_service
from app.services.document_vector_service import get_document_vector_service
from app.services.data_refresh_service import get_data_refresh_service
from app.services.orchestrator_service import get_orchestrator

# Optional: SIRRUS LangChain Service (may have import issues with langchain-google-genai)
try:
    from app.services.sirrus_langchain_service import get_sirrus_service
    SIRRUS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  SIRRUS LangChain service not available: {e}")
    SIRRUS_AVAILABLE = False
    get_sirrus_service = None

from app.calculators.layer4 import Layer4Calculator
from app.config import settings

# Create FastAPI app
app = FastAPI(
    title="Liases Foras Real Estate Analytics MCP",
    description="Four-layer dimensional knowledge graph with MCP API for real estate financial analysis",
    version="2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class LocationContext(BaseModel):
    region: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None

class QuestionRequest(BaseModel):
    question: str
    project_id: Optional[str] = None
    location_context: Optional[LocationContext] = None
    admin_mode: Optional[bool] = False  # If True, returns rich HTML tables; if False, returns GPT-like markdown

# Include routers
app.include_router(mcp_info.router, prefix="/api/mcp", tags=["MCP"])
app.include_router(mcp_query.router, prefix="/api/mcp", tags=["MCP"])
app.include_router(conversation.router, tags=["Conversation"])

# Query Handler - Simple Query Handler (uses DataService, NOT Neo4j)
try:
    from app.services.simple_query_handler import router as simple_query_router
    app.include_router(simple_query_router, tags=["Query"])
except ImportError:
    pass  # simple_query_handler not yet available

# ATLAS v4 - LangGraph Implementation
try:
    from app.api.v4 import router as atlas_v4_router
    app.include_router(atlas_v4_router, tags=["ATLAS v4"])
except ImportError:
    pass  # ATLAS v4 not yet available

# Hexagonal Architecture - LangGraph Orchestrator with Ports & Adapters
try:
    from app.api.hexagonal import router as hexagonal_router
    app.include_router(hexagonal_router, tags=["Hexagonal Architecture"])
except ImportError:
    pass  # Hexagonal architecture not yet available

# UltraThink Auto-Healing Testing System
try:
    from app.api.ultrathink import router as ultrathink_router
    app.include_router(ultrathink_router, tags=["UltraThink Testing"])
except ImportError:
    pass  # UltraThink testing not yet available

# ATLAS Hybrid Router - Interactions API with Intelligent Routing
try:
    from app.api.atlas_hybrid import router as atlas_hybrid_router
    app.include_router(atlas_hybrid_router, prefix="/api/atlas/hybrid", tags=["ATLAS Hybrid Router"])
except ImportError:
    pass  # ATLAS Hybrid Router not yet available


@app.get("/")
def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "service": "Liases Foras Real Estate Analytics",
        "version": "2.0",
        "architecture": "4-layer dimensional knowledge graph",
        "endpoints": {
            "mcp_info": "/api/mcp/info",
            "mcp_query": "/api/mcp/query",
            "unified_query": "/api/query/unified (Dimensional analysis with dynamic layer creation)",
            "qa_question": "/api/qa/question",
            "qa_summary": "/api/qa/summary",
            "context_location": "/api/context/location",
            "context_region": "/api/context/region",
            "context_catchment": "/api/context/catchment",
            "context_city_insights": "/api/context/city-insights",
            "projects": "/api/projects",
            "project_l2_metrics": "/api/projects/{id}/l2-metrics (NON-LLM)",
            "project_insights": "/api/projects/{id}/insights (NON-LLM L3)",
            "data_status": "/api/data/status",
            "data_refresh": "/api/data/refresh (POST)",
            "data_refresh_pdf": "/api/data/refresh/pdf (POST)",
            "knowledge_graph_dimensions": "/api/knowledge-graph/dimensions",
            "knowledge_graph_stats": "/api/knowledge-graph/stats",
            "knowledge_graph_relationships": "/api/knowledge-graph/relationships/{dimension}",
            "knowledge_graph_visualization": "/api/knowledge-graph/visualization?project_name=",
            "knowledge_graph_profile": "/api/knowledge-graph/profile/{project_name}",
            "docs": "/docs"
        }
    }


@app.get("/api/cities")
def get_cities():
    """
    Get list of available cities

    Returns list of cities configured in CITY_DATA_CONFIG
    """
    from app.config import CITY_DATA_CONFIG

    cities = []
    for city_name, config in CITY_DATA_CONFIG.items():
        cities.append({
            "name": city_name,
            "regions": config.get("regions", []),
            "default_region": config.get("default_region"),
            "data_file": config.get("data_file"),
            "format": config.get("format")
        })

    return {
        "cities": cities,
        "total": len(cities)
    }


@app.get("/api/projects")
def get_projects(city: Optional[str] = Query(None, description="City name (e.g., 'Pune', 'Kolkata')")):
    """
    Get all projects with nested structure

    Args:
        city: Optional city name. If not provided, defaults to Pune.
    """
    from app.services.data_service import get_data_service

    # Get city-specific data service
    city_data_service = get_data_service(city) if city else data_service

    projects = city_data_service.get_all_projects()
    return [{
        "projectId": int(city_data_service.get_value(p.get('projectId', {})) or 0),
        "projectName": city_data_service.get_value(p.get('projectName')),
        "location": city_data_service.get_value(p.get('location')),
        "microMarket": city_data_service.get_value(p.get('microMarket')),
        "city": city or city_data_service.city,
        "totalSupplyUnits": int(city_data_service.get_value(p.get('totalSupplyUnits', {})) or 0),
        "soldUnits": city_data_service.get_value(p.get('soldUnits')),
        "unsoldUnits": city_data_service.get_value(p.get('unsoldUnits')),
        "currentPricePSF": city_data_service.get_value(p.get('currentPricePSF')),
        "developerName": city_data_service.get_value(p.get('developerName'))
    } for p in projects]


@app.get("/api/projects/by-location")
def get_projects_by_location(location: str = Query(..., description="Location/MicroMarket name")):
    """Get all projects in a specific location/micro-market"""
    projects = data_service.get_all_projects()

    # Filter by location or microMarket (case-insensitive, handles whitespace/newlines)
    filtered_projects = []
    for p in projects:
        loc = (data_service.get_value(p.get('location', '')) or '').strip().replace('\n', ' ').lower()
        micro = (data_service.get_value(p.get('microMarket', '')) or '').strip().replace('\n', ' ').lower()
        search_term = location.strip().lower()

        # Match if search term appears in location or micromarket
        # This handles cases like "a chakan" matching "chakan"
        if search_term in loc or search_term in micro:
            filtered_projects.append(p)

    return [{
        "projectId": int(data_service.get_value(p.get('projectId', {})) or 0),
        "projectName": data_service.get_value(p.get('projectName')),
        "location": data_service.get_value(p.get('location')),
        "microMarket": data_service.get_value(p.get('microMarket')),
        "city": data_service.get_value(p.get('city')),
        "totalSupplyUnits": int(data_service.get_value(p.get('totalSupplyUnits', {})) or 0),
        "currentPricePSF": data_service.get_value(p.get('currentPricePSF')),
        "developerName": data_service.get_value(p.get('developerName')),
        "launchDate": data_service.get_value(p.get('launchDate')),
        "possessionDate": data_service.get_value(p.get('possessionDate'))
    } for p in filtered_projects]


@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    """Get project by ID (returns full nested structure)"""
    project = data_service.get_project(project_id)
    if not project:
        return {"error": f"Project not found: {project_id}"}

    return project


# Q&A Endpoints
@app.post("/api/qa/question")
def ask_question(request: QuestionRequest):
    """
    Ask a question about a project with intelligent routing

    Routes through prompt_router to detect enriched Layer 1 attributes,
    then falls back to simple query handler for other queries.

    Examples:
    - "What is sellout time for sara city?" → Enriched Layer 1 calculation (2.1 years)
    - "How long to sell remaining units?" → Months of Inventory calculation (2.79 months)
    - "Calculate the average of all project sizes" → Simple aggregation
    - "Top 5 projects by revenue" → SQL-like filtering
    """
    from app.services.v4_query_service import get_v4_service
    from app.services.simple_query_handler import SimpleQueryHandler
    from app.services.prompt_router import prompt_router, LayerType
    from app.services.enriched_calculator import get_enriched_calculator
    from app.services.enriched_layers_service import get_enriched_layers_service
    from app.services.dimension_validator import get_dimension_validator
    from app.services.dynamic_formula_service import get_dynamic_formula_service

    try:
        # Try V4QueryService first (LangGraph orchestrator with proper entity resolution)
        try:
            v4_service = get_v4_service()
            v4_result = v4_service.query(request.question)

            # Convert V4 response format to /api/qa/question format for Streamlit compatibility
            if v4_result and v4_result.get('answer'):
                # V4 returns natural language answer as string
                # Convert to dict format expected by Streamlit UI
                answer_text = v4_result.get('answer', '')

                return {
                    "status": "success",
                    "answer": {
                        "status": "success",
                        "query": request.question,
                        "understanding": {
                            "intent": v4_result.get('intent', 'unknown'),
                            "subcategory": v4_result.get('subcategory', ''),
                            "execution_path": v4_result.get('execution_path', [])
                        },
                        "result": {
                            "type": "single",
                            "text": answer_text,
                            "value": answer_text,  # For backward compatibility
                            "unit": ""
                        },
                        "calculation": {},
                        "provenance": v4_result.get('provenance', {})
                    },
                    "query": request.question
                }
        except Exception as v4_error:
            # If V4 fails, fall back to old logic
            print(f"[WARNING] V4QueryService failed: {v4_error}. Falling back to old routing logic.")

        # Fallback: Old logic with prompt_router
        # Step 1: Analyze prompt with prompt_router
        route_decision = prompt_router.analyze_prompt(request.question)

        # Step 2: If Layer 1 with decent confidence, try enriched calculator
        if route_decision.layer == LayerType.LAYER_1 and route_decision.confidence >= 0.3:
            try:
                # Use new dynamic formula service (Excel-driven, no hardcoded calculators)
                dynamic_service = get_dynamic_formula_service()
                capability_name = route_decision.capability

                # Extract project name from query using SimpleQueryHandler's method
                from app.services.simple_query_handler import SimpleQueryHandler
                temp_handler = SimpleQueryHandler(data_service)
                project_name = temp_handler._extract_project_name(request.question)

                # Fall back to request.project_id if extraction failed
                if not project_name:
                    project_name = request.project_id

                # Parse capability to attribute name
                attr_name = capability_name.replace('calculate_', '').replace('_', ' ').title()

                # Search for attribute in Excel-based dynamic service
                attr = dynamic_service.get_attribute(attr_name)
                if not attr:
                    # Try fuzzy search
                    search_result = dynamic_service.search_attribute(attr_name)
                    if search_result:
                        attr, confidence = search_result
                        if confidence < 0.3:
                            attr = None

                # If attribute doesn't require calculation (Formula = "Direct extraction" in Excel)
                if attr and not attr.requires_calculation:
                    # This is a direct extraction attribute, not a calculated one
                    # Fall back to data_service extraction instead of using calculator

                    if not project_name:
                        raise ValueError("Project name required for Layer 0 extraction")

                    # Find project by name using data_service
                    all_projects = data_service.get_all_projects()
                    project_data = None

                    # Normalize search term
                    normalized_search = ' '.join(project_name.lower().replace('\n', ' ').split())

                    for proj in all_projects:
                        # Extract project name from v4 nested format
                        proj_name_obj = proj.get('projectName', {})
                        if isinstance(proj_name_obj, dict):
                            proj_name = proj_name_obj.get('value', '')
                        else:
                            proj_name = proj_name_obj or ''

                        # Normalize project name
                        normalized_proj_name = ' '.join(proj_name.lower().replace('\n', ' ').split())

                        if normalized_proj_name == normalized_search:
                            project_data = proj
                            break

                    # Map attribute name to data field (camelCase conversion)
                    field_mapping = {
                        'Monthly Sales Velocity': 'monthlySalesVelocity',
                        'Sales Velocity': 'monthlySalesVelocity',
                    }

                    field_name = field_mapping.get(attr.target_attribute, attr.target_attribute.replace(' ', ''))

                    if not project_data:
                        raise ValueError(f"Project '{project_name}' not found")

                    # Extract the field value (handles both dict {value, unit} and direct values)
                    field_value = project_data.get(field_name, {})
                    if isinstance(field_value, dict):
                        value = field_value.get('value')
                        unit = field_value.get('unit', attr.unit)
                    else:
                        value = field_value
                        unit = attr.unit

                    if value is None:
                        raise ValueError(f"Field '{field_name}' not found in project data")

                    # Create calc_result in the same format as enriched calculator
                    calc_result = {
                        "status": "success",
                        "attribute": attr.target_attribute,
                        "value": value,
                        "unit": unit,
                        "dimension": attr.dimension,
                        "formula": "Direct extraction from data service",
                        "provenance": {
                            "dataSource": "Liases Foras",
                            "layer": attr.layer,
                            "calculationMethod": "Direct extraction",
                            "description": attr.description,
                            "timestamp": "",
                        }
                    }
                else:
                    # Execute calculation using dynamic formula service (Excel-driven runtime evaluation)
                    if not project_name:
                        raise ValueError("Project name required for calculation")

                    # Get project data
                    all_projects = data_service.get_all_projects()
                    project_data = None

                    # Normalize search term
                    normalized_search = ' '.join(project_name.lower().replace('\n', ' ').split())

                    for proj in all_projects:
                        # Extract project name from v4 nested format
                        proj_name_obj = proj.get('projectName', {})
                        if isinstance(proj_name_obj, dict):
                            proj_name = proj_name_obj.get('value', '')
                        else:
                            proj_name = proj_name_obj or ''

                        # Normalize project name
                        normalized_proj_name = ' '.join(proj_name.lower().replace('\n', ' ').split())

                        if normalized_proj_name == normalized_search:
                            project_data = proj
                            break

                    if not project_data:
                        raise ValueError(f"Project '{project_name}' not found")

                    # Execute formula dynamically using Excel formula
                    calc_result = dynamic_service.execute_formula(attr, project_data)

                    if not calc_result:
                        raise ValueError(f"Failed to calculate '{attr.target_attribute}'")

                # DIMENSION VALIDATION: Check response matches query expectation
                validator = get_dimension_validator()
                is_valid, error_msg = validator.validate_response(
                    query=request.question,
                    response_value=calc_result["value"],
                    response_unit=calc_result["unit"],
                    response_dimension=calc_result.get("dimension")
                )

                if not is_valid:
                    return {
                        "status": "error",
                        "error": error_msg,
                        "query": request.question,
                        "debug": {
                            "expected_dimension": validator.extract_expected_dimension(request.question),
                            "actual_dimension": calc_result.get("dimension"),
                            "actual_value": f"{calc_result['value']} {calc_result['unit']}"
                        }
                    }

                # Format for frontend (matching expected structure)
                return {
                    "status": "success",
                    "answer": {
                        "status": "success",
                        "query": request.question,
                        "understanding": {
                            "layer": "LAYER_1",
                            "dimension": calc_result["dimension"],
                            "operation": capability_name,
                            "confidence": route_decision.confidence,
                            "routing": "enriched_layers"
                        },
                        "result": {
                            "value": calc_result["value"],
                            "unit": calc_result["unit"],
                            "text": f"{round(calc_result['value'], 2)} {calc_result['unit']}",
                            "metric": calc_result.get("attribute", "Unknown"),
                            "dimension": calc_result["dimension"]
                        },
                        "calculation": {
                            "formula": calc_result["formula"],
                            "description": f"{calc_result.get('attribute', 'Calculation')}: {calc_result['formula']}",
                            "fullPrecisionValue": calc_result["value"],
                            "roundedValue": round(calc_result["value"], 2),
                            "unit": calc_result["unit"]
                        },
                        "provenance": {
                            "source": "Liases Foras",  # Source is LF data, even for calculated metrics
                            "attribute": calc_result.get("attribute", "Unknown"),
                            "formula": calc_result["formula"],
                            "timestamp": calc_result.get("provenance", {}).get("timestamp", ""),
                            "routing_confidence": route_decision.confidence,
                            "routing_reason": route_decision.reason
                        }
                    },
                    "query": request.question
                }

            except (ValueError, KeyError, AttributeError) as enriched_error:
                # Enriched calculation failed for Layer 1 query
                # DO NOT fall back to simple_query_handler for calculation queries
                # Return error with helpful message
                print(f"Enriched calculation failed: {enriched_error}")
                return {
                    "status": "error",
                    "error": f"Calculation failed: {str(enriched_error)}. This is a Layer 1 calculated metric that requires enriched calculator.",
                    "query": request.question,
                    "debug": {
                        "route_decision": {
                            "layer": str(route_decision.layer),
                            "confidence": route_decision.confidence,
                            "capability": route_decision.capability
                        },
                        "enriched_error": str(enriched_error)
                    }
                }

        # Step 3: Fall back to simple query handler (LEGACY) - ONLY for Layer 0 queries
        # If we got here, prompt_router said it's NOT Layer 1, so safe to use simple_query_handler
        handler = SimpleQueryHandler(data_service)
        result = handler.handle_query(request.question)

        # DIMENSION VALIDATION: Check simple_query_handler response
        if result.status == "success":
            validator = get_dimension_validator()

            # Extract value, unit, dimension from result
            # NOTE: dimension is a top-level attribute of QueryResult, not nested in result!
            response_value = result.result.get("value")
            response_unit = result.result.get("unit")
            response_dimension = result.dimension  # Top-level attribute!

            is_valid, error_msg = validator.validate_response(
                query=request.question,
                response_value=response_value,
                response_unit=response_unit,
                response_dimension=response_dimension
            )

            if not is_valid:
                return {
                    "status": "error",
                    "error": error_msg,
                    "query": request.question,
                    "debug": {
                        "handler": "simple_query_handler",
                        "expected_dimension": validator.extract_expected_dimension(request.question),
                        "actual_dimension": response_dimension,
                        "actual_value": f"{response_value} {response_unit}",
                        "suggestion": "The data you're looking for may not exist in the knowledge graph. Consider checking available fields."
                    }
                }

        # Format for frontend display
        if result.status == "success":
            return {
                "status": "success",
                "answer": {
                    "status": "success",
                    "query": request.question,
                    "understanding": {
                        "layer": result.layer,
                        "dimension": result.dimension,
                        "operation": result.operation
                    },
                    "result": result.result,
                    "calculation": result.calculation,
                    "provenance": result.provenance
                },
                "query": request.question
            }
        else:
            return {
                "status": "error",
                "error": result.result.get("error", "Query failed"),
                "query": request.question
            }

    except Exception as e:
        return {
            "status": "error",
            "error": f"Query handler error: {str(e)}",
            "query": request.question
        }


@app.post("/api/qa/question/v2")
def ask_question_v2(request: QuestionRequest):
    """
    Ask a question using LLM orchestration with function calling (NEW)

    Uses the new architecture:
    - Input enrichment (spell check, context)
    - LLM routing (Gemini decides which functions to call)
    - Function execution (deterministic calculations or GraphRAG)
    - LLM commentary (analysis, insights, recommendations)
    - Chat history with auto-compacting

    Examples:
    - "Calculate IRR for project 1" → Calls calculate_irr function, provides analysis
    - "Why is absorption rate low?" → Uses GraphRAG + semantic search + LLM insights
    - "Compare top 3 projects" → Calls comparison functions, generates comparative analysis
    - "What's the market opportunity in Chakan?" → Uses Layer 3 OPPS + market insights

    Returns:
    - response: LLM-generated response with analysis and insights
    - function_calls: List of functions called by LLM
    - query_type: Detected query type (calculation, comparison, insight, etc.)
    - session_id: Session ID for multi-turn conversation
    """
    try:
        # Get orchestrator instance
        orchestrator = get_orchestrator()

        # Extract project_id if provided
        project_id_int = None
        if request.project_id:
            try:
                project_id_int = int(request.project_id)
            except (ValueError, TypeError):
                pass

        # Extract location from location_context
        location_str = None
        if request.location_context:
            if request.location_context.region:
                location_str = request.location_context.region
            elif request.location_context.city:
                location_str = request.location_context.city

        # Process query through orchestrator
        result = orchestrator.process_query(
            query=request.question,
            session_id=None,  # Create new session for each request (stateless for now)
            project_id=project_id_int,
            location=location_str,
            metadata={
                "admin_mode": request.admin_mode
            }
        )

        # Format response for frontend compatibility
        return {
            "status": "success",
            "answer": {
                "status": "success",
                "query": request.question,
                "response": result["response"],
                "understanding": {
                    "query_type": result["query_type"],
                    "function_calls": result["function_calls"],
                    "session_id": result["session_id"]
                },
                "result": {
                    "response": result["response"],
                    "function_calls": result["function_calls"],
                    "function_results": result["function_results"]
                },
                "metadata": result["metadata"],
                "provenance": {
                    "source": "orchestrator_service",
                    "query_type": result["query_type"],
                    "timestamp": result["metadata"]["timestamp"]
                }
            },
            "query": request.question
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {
            "status": "error",
            "error": f"Orchestrator error: {str(e)}",
            "error_details": error_details,
            "query": request.question
        }


@app.post("/api/qa/question/v3")
def ask_question_v3_sirrus(request: QuestionRequest):
    """
    SIRRUS.AI - Multi-Dimensional Insight Engine (LangChain-based orchestration)

    Uses LangChain ReAct agent with tools to generate Layer 2 & Layer 3 insights:
    - Layer 0: Fetch raw dimensions (U, C, T, L²) from Knowledge Graph
    - Layer 1: Calculate derived metrics (PSF, AR, velocity) using calculators
    - Layer 2: Generate analytical insights (absorption status, pricing position, market saturation)
    - Layer 3: Generate strategic insights (product mix optimization, launch viability)

    **Architecture:**
    - LangChain ReAct Agent → Tools (KG, Calculators, VectorDB) → Gemini 2.5 Flash Synthesis

    **Example Queries:**
    - "Tell me about Chakan" → Multi-dimensional analysis of Chakan region
    - "Why is absorption low in Sara City?" → Layer 2 insights with market context
    - "Optimize product mix for 100 units" → Layer 3 strategic recommendations

    **Returns:**
    - Structured JSON with insights array (metadata, content, reasoning, recommendations)
    - Each insight traces back to Layer 1 metrics → Layer 0 dimensions
    - Confidence scores and limitations clearly stated
    """
    # Check if SIRRUS service is available
    if not SIRRUS_AVAILABLE or get_sirrus_service is None:
        return {
            "status": "error",
            "error": "SIRRUS.AI service is not available due to import issues with langchain-google-genai. Please update the package or use /api/qa/question endpoint instead.",
            "query": request.question
        }

    try:
        # Get SIRRUS.AI LangChain service
        sirrus_service = get_sirrus_service()

        # Extract region from location_context
        region = None
        if request.location_context:
            if request.location_context.region:
                region = request.location_context.region
            elif request.location_context.city:
                region = request.location_context.city

        # Extract project_id
        project_id_int = None
        if request.project_id:
            try:
                project_id_int = int(request.project_id)
            except (ValueError, TypeError):
                pass

        # Process query using SIRRUS.AI
        result = sirrus_service.process_query(
            query=request.question,
            region=region,
            project_id=project_id_int
        )

        # Format response
        return {
            "status": "success",
            "answer": {
                "status": "success",
                "query": request.question,
                "response": result.get("summary", ""),
                "insights": result.get("insights", []),
                "metadata": result.get("metadata", {}),
                "provenance": {
                    "source": "sirrus_langchain_service",
                    "framework": "LangChain ReAct Agent",
                    "llm": "Gemini 2.5 Flash",
                    "timestamp": result.get("metadata", {}).get("timestamp")
                }
            },
            "query": request.question
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {
            "status": "error",
            "error": f"SIRRUS.AI error: {str(e)}",
            "error_details": error_details,
            "query": request.question
        }


@app.get("/api/qa/summary")
def get_summary(project_id: Optional[str] = Query(None)):
    """
    Get comprehensive project summary (Layer 0 + Layer 1 metrics)

    If no project_id provided, returns summary for first available project
    """
    qa_service = get_qa_service()
    return qa_service.get_project_summary(project_id=project_id)


# Context Service Endpoints (Maps, Images, Weather, News)
@app.get("/api/context/location")
def get_location_context(
    location: str = Query(..., description="Location name (e.g., 'Chakan, Pune')"),
    location_type: str = Query("region", description="Type: 'region' or 'project'"),
    city: Optional[str] = Query(None, description="City name for better search context")
):
    """
    Get visual and informational context for a location/project

    Returns:
    - Google Maps (static image + embed URL)
    - Image collage (4-5 photos from Google Images)
    - Current weather (OpenWeather API)
    - Latest news (NewsAPI)

    Works with graceful fallbacks if API keys not configured
    """
    context_service = get_context_service()
    return context_service.get_location_context(
        location_name=location,
        location_type=location_type,
        city=city
    )


@app.get("/api/context/region")
def get_region_insights(
    region: str = Query(..., description="Region name (e.g., 'Chakan')"),
    city: str = Query("Pune", description="City name")
):
    """
    Get Layer 4 RAG-based insights for a region

    Returns comprehensive market intelligence:
    - Regional overview from city reports
    - Micro-markets within the region
    - Infrastructure and connectivity
    - Development trends and future outlook
    - Price trends
    """
    layer4_calc = Layer4Calculator()
    return layer4_calc.get_region_insights(region=region, city=city)


@app.get("/api/context/catchment")
def get_catchment_insights(
    catchment_area: str = Query(..., description="Catchment area (e.g., 'Western Pune')"),
    city: str = Query("Pune", description="City name"),
    radius_km: Optional[float] = Query(None, description="Radius in km")
):
    """
    Get Layer 4 RAG-based insights for a broader catchment area

    Returns aggregated insights for entire catchment:
    - Area overview and regional breakdown
    - Demographics and economic indicators
    - Major projects and developments
    """
    layer4_calc = Layer4Calculator()
    return layer4_calc.get_catchment_area_insights(
        catchment_area=catchment_area,
        city=city,
        radius_km=radius_km
    )


@app.get("/api/context/city-insights")
def get_city_insights(
    city: str = Query(..., description="City name (e.g., 'Pune')"),
    region: Optional[str] = Query(None, description="Optional region name (e.g., 'Chakan')")
):
    """
    Get document-based city/region insights from vectorized city reports

    Returns salient features extracted from city reports:
    - Economy, culture, geography
    - Infrastructure and connectivity
    - Demographics and landmarks
    - Unique characteristics and history

    Data source: Vectorized city reports in ChromaDB
    """
    doc_vector_service = get_document_vector_service()
    return doc_vector_service.query_city_insights(city=city, region=region)


@app.get("/api/context/news")
def get_location_news(
    location: str = Query(..., description="Location name (e.g., 'Chakan')"),
    city: str = Query(..., description="City name (e.g., 'Pune')")
):
    """
    Get news for a location using Google Custom Search API

    Returns 3 categories:
    1. Latest news (last 7 days) - 3 stories
    2. Big stories in last 1 month - 3 stories
    3. Big stories in last 1 year - 3 stories

    Data source: Google Custom Search API (News search)
    """
    context_service = get_context_service()
    return context_service.get_news_by_timeframe(location=location, city=city)


@app.get("/api/context/distances")
def get_location_distances(
    location: str = Query(..., description="Location name (e.g., 'Chakan')"),
    city: str = Query(..., description="City name (e.g., 'Pune')")
):
    """
    Get distances from location to key destinations

    Uses Google Distance Matrix API to calculate:
    - Distance to airports (Mumbai, Pune)
    - Distance to railway station
    - Distance to city center
    - Distance to IT parks
    - Distance to nearby hospitals, schools, malls

    Returns distance in km and travel time

    Data source: Google Distance Matrix API
    """
    context_service = get_context_service()
    return context_service.get_distances(location=location, city=city)


# Data Refresh Endpoints (V3.0.0)
@app.get("/api/data/status")
def get_data_status():
    """Get current data status (last extraction time, file info)"""
    refresh_service = get_data_refresh_service()
    return refresh_service.get_data_status()


@app.post("/api/data/refresh")
def refresh_all_data():
    """
    Complete data refresh pipeline:
    1. Re-extract PDF data
    2. Export clean nested JSON structure

    Returns pipeline status with step-by-step results
    """
    refresh_service = get_data_refresh_service()
    return refresh_service.refresh_all_data()


@app.post("/api/data/refresh/pdf")
def refresh_pdf_only():
    """Run PDF extraction to nested format"""
    refresh_service = get_data_refresh_service()
    return refresh_service.extract_pdf_only()


# ==================================================================
# KNOWLEDGE GRAPH ENDPOINTS
# ==================================================================

@app.get("/api/knowledge-graph/dimensions")
def get_l0_dimensions():
    """Get L0 dimension definitions (center of knowledge graph)"""
    return knowledge_graph_service.get_layer_0_dimensions()


@app.get("/api/knowledge-graph/stats")
def get_kg_stats():
    """Get knowledge graph statistics"""
    return knowledge_graph_service.get_knowledge_graph_stats()


@app.get("/api/knowledge-graph/relationships/{dimension}")
def get_relationships_for_dimension(dimension: str):
    """
    Get all relationships involving a dimension

    Args:
        dimension: U, L², T, or C
    """
    return knowledge_graph_service.get_all_relationships_for_dimension(dimension)


@app.get("/api/knowledge-graph/visualization")
def get_graph_visualization(project_name: Optional[str] = None, city: Optional[str] = None):
    """
    Get graph visualization data

    Args:
        project_name: Optional project name to focus on
        city: Optional city name for location-aware data (default: Pune)
    """
    # Switch to requested city if provided
    if city and city != knowledge_graph_service.city:
        knowledge_graph_service.set_city(city)

    return knowledge_graph_service.get_graph_visualization_data(project_name)


@app.get("/api/knowledge-graph/profile/{project_name}")
def get_dimensional_profile(project_name: str):
    """Get complete dimensional profile of a project"""
    return knowledge_graph_service.get_dimensional_profile(project_name)


# ==================================================================
# L2 + L3 INSIGHTS ENDPOINTS (NON-LLM)
# ==================================================================

@app.get("/api/projects/{project_id}/insights")
def get_project_insights(project_id: str):
    """
    Get pre-calculated L3 insights for a project (NON-LLM)

    Returns:
    - L1 insights (from rules applied to raw data)
    - L2 insights (from rules applied to calculated metrics)
    - Summary (Excellent/Okay/Bad counts, overall health)
    - Metrics needing LLM recommendations
    """
    project = data_service.get_project(project_id)
    if not project:
        return {"error": f"Project not found: {project_id}"}

    # Return pre-calculated L3 insights
    l3_insights = project.get("l3_insights", {})

    if not l3_insights:
        return {"error": "L3 insights not yet calculated for this project"}

    return {
        "projectId": project_id,
        "projectName": data_service.get_value(project.get("projectName")),
        "insights": l3_insights,
        "note": "All insights generated using NON-LLM rule-based thresholds"
    }


@app.get("/api/projects/{project_id}/l2-metrics")
def get_project_l2_metrics(project_id: str):
    """
    Get pre-calculated L2 financial metrics for a project

    Returns all L2 metrics: NPV, IRR, ROI, Payback Period, etc.
    """
    project = data_service.get_project(project_id)
    if not project:
        return {"error": f"Project not found: {project_id}"}

    l2_metrics = project.get("l2_metrics", {})

    if not l2_metrics:
        return {"error": "L2 metrics not yet calculated for this project"}

    return {
        "projectId": project_id,
        "projectName": data_service.get_value(project.get("projectName")),
        "l2_metrics": l2_metrics,
        "note": "All metrics calculated using deterministic formulas (NON-LLM)"
    }


# ==================================================================
# MAP VISUALIZATION ENDPOINTS
# ==================================================================

@app.get("/api/maps/heat-map")
def get_heat_map_data(
    metric: str = Query("currentPricePSF", description="Metric to visualize (e.g., currentPricePSF, totalSupplyUnits)"),
    region: Optional[str] = Query(None, description="Optional region filter (e.g., 'Chakan')")
):
    """
    Get project data for heat-map visualization

    Returns projects with latitude/longitude and selected metric for Plotly scatter_mapbox

    Args:
        metric: Attribute name to extract (default: currentPricePSF)
        region: Optional region filter

    Returns:
        List of projects with:
        - projectName
        - latitude, longitude (from L0 geocoding)
        - metric_value (extracted from specified attribute)
        - metric_name (for display)
        - location (for grouping)

    Example:
        GET /api/maps/heat-map?metric=currentPricePSF&region=Chakan
    """
    try:
        # Get all projects
        projects = data_service.get_all_projects()

        # Filter by region if provided
        if region:
            normalized_region = region.strip().lower()
            projects = [
                p for p in projects
                if normalized_region in (data_service.get_value(p.get('location', '')) or '').strip().lower()
            ]

        # Extract coordinates and metric for each project
        result = []
        for p in projects:
            # Extract latitude and longitude from L0 attributes
            lat_attr = p.get('latitude', {})
            lon_attr = p.get('longitude', {})

            # Get coordinates (already stored as L0 attributes from geocoding)
            latitude = data_service.get_value(lat_attr)
            longitude = data_service.get_value(lon_attr)

            # Skip projects without coordinates
            if latitude is None or longitude is None:
                continue

            # Extract metric value
            metric_attr = p.get(metric, {})
            metric_value = data_service.get_value(metric_attr)

            # Skip projects without metric value
            if metric_value is None:
                continue

            # Get metric unit for display
            metric_unit = data_service.get_unit(metric_attr)

            result.append({
                "projectId": int(data_service.get_value(p.get('projectId', {})) or 0),
                "projectName": data_service.get_value(p.get('projectName')),
                "latitude": latitude,
                "longitude": longitude,
                "metric_value": metric_value,
                "metric_name": metric,
                "metric_unit": metric_unit,
                "location": data_service.get_value(p.get('location')),
                "microMarket": data_service.get_value(p.get('microMarket'))
            })

        return {
            "status": "success",
            "count": len(result),
            "metric": metric,
            "region": region,
            "projects": result
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "metric": metric,
            "region": region
        }


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    projects_loaded = len(data_service.get_all_projects())
    lf_data_loaded = len(data_service.lf_data)

    return {
        "status": "healthy",
        "data": {
            "projects_loaded": projects_loaded,
            "lf_pillars_loaded": lf_data_loaded
        },
        "version": "2.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=settings.DEBUG
    )
