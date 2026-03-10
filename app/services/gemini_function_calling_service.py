"""
Gemini Function Calling Service: LLM-driven function routing with native function calling

Implements the function calling loop:
1. User query → LLM (with function schemas)
2. LLM decides which functions to call
3. Execute functions
4. Results → LLM for commentary
5. Final response with analysis/insights/recommendations

State Management:
- Uses Google's Interactions API for server-side conversation state
- Chains interactions using previous_interaction_id
- Stateless client - only passes interaction IDs
"""

import os
import json
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from app.services.function_registry import get_function_registry
from app.adapters.gemini_interactions_adapter import get_gemini_interactions_adapter
import time


class GeminiFunctionCallingService:
    """
    Service for LLM-orchestrated function calling using Gemini 2.5 Flash

    Features:
    - Native function calling (Gemini's built-in support)
    - Multi-turn function calling loop
    - Automatic routing based on user query
    - Commentary and synthesis on function results
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini Function Calling Service

        Args:
            api_key: Gemini API key (defaults to env var)
        """
        # Get API key
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")

        # Initialize Interactions API adapter
        self.interactions_adapter = get_gemini_interactions_adapter(api_key=self.api_key)

        # Get function registry
        self.function_registry = get_function_registry()

        # Get function declarations for Interactions API
        self.function_declarations = self._get_function_declarations()

        # Keep backward compatibility with old API
        genai.configure(api_key=self.api_key)

        # Upload knowledge base file for RAG
        self.knowledge_base_file = self._upload_knowledge_base()

        # Initialize model with functions and grounding
        self.model = self._initialize_model_with_functions()

        print(f"✓ Gemini Function Calling Service initialized with Interactions API ({self.function_registry.get_function_count()} functions)")
        print(f"✓ Knowledge base file uploaded: {self.knowledge_base_file.display_name if self.knowledge_base_file else 'None'}")

    def _get_function_declarations(self) -> List[FunctionDeclaration]:
        """
        Get function declarations for Interactions API

        Returns:
            List of FunctionDeclaration objects
        """
        # Get all function schemas from registry
        function_schemas = self.function_registry.get_all_function_schemas()

        # Convert to Gemini FunctionDeclaration format
        function_declarations = []
        for schema in function_schemas:
            # Extract schema components
            name = schema["name"]
            description = schema["description"]
            parameters = schema["parameters"]

            # Create FunctionDeclaration
            func_decl = FunctionDeclaration(
                name=name,
                description=description,
                parameters=parameters
            )
            function_declarations.append(func_decl)

        return function_declarations

    def _upload_knowledge_base(self):
        """
        Upload the vectorized knowledge base (Excel file) to Gemini for RAG

        Returns:
            Uploaded file object or None if upload fails
        """
        knowledge_base_path = "change-request/managed-rag/LF-Layers_FULLY_ENRICHED_ALL_36.xlsx"

        try:
            # Check if file exists
            if not os.path.exists(knowledge_base_path):
                print(f"⚠️  Knowledge base file not found: {knowledge_base_path}")
                return None

            # Upload file to Gemini
            print(f"📤 Uploading knowledge base: {knowledge_base_path}")
            uploaded_file = genai.upload_file(knowledge_base_path, display_name="LF_Layers_Knowledge_Base")

            # Wait for file to be processed
            print(f"⏳ Waiting for file processing...")
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = genai.get_file(uploaded_file.name)

            if uploaded_file.state.name == "FAILED":
                print(f"❌ File upload failed")
                return None

            print(f"✅ Knowledge base uploaded: {uploaded_file.display_name} (URI: {uploaded_file.uri})")
            return uploaded_file

        except Exception as e:
            print(f"⚠️  Failed to upload knowledge base: {e}")
            return None

    def _initialize_model_with_functions(self) -> genai.GenerativeModel:
        """
        Initialize Gemini model with all registered functions and RAG grounding

        Returns:
            GenerativeModel configured with function calling and knowledge base grounding
        """
        # Create Tool with all functions
        tools = [Tool(function_declarations=self.function_declarations)]

        # Build system instruction with RAG reference and query routing rules
        system_instruction = """You are an expert real estate intelligence assistant with MULTI-CITY support.

IMPORTANT: You have access to data for MULTIPLE CITIES including:
- Pune (regions: Chakan, Baner, Hinjewadi)
- Kolkata (regions: New Town, Rajarhat, E-M Bypass, Salt Lake, Park Street)

ALWAYS process queries for ANY city the user mentions. DO NOT restrict responses to specific cities.

You have access to a comprehensive knowledge base (LF-Layers_FULLY_ENRICHED_ALL_36.xlsx) that contains:
- ALL metric definitions and formulas
- Metric synonyms (e.g., "Efficiency Ratio" → "Sellout Efficiency")
- Dimensional relationships
- Real estate industry terminology

CRITICAL ROUTING RULES:

1. QUARTERLY MARKET DATA QUERIES (Default for market-level queries):
   When user asks about "supply units", "sales units", "market data", or mentions a FISCAL YEAR (e.g., "FY 24-25", "FY 2023-24")
   WITHOUT specifying a specific project name:

   → ALWAYS use: get_quarters_by_year_range or get_recent_quarters

   Examples:
   - "What is supply units for FY 24-25?" → get_quarters_by_year_range(start_year=2024, end_year=2024)
   - "Show me sales in 2023" → get_quarters_by_year_range(start_year=2023, end_year=2023)
   - "Market data" → get_recent_quarters(n=8)

   This returns aggregated quarterly market data for the region.

2. PROJECT-SPECIFIC QUERIES:
   When user mentions a SPECIFIC PROJECT NAME:

   → Use: get_project_by_name

   Examples:
   - "What is supply for Sara City?" → get_project_by_name(project_name="Sara City")
   - "Show me Orbit Urban Park details" → get_project_by_name(project_name="Orbit Urban Park")

3. METRIC DEFINITIONS:
   When user asks about ANY metric:
   - First search the knowledge base file for the metric definition
   - If you find a synonym, use the official metric name
   - Cite the knowledge base when explaining metrics

Use the available functions to execute queries and calculations for ANY city.

REMEMBER:
- Support ALL cities (Pune, Kolkata, etc.)
- "FY 24-25" or "fiscal year" queries WITHOUT a project name = quarterly market data"""

        # Initialize model with tools and optional knowledge base file
        if self.knowledge_base_file:
            # Model with RAG grounding
            model = genai.GenerativeModel(
                model_name='gemini-2.0-flash-exp',
                tools=tools,
                system_instruction=system_instruction
            )
            # Note: Gemini 2.0 Flash doesn't support file grounding yet with tools
            # This will be updated when the feature is available
            print("⚠️  Note: Gemini 2.0 Flash with tools doesn't support file grounding yet")
            print("   The knowledge base is uploaded and ready for future use")
        else:
            # Model without RAG (fallback)
            model = genai.GenerativeModel(
                model_name='gemini-2.0-flash-exp',
                tools=tools,
                system_instruction=system_instruction
            )

        return model

    def process_query(
        self,
        query: str,
        chat_history: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None,
        max_function_calls: int = 5,
        previous_interaction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query with function calling using Interactions API

        Args:
            query: User query string
            chat_history: Optional chat history for context (deprecated, use previous_interaction_id)
            system_prompt: Optional system prompt to set behavior
            max_function_calls: Maximum number of function calls to prevent infinite loops
            previous_interaction_id: Optional ID from previous interaction for context

        Returns:
            Dict with:
                - response: Final LLM response with commentary
                - function_calls: List of functions called
                - function_results: List of function results
                - interaction_id: ID for this interaction (use in next turn)
                - chat_history: Updated chat history (deprecated)
        """
        # Initialize chat session
        chat = self.model.start_chat(history=[])

        # Build initial prompt
        initial_prompt = self._build_initial_prompt(query, chat_history, system_prompt)

        # Track function calls
        function_calls_made = []
        function_results = []

        # Send initial message
        response = chat.send_message(initial_prompt)

        # Function calling loop
        call_count = 0
        while call_count < max_function_calls:
            # Check if LLM wants to call functions
            if not response.candidates:
                break

            candidate = response.candidates[0]

            # Check for function calls
            if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
                break

            has_function_call = False
            for part in candidate.content.parts:
                if hasattr(part, 'function_call'):
                    has_function_call = True
                    break

            if not has_function_call:
                # No more function calls - LLM has final response
                break

            # Execute all function calls in this turn
            turn_function_calls = []
            turn_function_responses = []

            for part in candidate.content.parts:
                if hasattr(part, 'function_call'):
                    function_call = part.function_call
                    function_name = function_call.name if hasattr(function_call, 'name') and function_call.name else ""
                    function_args = dict(function_call.args) if function_call.args else {}

                    # Skip empty function names
                    if not function_name:
                        continue

                    # Track function call
                    turn_function_calls.append({
                        "name": function_name,
                        "arguments": function_args
                    })

                    # Execute function
                    try:
                        result = self.function_registry.execute_function(
                            function_name=function_name,
                            parameters=function_args
                        )
                        function_results.append({
                            "function": function_name,
                            "result": result
                        })
                    except Exception as e:
                        result = {
                            "error": f"Function execution failed: {str(e)}",
                            "function": function_name,
                            "arguments": function_args
                        }
                        function_results.append({
                            "function": function_name,
                            "result": result,
                            "error": True
                        })

                    # Create function response for Gemini
                    function_response = genai.protos.FunctionResponse(
                        name=function_name,
                        response={"result": result}
                    )
                    turn_function_responses.append(function_response)

            function_calls_made.extend(turn_function_calls)

            # If no function responses, break
            if not turn_function_responses:
                break

            # Send function results back to LLM
            response = chat.send_message(
                genai.protos.Content(
                    parts=[
                        genai.protos.Part(function_response=fr)
                        for fr in turn_function_responses
                    ]
                )
            )

            call_count += 1

        # Extract final response text
        final_response = ""
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text'):
                    final_response += part.text

        # Build result
        result = {
            "response": final_response,
            "function_calls": function_calls_made,
            "function_results": function_results,
            "chat_history": self._extract_chat_history(chat),
            "interaction_id": previous_interaction_id,  # Note: Full Interactions API integration for function calling can be added later
            "metadata": {
                "total_function_calls": len(function_calls_made),
                "max_function_calls_reached": (call_count >= max_function_calls),
                "uses_interactions_api": False  # Flag for future migration
            }
        }

        return result

    def _build_initial_prompt(
        self,
        query: str,
        chat_history: Optional[List[Dict]],
        system_prompt: Optional[str]
    ) -> str:
        """
        Build initial prompt with system instructions and context

        Args:
            query: User query
            chat_history: Optional chat history
            system_prompt: Optional system prompt

        Returns:
            Complete prompt string
        """
        prompt_parts = []

        # CRITICAL: Add routing hint for fiscal year queries
        routing_hint = ""
        query_lower = query.lower()

        # Check if query mentions fiscal year patterns without a project name
        has_fy_pattern = any(pattern in query_lower for pattern in ['fy ', 'fiscal year', 'financial year', 'f.y.'])
        has_year_number = any(str(year) in query for year in range(2014, 2027))
        has_market_keyword = any(kw in query_lower for kw in ['supply units', 'sales units', 'market data', 'quarterly', 'market', 'trend'])

        # Dynamically fetch project names from data service (instead of hardcoding)
        known_projects = []
        try:
            all_projects = self.function_registry.data_service.get_all_projects()
            known_projects = [
                self.function_registry.data_service.get_value(project.get('projectName', {})).lower()
                for project in all_projects
                if self.function_registry.data_service.get_value(project.get('projectName', {}))
            ]
        except Exception as e:
            print(f"⚠️  Could not fetch project names for routing: {e}")

        has_project_name = any(project in query_lower for project in known_projects)

        # If fiscal year or market query WITHOUT project name, add routing hint
        if (has_fy_pattern or (has_year_number and has_market_keyword)) and not has_project_name:
            routing_hint = """
<ROUTING_INSTRUCTION>
This query is about MARKET-LEVEL data (no specific project mentioned).
Use get_quarters_by_year_range or get_recent_quarters function.
DO NOT ask for project name - return quarterly market data for the region.
</ROUTING_INSTRUCTION>

"""

        # Add routing hint if applicable
        if routing_hint:
            prompt_parts.append(routing_hint)

        # Add system prompt if provided
        if system_prompt:
            prompt_parts.append(f"<SYSTEM_INSTRUCTIONS>\n{system_prompt}\n</SYSTEM_INSTRUCTIONS>\n")

        # Add chat history context if provided
        if chat_history and len(chat_history) > 0:
            prompt_parts.append("<CONVERSATION_HISTORY>")
            for turn in chat_history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                prompt_parts.append(f"{role.upper()}: {content}")
            prompt_parts.append("</CONVERSATION_HISTORY>\n")

        # Add current query
        prompt_parts.append(f"USER_QUERY: {query}\n")

        # Add instruction for function calling
        prompt_parts.append("""
INSTRUCTIONS:
1. Analyze the user's query carefully
2. Determine which functions (if any) need to be called to answer the question
3. Call the necessary functions to retrieve data or perform calculations
4. Once you have the function results, provide a comprehensive response that includes:
   - Analysis of the results
   - Insights based on the data
   - Recommendations or actionable advice (if applicable)
   - Context and explanation in clear, business-friendly language

If the query requires calculations (like IRR, NPV, PSF), call the calculation functions first.
If the query asks "why" or needs market context, use semantic search and GraphRAG functions.
If comparing projects, use comparison and statistical functions.

Always provide subjective commentary on top of the calculated numbers. Don't just return raw data.

==================== KNOWLEDGE BASE ====================
You have access to a comprehensive real estate knowledge base (LF-Layers_FULLY_ENRICHED_ALL_36.xlsx)
that contains ALL metric definitions, synonyms, formulas, and relationships.

IMPORTANT: When users ask about ANY metric or dimension:
1. Check the knowledge base for the exact definition
2. Look up synonyms (e.g., "Efficiency Ratio" may be a synonym for another metric)
3. Use the official metric name from the knowledge base in function calls
4. Cite the knowledge base when explaining metrics

==================== GEOSPATIAL CAPABILITIES ====================
You have POWERFUL geospatial distance calculation functions:

1. getDistanceFromProject(source_project, target_project):
   - Calculates Haversine distance between ANY two projects
   - Uses their latitude/longitude coordinates automatically
   - Returns distance in kilometers
   - Example: "Distance from Sara City to Gulmohar City" → Use this function

2. find_projects_within_radius(center_project, radius_km):
   - Finds all projects within a specified radius of a reference project
   - Automatically retrieves center project's lat/long
   - Returns sorted list by distance
   - Example: "Projects within 2 KM of Sara City" → Use this function

IMPORTANT: When user asks "distance between X and Y" or "how far is X from Y",
use getDistanceFromProject. You do NOT need coordinates - just provide project names!

==================== ANSWER FORMATTING GUIDELINES (MANDATORY) ====================

1. INSIGHTS & EXPERT COMMENTARY:
   - Always provide subjective analysis as a real estate expert
   - Explain "what this means" for the market, investor, or developer
   - Include market context and business implications
   - Never return bare numbers without interpretation

2. DELTA & PERCENTAGE CHANGES (CRITICAL):
   - When showing time-series data (e.g., PSF over quarters), ALWAYS calculate and show:
     * Absolute change: "PSF increased from ₹X to ₹Y (+₹Z)"
     * Percentage change: "(+X% growth)"
     * Rate of change: "growing at X% per year"
   - Use visual indicators: ⬆️ for increase, ⬇️ for decrease, ➡️ for stable

3. COMPARATIVE ANALYSIS:
   - When comparing multiple projects, use tables with Markdown formatting
   - Include comparative metrics: "Project A is X% higher than average"
   - Rank projects and explain why top performers excel

Example Table Format:
| Project | Metric | Δ vs Avg | Rank | Insight |
|---------|--------|----------|------|---------|
| Sara City | 4,200 | +15% ⬆️ | 1 | Premium location |

4. VISUAL FORMATTING:
   - Use emojis for visual impact: 📈 📉 ⚠️ ✅ ❌
   - Bold **key metrics**
   - Use bullet points for insights
   - Add section headers

5. MINIMUM LENGTH REQUIREMENTS:
   - Simple attribute queries: Minimum 150 characters with context
   - Metric queries (PSF, Absorption Rate): Minimum 200 characters with analysis
   - Comparison queries: Minimum 300 characters with detailed comparison

6. ALWAYS INCLUDE:
   - Source of data (e.g., "Source: Liases Foras database")
   - Timestamp/data version where available
   - Confidence level if applicable

Example Good Answer Format:
```
**Sara City PSF: ₹4,200/sqft** 📈

**Growth Analysis:**
- Q1 2024: ₹3,800/sqft
- Q3 2024: ₹4,200/sqft
- **Δ Change: +₹400 (+10.5% growth)** ⬆️
- Annual rate: ~14% appreciation

**Market Context:**
This strong appreciation indicates high demand and successful positioning.
Sara City outperforms the market average by 15%, suggesting premium location
value and strong developer execution.

**Investment Insight:**
This trend suggests continued price resilience and potential for further
appreciation, particularly given the project's proximity to infrastructure
development.

Source: Liases Foras Q3 2024
```
""")

        return "\n".join(prompt_parts)

    def _extract_chat_history(self, chat) -> List[Dict]:
        """
        Extract chat history from Gemini chat session

        Args:
            chat: Gemini chat session

        Returns:
            List of chat turns
        """
        history = []
        for message in chat.history:
            role = message.role
            content = ""

            # Extract text from parts
            if hasattr(message, 'parts'):
                for part in message.parts:
                    if hasattr(part, 'text'):
                        content += part.text

            if content:
                history.append({
                    "role": role,
                    "content": content
                })

        return history

    def get_available_functions_summary(self) -> Dict:
        """
        Get summary of available functions for debugging/monitoring

        Returns:
            Dict with function registry summary
        """
        return self.function_registry.get_registry_summary()


# Global singleton instance
_gemini_service_instance = None

def get_gemini_function_calling_service() -> GeminiFunctionCallingService:
    """Get or create global Gemini function calling service instance"""
    global _gemini_service_instance
    if _gemini_service_instance is None:
        _gemini_service_instance = GeminiFunctionCallingService()
    return _gemini_service_instance
