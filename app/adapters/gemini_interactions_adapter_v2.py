"""
Gemini Interactions API Adapter V2 - Rewritten from Official Examples

This is a complete rewrite based on official Google documentation:
https://ai.google.dev/gemini-api/docs/interactions

Key Changes from V1:
- Tools passed as raw dict (not types.Tool)
- Response parsing uses outputs[-1].text pattern
- Function calling follows official format
- Simplified error handling
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    from google import genai
    INTERACTIONS_API_AVAILABLE = True
except ImportError:
    INTERACTIONS_API_AVAILABLE = False
    genai = None
    print("⚠️  WARNING: google-genai package not installed.")
    print("⚠️  Install with: pip install google-genai")


@dataclass
class InteractionResult:
    """Result from an interaction with Gemini"""
    interaction_id: str
    text_response: str
    function_calls: List[Dict]
    status: str
    usage: Optional[Dict] = None


class GeminiInteractionsAdapterV2:
    """
    Gemini Interactions API wrapper - Rewritten from official examples

    Official docs: https://ai.google.dev/gemini-api/docs/interactions
    """

    def __init__(self, api_key: Optional[str] = None, default_model: str = "gemini-2.5-flash"):
        """
        Initialize Gemini Interactions API adapter

        Args:
            api_key: Optional Google API key (defaults to env var)
            default_model: Default model to use
        """
        # Get API key
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")

        # Check if Interactions API is available
        if not INTERACTIONS_API_AVAILABLE:
            raise ImportError(
                "Interactions API not available. Install google-genai package:\n"
                "pip install google-genai"
            )

        # Initialize client (official pattern)
        self.client = genai.Client(api_key=self.api_key)
        self.default_model = default_model

        print(f"✅ Gemini Interactions API V2 initialized (model: {default_model})")

    def create_interaction(
        self,
        input_text: str,
        model: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        previous_interaction_id: Optional[str] = None
    ) -> InteractionResult:
        """
        Create a new interaction (official pattern from docs)

        Args:
            input_text: User's input message
            model: Model to use (defaults to self.default_model)
            tools: Optional list of tool definitions (as raw dicts)
            previous_interaction_id: Optional ID to continue conversation

        Returns:
            InteractionResult with interaction_id and response

        Example (from official docs):
            >>> adapter = GeminiInteractionsAdapterV2()
            >>> result = adapter.create_interaction("Tell me a joke")
            >>> print(result.text_response)
        """
        model_name = model or self.default_model

        # Build interaction parameters (official pattern)
        params = {
            "model": model_name,
            "input": input_text
        }

        # Add optional parameters
        if tools:
            params["tools"] = tools

        if previous_interaction_id:
            params["previous_interaction_id"] = previous_interaction_id

        # Create interaction (official API call)
        try:
            interaction = self.client.interactions.create(**params)
            return self._parse_interaction(interaction)
        except Exception as e:
            print(f"❌ Interaction creation failed: {e}")
            raise

    def create_interaction_with_function_calling(
        self,
        input_text: str,
        function_definitions: List[Dict],
        model: Optional[str] = None,
        previous_interaction_id: Optional[str] = None
    ) -> InteractionResult:
        """
        Create interaction with function calling enabled

        Args:
            input_text: User's input message
            function_definitions: List of function schemas (raw dicts)
            model: Model to use
            previous_interaction_id: Optional ID to continue conversation

        Returns:
            InteractionResult with function calls (if any)

        Example (from official docs):
            >>> weather_tool = {
            ...     "type": "function",
            ...     "name": "get_weather",
            ...     "description": "Gets weather for a location",
            ...     "parameters": {
            ...         "type": "object",
            ...         "properties": {
            ...             "location": {
            ...                 "type": "string",
            ...                 "description": "City and state"
            ...             }
            ...         },
            ...         "required": ["location"]
            ...     }
            ... }
            >>> result = adapter.create_interaction_with_function_calling(
            ...     "What's the weather in Paris?",
            ...     [weather_tool]
            ... )
        """
        # Tools are passed as-is (official pattern)
        return self.create_interaction(
            input_text=input_text,
            model=model,
            tools=function_definitions,
            previous_interaction_id=previous_interaction_id
        )

    def send_function_result(
        self,
        previous_interaction_id: str,
        function_name: str,
        call_id: str,
        result: Any,
        model: Optional[str] = None
    ) -> InteractionResult:
        """
        Send function execution result back to model

        Args:
            previous_interaction_id: ID from function call interaction
            function_name: Name of the function that was called
            call_id: ID of the function call (from output.id)
            result: Result from function execution
            model: Model to use

        Returns:
            InteractionResult with model's synthesis of function result

        Example (from official docs):
            >>> # After function call detected
            >>> result = adapter.send_function_result(
            ...     previous_interaction_id=interaction.id,
            ...     function_name="get_weather",
            ...     call_id=output.id,
            ...     result="The weather in Paris is sunny."
            ... )
        """
        model_name = model or self.default_model

        # Build function result input (official pattern from docs)
        function_result_input = [{
            "type": "function_result",
            "name": function_name,
            "call_id": call_id,
            "result": str(result)  # Convert to string for API
        }]

        # Create interaction with function result
        try:
            interaction = self.client.interactions.create(
                model=model_name,
                previous_interaction_id=previous_interaction_id,
                input=function_result_input
            )
            return self._parse_interaction(interaction)
        except Exception as e:
            print(f"❌ Function result submission failed: {e}")
            raise

    def get_interaction(self, interaction_id: str) -> Dict[str, Any]:
        """
        Retrieve a past interaction by ID (official pattern)

        Args:
            interaction_id: ID of the interaction to retrieve

        Returns:
            Full interaction object

        Example:
            >>> previous = adapter.get_interaction("abc123")
            >>> print(previous["id"])
        """
        try:
            interaction = self.client.interactions.get(interaction_id)
            return {
                "id": interaction.id,
                "model": getattr(interaction, 'model', None),
                "outputs": [self._parse_output(out) for out in interaction.outputs] if hasattr(interaction, 'outputs') else [],
                "status": getattr(interaction, 'status', None),
                "usage": self._parse_usage(interaction.usage) if hasattr(interaction, 'usage') else None,
            }
        except Exception as e:
            print(f"❌ Failed to retrieve interaction {interaction_id}: {e}")
            raise

    def _parse_interaction(self, interaction) -> InteractionResult:
        """
        Parse interaction response (official pattern: outputs[-1].text)

        Args:
            interaction: Raw interaction object from Gemini API

        Returns:
            InteractionResult with parsed data
        """
        # Official pattern: use outputs[-1] for latest response
        text_response = ""
        function_calls = []

        if hasattr(interaction, 'outputs') and interaction.outputs:
            for output in interaction.outputs:
                # Official pattern: check output.type
                if hasattr(output, 'type'):
                    if output.type == "text" and hasattr(output, 'text'):
                        text_response += output.text
                    elif output.type == "function_call":
                        # Function call detected (official format)
                        function_calls.append({
                            "name": getattr(output, 'name', ''),
                            "arguments": dict(output.arguments) if hasattr(output, 'arguments') else {},
                            "id": getattr(output, 'id', None)
                        })

        # Parse usage
        usage = None
        if hasattr(interaction, 'usage'):
            usage = self._parse_usage(interaction.usage)

        return InteractionResult(
            interaction_id=interaction.id,
            text_response=text_response.strip(),
            function_calls=function_calls,
            status=getattr(interaction, 'status', 'completed'),
            usage=usage
        )

    def _parse_output(self, output) -> Dict:
        """Parse output object into dict"""
        result = {"type": getattr(output, 'type', 'unknown')}

        if hasattr(output, 'text'):
            result['text'] = output.text

        if hasattr(output, 'name'):
            result['name'] = output.name

        if hasattr(output, 'arguments'):
            result['arguments'] = dict(output.arguments)

        return result

    def _parse_usage(self, usage) -> Dict:
        """Parse usage metadata into dict"""
        if not usage:
            return None

        return {
            "prompt_tokens": getattr(usage, 'prompt_token_count', 0),
            "candidates_tokens": getattr(usage, 'candidates_token_count', 0),
            "total_tokens": getattr(usage, 'total_token_count', 0),
            "cached_tokens": getattr(usage, 'cached_content_token_count', 0)
        }


# Global singleton instance
_gemini_interactions_adapter_v2 = None


def get_gemini_interactions_adapter_v2(api_key: Optional[str] = None) -> GeminiInteractionsAdapterV2:
    """
    Get or create global Gemini Interactions API V2 adapter instance

    Args:
        api_key: Optional Google API key

    Returns:
        GeminiInteractionsAdapterV2 singleton instance
    """
    global _gemini_interactions_adapter_v2

    if _gemini_interactions_adapter_v2 is None:
        _gemini_interactions_adapter_v2 = GeminiInteractionsAdapterV2(api_key=api_key)

    return _gemini_interactions_adapter_v2
