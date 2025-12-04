"""
Gemini Function Calling Service: LLM-driven function routing with native function calling

Implements the function calling loop:
1. User query → LLM (with function schemas)
2. LLM decides which functions to call
3. Execute functions
4. Results → LLM for commentary
5. Final response with analysis/insights/recommendations
"""

import os
import json
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from app.services.function_registry import get_function_registry


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

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Get function registry
        self.function_registry = get_function_registry()

        # Initialize Gemini model with function calling
        self.model = self._initialize_model_with_functions()

        print(f"✓ Gemini Function Calling Service initialized with {self.function_registry.get_function_count()} functions")

    def _initialize_model_with_functions(self) -> genai.GenerativeModel:
        """
        Initialize Gemini model with all registered functions

        Returns:
            GenerativeModel configured with function calling
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

        # Create Tool with all functions
        tools = [Tool(function_declarations=function_declarations)]

        # Initialize model with tools
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            tools=tools
        )

        return model

    def process_query(
        self,
        query: str,
        chat_history: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None,
        max_function_calls: int = 5
    ) -> Dict[str, Any]:
        """
        Process a user query with function calling

        Args:
            query: User query string
            chat_history: Optional chat history for context
            system_prompt: Optional system prompt to set behavior
            max_function_calls: Maximum number of function calls to prevent infinite loops

        Returns:
            Dict with:
                - response: Final LLM response with commentary
                - function_calls: List of functions called
                - function_results: List of function results
                - chat_history: Updated chat history
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
                    function_name = function_call.name
                    function_args = dict(function_call.args)

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
            "metadata": {
                "total_function_calls": len(function_calls_made),
                "max_function_calls_reached": (call_count >= max_function_calls)
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
