"""
Gemini Unified Adapter - File Search (Managed RAG) + Knowledge Graph Function Calling

This adapter implements the future-state ATLAS architecture where:
1. Gemini File Search provides managed RAG over documents (Excel, PDF, DOCX)
2. Knowledge Graph functions provide structured data access
3. Gemini decides autonomously which tool to use (or both)

Architecture:
    User Query
        ↓
    Gemini (with 2 tools: File Search + KG)
        ↓
    ┌─────────────────┬──────────────────────┐
    │ File Search     │ KG Function Call     │
    │ (Managed RAG)   │ (Custom Function)    │
    └─────────────────┴──────────────────────┘
        ↓
    Gemini synthesizes final answer with citations

References:
- https://ai.google.dev/gemini-api/docs/file-search
- https://ai.google.dev/gemini-api/docs/function-calling
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    from google import genai
    from google.genai import types
    GENAI_SDK_AVAILABLE = True
except ImportError:
    GENAI_SDK_AVAILABLE = False
    genai = None
    types = None
    print("⚠️  WARNING: google-genai package not installed")
    print("⚠️  Install with: pip install google-genai")


@dataclass
class UnifiedQueryResult:
    """Result from unified File Search + KG query"""
    text_response: str
    file_search_used: bool
    kg_function_called: bool
    kg_results: Optional[Dict] = None
    citations: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None


class GeminiUnifiedAdapter:
    """
    Unified adapter combining Gemini File Search (managed RAG) + KG function calling

    This is the core adapter for future-state ATLAS where Gemini autonomously
    decides whether to use File Search, Knowledge Graph lookup, or both.

    Key Features:
    - Managed RAG via Gemini File Search (no vector DB maintenance)
    - Structured data via KG function calling
    - Autonomous tool selection by Gemini
    - Citation support from File Search
    - Hexagonal architecture (implements multiple ports)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        file_search_store_name: Optional[str] = None,
        kg_adapter = None,
        model: str = "gemini-2.0-flash-exp"
    ):
        """
        Initialize unified adapter

        Args:
            api_key: Google API key (defaults to env var)
            file_search_store_name: Name of File Search store (defaults to env var)
            kg_adapter: Knowledge Graph adapter (for function execution)
            model: Gemini model to use
        """
        if not GENAI_SDK_AVAILABLE:
            raise ImportError(
                "google-genai package required. Install with: pip install google-genai"
            )

        # Get API key
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")

        # Get File Search store name
        self.file_search_store_name = file_search_store_name or os.getenv("FILE_SEARCH_STORE_NAME")
        if not self.file_search_store_name:
            print("⚠️  WARNING: FILE_SEARCH_STORE_NAME not set. File Search will not be available.")
            print("⚠️  Run scripts/upload_to_gemini_file_search.py to create and configure File Search store.")

        # Initialize client
        self.client = genai.Client(api_key=self.api_key)
        self.model = model

        # Store KG adapter for function execution
        self.kg_adapter = kg_adapter

        print(f"✅ Gemini Unified Adapter initialized")
        print(f"   Model: {model}")
        print(f"   File Search Store: {self.file_search_store_name[:50] if self.file_search_store_name else 'Not configured'}...")
        print(f"   KG Adapter: {type(kg_adapter).__name__ if kg_adapter else 'Not configured'}")

    def _create_file_search_tool(self) -> types.Tool:
        """
        Create Gemini File Search tool configuration

        Returns:
            File Search tool for Gemini
        """
        if not self.file_search_store_name:
            raise ValueError("File Search store not configured. Set FILE_SEARCH_STORE_NAME environment variable.")

        # Create File Search tool (native Gemini tool)
        file_search_tool = types.Tool(
            file_search=types.FileSearchTool(
                file_search_store_names=[self.file_search_store_name]
            )
        )

        return file_search_tool

    def _create_kg_function_tool(self) -> types.Tool:
        """
        Create Knowledge Graph function calling tool

        This tool allows Gemini to query the local Knowledge Graph for:
        - Project data (dimensions, metrics)
        - Entity lookups
        - Relationship traversal
        - Dimensional lineage

        Returns:
            KG function calling tool for Gemini
        """
        # Define KG function schema (compatible with Interactions API)
        # Uses raw dict format that gets converted to types.FunctionDeclaration
        kg_function_dict = {
            "name": "knowledge_graph_lookup",
            "description": """Query the local Knowledge Graph for structured real estate data.

Use this tool when the user asks for:
- Specific project data (e.g., "What is the project size of Sara City?")
- Dimensional metrics (Units, Area, Time, Cash Flow, PSF, ASP, IRR, NPV)
- Comparisons between projects
- Calculations based on structured data
- Entity resolution (finding projects by name or location)

DO NOT use this for:
- Definitions or concepts (use File Search instead)
- General real estate knowledge (use File Search instead)
- Market insights from documents (use File Search instead)""",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "description": """Type of KG query to execute:
- "get_project_by_name": Find project by name
- "get_project_dimensions": Get raw Layer 0 dimensions (U, L², T, CF)
- "get_project_metrics": Get calculated Layer 1 metrics (PSF, ASP, AR)
- "compare_projects": Compare multiple projects
- "calculate_metric": Calculate a specific metric (IRR, NPV, etc.)""",
                        "enum": [
                            "get_project_by_name",
                            "get_project_dimensions",
                            "get_project_metrics",
                            "compare_projects",
                            "calculate_metric"
                        ]
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project (e.g., 'Sara City', 'VTP Pegasus')"
                    },
                    "project_id": {
                        "type": "integer",
                        "description": "Project ID (optional, use if known)"
                    },
                    "attribute": {
                        "type": "string",
                        "description": "Attribute name for metrics/calculations (e.g., 'Project Size', 'PSF', 'IRR')"
                    },
                    "projects": {
                        "type": "array",
                        "description": "List of project names for comparison queries",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["query_type"]
            }
        }

        # Convert to FunctionDeclaration (Interactions API format)
        kg_function = types.FunctionDeclaration(**kg_function_dict)

        # Wrap in Tool
        kg_tool = types.Tool(function_declarations=[kg_function])

        return kg_tool

    def _execute_kg_function(self, function_name: str, args: Dict) -> Dict:
        """
        Execute Knowledge Graph function call

        Args:
            function_name: Name of function to execute
            args: Function arguments from Gemini

        Returns:
            Result from KG query
        """
        if not self.kg_adapter:
            return {
                "error": "Knowledge Graph adapter not configured",
                "success": False
            }

        query_type = args.get("query_type")
        project_name = args.get("project_name")
        project_id = args.get("project_id")
        attribute = args.get("attribute")
        projects = args.get("projects", [])

        print(f"\n🔍 KG Function Call:")
        print(f"   Type: {query_type}")
        print(f"   Project: {project_name or project_id}")
        print(f"   Attribute: {attribute}")

        try:
            # Route to appropriate KG adapter method based on query type
            if query_type == "get_project_by_name":
                if not project_name:
                    return {"error": "project_name required", "success": False}

                # Fuzzy match project name
                result = self.kg_adapter.fuzzy_match_project(project_name)
                if not result:
                    return {
                        "error": f"Project '{project_name}' not found",
                        "success": False
                    }

                return {
                    "success": True,
                    "data": result,
                    "query_type": query_type
                }

            elif query_type == "get_project_dimensions":
                # Get raw Layer 0 dimensions
                if project_id:
                    project_data = self.kg_adapter.get_project_by_id(project_id)
                elif project_name:
                    matched_project = self.kg_adapter.fuzzy_match_project(project_name)
                    if matched_project:
                        project_data = matched_project
                    else:
                        return {"error": f"Project '{project_name}' not found", "success": False}
                else:
                    return {"error": "project_name or project_id required", "success": False}

                # Extract Layer 0 dimensions
                dimensions = self.kg_adapter.extract_layer0_dimensions(project_data)

                return {
                    "success": True,
                    "data": dimensions,
                    "query_type": query_type,
                    "project_name": project_data.get("projectName", {}).get("value")
                }

            elif query_type == "get_project_metrics":
                # Get calculated Layer 1 metrics
                if project_id:
                    project_data = self.kg_adapter.get_project_by_id(project_id)
                elif project_name:
                    matched_project = self.kg_adapter.fuzzy_match_project(project_name)
                    if matched_project:
                        project_data = matched_project
                    else:
                        return {"error": f"Project '{project_name}' not found", "success": False}
                else:
                    return {"error": "project_name or project_id required", "success": False}

                # If specific attribute requested
                if attribute:
                    value = self.kg_adapter.get_attribute_value(project_data, attribute)
                    return {
                        "success": True,
                        "data": {
                            "attribute": attribute,
                            "value": value.get("value") if isinstance(value, dict) else value,
                            "unit": value.get("unit") if isinstance(value, dict) else None
                        },
                        "query_type": query_type,
                        "project_name": project_data.get("projectName", {}).get("value")
                    }
                else:
                    # Return all metrics
                    metrics = self.kg_adapter.extract_layer1_metrics(project_data)
                    return {
                        "success": True,
                        "data": metrics,
                        "query_type": query_type,
                        "project_name": project_data.get("projectName", {}).get("value")
                    }

            elif query_type == "compare_projects":
                # Compare multiple projects
                if not projects or len(projects) < 2:
                    return {"error": "At least 2 projects required for comparison", "success": False}

                comparison_results = []
                for proj_name in projects:
                    matched = self.kg_adapter.fuzzy_match_project(proj_name)
                    if matched:
                        comparison_results.append({
                            "project_name": matched.get("projectName", {}).get("value"),
                            "data": self.kg_adapter.extract_layer1_metrics(matched)
                        })

                return {
                    "success": True,
                    "data": comparison_results,
                    "query_type": query_type
                }

            elif query_type == "calculate_metric":
                # Calculate specific metric (IRR, NPV, etc.)
                if not attribute:
                    return {"error": "attribute required for calculation", "success": False}

                if project_id:
                    project_data = self.kg_adapter.get_project_by_id(project_id)
                elif project_name:
                    matched_project = self.kg_adapter.fuzzy_match_project(project_name)
                    if matched_project:
                        project_data = matched_project
                    else:
                        return {"error": f"Project '{project_name}' not found", "success": False}
                else:
                    return {"error": "project_name or project_id required", "success": False}

                # Use calculator to compute metric
                # This would be enhanced with actual calculator integration
                calc_result = self.kg_adapter.calculate_attribute(project_data, attribute)

                return {
                    "success": True,
                    "data": calc_result,
                    "query_type": query_type,
                    "project_name": project_data.get("projectName", {}).get("value")
                }

            else:
                return {
                    "error": f"Unknown query_type: {query_type}",
                    "success": False
                }

        except Exception as e:
            return {
                "error": f"KG function execution failed: {str(e)}",
                "success": False
            }

    def query(
        self,
        user_query: str,
        previous_interaction_id: Optional[str] = None,
        enable_file_search: bool = True,
        enable_kg: bool = True
    ) -> UnifiedQueryResult:
        """
        Query with unified File Search + KG function calling

        Gemini autonomously decides which tool(s) to use based on the query.

        Args:
            user_query: Natural language query from user
            previous_interaction_id: Optional interaction ID for multi-turn context
            enable_file_search: Enable File Search tool (default: True)
            enable_kg: Enable KG function calling (default: True)

        Returns:
            UnifiedQueryResult with response and metadata
        """
        print(f"\n{'='*80}")
        print(f"UNIFIED QUERY (File Search + KG)")
        print(f"{'='*80}")
        print(f"Query: {user_query}")
        print(f"Tools enabled: File Search={enable_file_search}, KG={enable_kg}")

        # Build tools list
        tools = []

        if enable_file_search and self.file_search_store_name:
            tools.append(self._create_file_search_tool())
            print("✓ File Search tool added")

        if enable_kg and self.kg_adapter:
            tools.append(self._create_kg_function_tool())
            print("✓ KG function tool added")

        if not tools:
            raise ValueError("At least one tool must be enabled (File Search or KG)")

        # Create config with tools
        config = types.GenerateContentConfig(
            tools=tools,
            temperature=0.2,  # Low temperature for factual queries
            top_p=0.95
        )

        # Generate content
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_query,
                config=config
            )

            # Check for function calls
            file_search_used = False
            kg_function_called = False
            kg_results = None

            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]

                # Check for KG function calls
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call'):
                            kg_function_called = True
                            func_call = part.function_call

                            print(f"\n🔧 Function Call Detected:")
                            print(f"   Name: {func_call.name}")
                            print(f"   Args: {dict(func_call.args)}")

                            # Execute KG function
                            kg_results = self._execute_kg_function(
                                function_name=func_call.name,
                                args=dict(func_call.args)
                            )

                            print(f"   Result: {kg_results.get('success', False)}")

                            # Send KG result back to Gemini for synthesis
                            function_response_part = types.Part.from_function_response(
                                name=func_call.name,
                                response={"result": kg_results}
                            )

                            # Generate final response with KG results
                            final_response = self.client.models.generate_content(
                                model=self.model,
                                contents=[
                                    types.Content(role="user", parts=[types.Part.from_text(user_query)]),
                                    types.Content(role="model", parts=[part]),
                                    types.Content(role="user", parts=[function_response_part])
                                ],
                                config=config
                            )

                            response = final_response

            # Extract text response
            text_response = ""
            if hasattr(response, 'text'):
                text_response = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        text_response += part.text

            # Check if File Search was used (heuristic: if no KG call and we got a response)
            if not kg_function_called and text_response:
                file_search_used = True

            # Extract citations (if File Search was used)
            citations = None
            if file_search_used:
                # TODO: Extract grounding metadata for citations
                # This will be available in response.candidates[0].grounding_metadata
                citations = []

            print(f"\n✅ Query complete:")
            print(f"   File Search used: {file_search_used}")
            print(f"   KG function called: {kg_function_called}")
            print(f"   Response length: {len(text_response)} chars")

            return UnifiedQueryResult(
                text_response=text_response,
                file_search_used=file_search_used,
                kg_function_called=kg_function_called,
                kg_results=kg_results,
                citations=citations,
                metadata={
                    "model": self.model,
                    "tools_available": len(tools),
                    "query_length": len(user_query)
                }
            )

        except Exception as e:
            print(f"\n❌ Query failed: {e}")
            raise


# Singleton instance
_unified_adapter_instance = None


def get_gemini_unified_adapter(
    api_key: Optional[str] = None,
    file_search_store_name: Optional[str] = None,
    kg_adapter = None
) -> GeminiUnifiedAdapter:
    """
    Get or create singleton Gemini Unified Adapter instance

    Args:
        api_key: Optional API key
        file_search_store_name: Optional File Search store name
        kg_adapter: Optional KG adapter

    Returns:
        GeminiUnifiedAdapter singleton
    """
    global _unified_adapter_instance

    if _unified_adapter_instance is None:
        _unified_adapter_instance = GeminiUnifiedAdapter(
            api_key=api_key,
            file_search_store_name=file_search_store_name,
            kg_adapter=kg_adapter
        )

    return _unified_adapter_instance
