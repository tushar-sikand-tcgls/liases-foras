"""
Query Orchestrator using LangGraph State Machine

This orchestrator coordinates query execution across different adapters
using a state machine pattern to route queries to the appropriate handlers.
"""

from typing import Dict, List, Optional, Any, TypedDict, Literal
from langgraph.graph import StateGraph, END
from app.adapters import FormulaServiceAdapter, ProjectServiceAdapter, StatisticalAnalysisAdapter
from app.services.graphrag_orchestrator import GraphRAGOrchestrator
import os


# Define the state schema
class QueryState(TypedDict):
    """State schema for the query orchestration workflow"""
    # Input
    query: str  # User's natural language query

    # Classification
    query_type: Optional[str]  # 'attribute_query', 'calculation', 'statistical', 'project_search', 'comparison'

    # Context extraction
    attribute_name: Optional[str]  # Extracted attribute name
    project_name: Optional[str]  # Extracted project name
    location: Optional[str]  # Extracted location
    aggregation_type: Optional[str]  # For statistical queries: 'mean', 'sum', etc.

    # Resolved entities
    attribute_def: Optional[Dict]  # Attribute definition from Excel
    project_data: Optional[Dict]  # Project data if found
    projects_list: Optional[List[Dict]]  # List of projects for statistical queries

    # Results
    result: Optional[Any]  # Final result
    error: Optional[str]  # Error message if any

    # Metadata
    execution_path: List[str]  # Track which nodes were executed

    # GraphRAG metadata (LLM-driven resolution)
    graphrag_used: Optional[bool]  # Whether GraphRAG was used
    graphrag_confidence: Optional[float]  # LLM confidence score (0-1)
    graphrag_reasoning: Optional[str]  # LLM's reasoning for the decision


class QueryOrchestrator:
    """
    LangGraph-based orchestrator for query routing and execution

    Routes queries through a state machine to appropriate adapters:
    - FormulaServiceAdapter for attribute calculations
    - ProjectServiceAdapter for project queries
    - StatisticalAnalysisAdapter for aggregations
    """

    def __init__(self):
        # Initialize adapters
        self.formula_adapter = FormulaServiceAdapter()
        self.project_adapter = ProjectServiceAdapter()
        self.stats_adapter = StatisticalAnalysisAdapter()

        # Initialize GraphRAG orchestrator (LLM-driven matching)
        # Only initialize if GOOGLE_API_KEY or GEMINI_API_KEY is available
        self.graphrag = None
        self.use_graphrag = False
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                self.graphrag = GraphRAGOrchestrator()
                self.use_graphrag = True
                print("✅ GraphRAG enabled - LLM-driven query resolution active")
            except Exception as e:
                print(f"⚠️  GraphRAG initialization failed: {e}. Falling back to fuzzy matching.")
                self.use_graphrag = False
        else:
            print("ℹ️  GraphRAG disabled - GOOGLE_API_KEY not found. Using fuzzy matching.")

        # Build the state graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""

        # Create the graph
        workflow = StateGraph(QueryState)

        # Add nodes
        workflow.add_node("classify_query", self._classify_query_node)
        workflow.add_node("extract_context", self._extract_context_node)
        workflow.add_node("resolve_attribute", self._resolve_attribute_node)
        workflow.add_node("resolve_project", self._resolve_project_node)
        workflow.add_node("resolve_projects_list", self._resolve_projects_list_node)
        workflow.add_node("execute_calculation", self._execute_calculation_node)
        workflow.add_node("execute_statistical", self._execute_statistical_node)
        workflow.add_node("execute_project_query", self._execute_project_query_node)
        workflow.add_node("format_response", self._format_response_node)

        # Set entry point
        workflow.set_entry_point("classify_query")

        # Add edges
        workflow.add_edge("classify_query", "extract_context")

        # Conditional routing from extract_context
        workflow.add_conditional_edges(
            "extract_context",
            self._route_after_context,
            {
                "resolve_attribute": "resolve_attribute",
                "resolve_projects_list": "resolve_projects_list",
                "resolve_project": "resolve_project",
                "error": "format_response",
            }
        )

        # Attribute resolution routes
        workflow.add_conditional_edges(
            "resolve_attribute",
            self._route_after_attribute,
            {
                "resolve_project": "resolve_project",
                "resolve_projects_list": "resolve_projects_list",
                "error": "format_response",
            }
        )

        # Project resolution routes
        workflow.add_edge("resolve_project", "execute_calculation")

        # Conditional routing from resolve_projects_list
        workflow.add_conditional_edges(
            "resolve_projects_list",
            self._route_after_projects_list,
            {
                "execute_statistical": "execute_statistical",
                "execute_project_query": "execute_project_query",
            }
        )

        # Execution routes
        workflow.add_edge("execute_calculation", "format_response")
        workflow.add_edge("execute_statistical", "format_response")
        workflow.add_edge("execute_project_query", "format_response")

        # End
        workflow.add_edge("format_response", END)

        return workflow.compile()

    # ========== Node Functions ==========

    def _classify_query_node(self, state: QueryState) -> QueryState:
        """Classify the query type"""
        query = state["query"].lower()
        state["execution_path"].append("classify_query")

        # Simple keyword-based classification (order matters!)
        # First check for project search (most specific)
        if any(phrase in query for phrase in ["show all projects", "list projects", "find projects", "search projects"]):
            state["query_type"] = "project_search"
        # Then check for statistical queries
        elif any(word in query for word in ["average", "mean", "total", "sum", "median", "max", "min"]) and "across" in query:
            state["query_type"] = "statistical"
        # Check for comparison
        elif "compare" in query or "vs" in query or "versus" in query:
            state["query_type"] = "comparison"
        else:
            # Default to attribute query/calculation
            state["query_type"] = "calculation"

        return state

    def _extract_context_node(self, state: QueryState) -> QueryState:
        """Extract context from the query (attribute name, project name, location)"""
        state["execution_path"].append("extract_context")

        query = state["query"]

        # Extract project name (simple pattern matching)
        # Look for common patterns like "of <project>" or "for <project>"
        for prep in [" of ", " for ", " in "]:
            if prep in query.lower():
                parts = query.lower().split(prep)
                if len(parts) > 1:
                    # Try to extract project name
                    potential_project = parts[1].strip().split()[0:3]  # Take up to 3 words
                    potential_project_str = " ".join(potential_project).strip("?.")

                    # Check if this matches a known project
                    all_projects = self.project_adapter.list_all_projects()
                    for proj in all_projects:
                        proj_name_obj = proj.get('projectName', {})
                        if isinstance(proj_name_obj, dict):
                            proj_name = proj_name_obj.get('value', '').lower()
                        else:
                            proj_name = str(proj_name_obj).lower()

                        if potential_project_str in proj_name or proj_name in potential_project_str:
                            state["project_name"] = proj_name_obj.get('value') if isinstance(proj_name_obj, dict) else proj_name_obj
                            break

        # Extract location (simple pattern matching)
        for location_keyword in ["pune", "mumbai", "bangalore", "delhi", "hyderabad", "chennai", "chakan"]:
            if location_keyword in query.lower():
                state["location"] = location_keyword.title()
                break

        # Extract aggregation type for statistical queries
        if state["query_type"] == "statistical":
            for agg_type in ["average", "mean", "sum", "total", "median", "max", "min"]:
                if agg_type in query.lower():
                    if agg_type == "average":
                        state["aggregation_type"] = "mean"
                    elif agg_type == "total":
                        state["aggregation_type"] = "sum"
                    else:
                        state["aggregation_type"] = agg_type
                    break

        return state

    def _resolve_attribute_node(self, state: QueryState) -> QueryState:
        """Resolve the attribute being queried using GraphRAG (LLM-driven) or vector search fallback"""
        state["execution_path"].append("resolve_attribute")

        query = state["query"]

        # GraphRAG Path: Use LLM-driven intelligent matching (handles spelling, case, newlines)
        if self.use_graphrag and self.graphrag:
            try:
                # Get available attributes and projects for LLM context
                available_attributes = [attr.get('name', '') for attr in self.formula_adapter.list_all_attributes()]
                available_projects = [proj.get('projectName', {}).get('value', '') for proj in self.project_adapter.list_all_projects()]

                # Let GraphRAG LLM think about the query
                graphrag_response = self.graphrag.query(
                    user_query=query,
                    available_attributes=available_attributes,
                    available_projects=available_projects
                )

                # If LLM successfully resolved the query
                if graphrag_response.attribute_used and graphrag_response.confidence > 0.5:
                    state["attribute_name"] = graphrag_response.attribute_used

                    # Find the full attribute definition
                    all_attributes = self.formula_adapter.list_all_attributes()
                    for attr in all_attributes:
                        if attr.get('name') == graphrag_response.attribute_used:
                            state["attribute_def"] = attr
                            break

                    # Store GraphRAG metadata for debugging
                    state["graphrag_used"] = True
                    state["graphrag_confidence"] = graphrag_response.confidence
                    state["graphrag_reasoning"] = graphrag_response.llm_reasoning

                    return state
                else:
                    # LLM couldn't resolve with high confidence, fall through to fuzzy matching
                    print(f"⚠️  GraphRAG low confidence ({graphrag_response.confidence:.2f}), falling back to fuzzy matching")

            except Exception as e:
                print(f"⚠️  GraphRAG error: {e}. Falling back to fuzzy matching.")
                # Fall through to fuzzy matching

        # Fuzzy Matching Fallback Path: Traditional vector search
        # First try: Use formula adapter vector search
        results = self.formula_adapter.search_attributes(query)

        if results and len(results) > 0:
            # Take the first result (highest confidence)
            attr_result = results[0]
            state["attribute_def"] = attr_result
            state["attribute_name"] = attr_result.get("name")
            return state

        # Second try: Extract potential attribute names from query and lookup directly
        # Get all available attributes
        all_attributes = self.formula_adapter.list_all_attributes()

        # Try to find attribute by partial name match
        query_lower = query.lower()
        for attr in all_attributes:
            attr_name_lower = attr.get('name', '').lower()
            # Check if attribute name appears in query
            if attr_name_lower in query_lower or any(word in attr_name_lower for word in query_lower.split()):
                # Found a match!
                state["attribute_def"] = attr
                state["attribute_name"] = attr.get("name")
                return state

        # If still no match, set error
        state["error"] = f"Could not find attribute matching query: {query}"

        return state

    def _resolve_project_node(self, state: QueryState) -> QueryState:
        """Resolve the project data using GraphRAG (LLM-driven) or fuzzy matching fallback"""
        state["execution_path"].append("resolve_project")

        project_name = state.get("project_name")

        # If GraphRAG was used in attribute resolution and provided a project match, use it
        if self.use_graphrag and self.graphrag and state.get("graphrag_used"):
            # GraphRAG might have already resolved the project name better
            # Check if there's a GraphRAG project match in the response
            if state.get("project_name"):
                # Try to find with GraphRAG-resolved project name (handles spelling variations)
                all_projects = self.project_adapter.list_all_projects()

                # Normalize project name for matching
                project_name_normalized = project_name.replace('\n', ' ').strip().lower()

                for proj in all_projects:
                    proj_name_obj = proj.get('projectName', {})
                    if isinstance(proj_name_obj, dict):
                        proj_name = proj_name_obj.get('value', '').replace('\n', ' ').strip().lower()
                    else:
                        proj_name = str(proj_name_obj).replace('\n', ' ').strip().lower()

                    # Exact match or very close match
                    if proj_name == project_name_normalized or project_name_normalized in proj_name or proj_name in project_name_normalized:
                        state["project_data"] = proj
                        return state

        if not project_name:
            state["error"] = "No project name found in query"
            return state

        # Fuzzy Matching Fallback: Try to find project by name with normalization
        project = self.project_adapter.find_by_name(project_name)

        if project:
            state["project_data"] = project
        else:
            # Try with newline normalization
            project_name_normalized = project_name.replace('\n', ' ').strip()
            project = self.project_adapter.find_by_name(project_name_normalized)

            if project:
                state["project_data"] = project
            else:
                state["error"] = f"Project '{project_name}' not found"

        return state

    def _resolve_projects_list_node(self, state: QueryState) -> QueryState:
        """Resolve list of projects for statistical queries"""
        state["execution_path"].append("resolve_projects_list")

        location = state.get("location")

        if location:
            # Get projects by location
            projects = self.project_adapter.find_by_location(location)
        else:
            # Get all projects
            projects = self.project_adapter.find_all()

        state["projects_list"] = projects

        if not projects:
            state["error"] = f"No projects found" + (f" in {location}" if location else "")

        return state

    def _execute_calculation_node(self, state: QueryState) -> QueryState:
        """Execute attribute calculation"""
        state["execution_path"].append("execute_calculation")

        attribute_name = state.get("attribute_name")
        project_data = state.get("project_data")

        if not attribute_name or not project_data:
            state["error"] = "Missing attribute name or project data for calculation"
            return state

        # Execute calculation using formula adapter
        result = self.formula_adapter.calculate(attribute_name, project_data)

        state["result"] = result

        return state

    def _execute_statistical_node(self, state: QueryState) -> QueryState:
        """Execute statistical analysis"""
        state["execution_path"].append("execute_statistical")

        attribute_name = state.get("attribute_name")
        projects_list = state.get("projects_list")
        aggregation_type = state.get("aggregation_type", "mean")

        if not attribute_name or not projects_list:
            state["error"] = "Missing attribute name or projects list for statistical analysis"
            return state

        try:
            # Execute statistical calculation
            if aggregation_type in ["sum", "mean", "median", "max", "min"]:
                result_value = self.stats_adapter.calculate_aggregation(
                    attribute_name,
                    aggregation_type,
                    projects_list
                )
            else:
                # Default to average
                result_value = self.stats_adapter.calculate_average(
                    attribute_name,
                    projects_list
                )

            state["result"] = {
                "attribute": attribute_name,
                "aggregation_type": aggregation_type,
                "value": result_value,
                "num_projects": len(projects_list),
                "location": state.get("location")
            }
        except ValueError as e:
            state["error"] = str(e)

        return state

    def _execute_project_query_node(self, state: QueryState) -> QueryState:
        """Execute project search query"""
        state["execution_path"].append("execute_project_query")

        location = state.get("location")

        # Get projects
        if location:
            projects = self.project_adapter.find_by_location(location)
        else:
            projects = self.project_adapter.find_all()

        state["result"] = {
            "projects": projects,
            "count": len(projects),
            "location": location
        }

        return state

    def _format_response_node(self, state: QueryState) -> QueryState:
        """Format the final response"""
        state["execution_path"].append("format_response")

        # Response is already formatted in result or error
        # This node can be extended to add additional formatting logic

        return state

    # ========== Routing Functions ==========

    def _route_after_context(self, state: QueryState) -> str:
        """Route after context extraction based on query type"""

        if state.get("error"):
            return "error"

        query_type = state.get("query_type")

        if query_type == "project_search":
            # Just get projects list - skip attribute resolution
            return "resolve_projects_list"
        elif query_type == "statistical":
            # Need to resolve attribute and projects list
            return "resolve_attribute"
        elif query_type == "calculation":
            # Need attribute and project
            return "resolve_attribute"
        else:
            # Default to attribute resolution
            return "resolve_attribute"

    def _route_after_attribute(self, state: QueryState) -> str:
        """Route after attribute resolution"""

        if state.get("error"):
            return "error"

        query_type = state.get("query_type")

        if query_type == "statistical":
            return "resolve_projects_list"
        else:
            return "resolve_project"

    def _route_after_projects_list(self, state: QueryState) -> str:
        """Route after projects list resolution"""

        query_type = state.get("query_type")

        if query_type == "project_search":
            return "execute_project_query"
        else:
            # Statistical query
            return "execute_statistical"

    # ========== Public Interface ==========

    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a query through the LangGraph orchestrator

        Args:
            query: Natural language query string

        Returns:
            Dictionary with result, error, execution metadata, and GraphRAG metadata
        """
        # Initialize state
        initial_state: QueryState = {
            "query": query,
            "query_type": None,
            "attribute_name": None,
            "project_name": None,
            "location": None,
            "aggregation_type": None,
            "attribute_def": None,
            "project_data": None,
            "projects_list": None,
            "result": None,
            "error": None,
            "execution_path": [],
            "graphrag_used": None,
            "graphrag_confidence": None,
            "graphrag_reasoning": None
        }

        # Execute the graph
        final_state = self.graph.invoke(initial_state)

        # Return formatted response with GraphRAG metadata
        return {
            "query": query,
            "query_type": final_state.get("query_type"),
            "result": final_state.get("result"),
            "error": final_state.get("error"),
            "execution_path": final_state.get("execution_path"),
            "metadata": {
                "attribute_name": final_state.get("attribute_name"),
                "project_name": final_state.get("project_name"),
                "location": final_state.get("location"),
                "aggregation_type": final_state.get("aggregation_type"),
            },
            "graphrag_metadata": {
                "used": final_state.get("graphrag_used", False),
                "confidence": final_state.get("graphrag_confidence"),
                "reasoning": final_state.get("graphrag_reasoning")
            }
        }
