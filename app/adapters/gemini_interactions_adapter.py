"""
Gemini Interactions API Adapter - Stateful Conversation Management

This adapter uses Google's Interactions API (Beta) for server-side conversation state.
Instead of manually managing chat history, we use interaction_id chaining.

Key Features:
- Server-side state management via Interactions API
- Stateless client design - only pass interaction_id
- Implicit caching for cost/speed optimization
- Support for reloading conversation history
- Multi-turn conversation with automatic context

API Pattern:
- First turn: client.interactions.create() → returns interaction.id
- Subsequent turns: client.interactions.create(previous_interaction_id=...) → returns new interaction.id
- Reload: client.interactions.get(interaction_id) → retrieves full history

References:
https://ai.google.dev/gemini-api/docs/interactions
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

# Try to import new Interactions API SDK
try:
    from google import genai
    from google.genai.types import Tool, FunctionDeclaration
    INTERACTIONS_API_AVAILABLE = True
except (ImportError, AttributeError):
    # Fallback to old SDK if new one not available
    INTERACTIONS_API_AVAILABLE = False
    genai = None
    Tool = None
    FunctionDeclaration = None
    print("⚠️  WARNING: google-genai package not installed. Interactions API not available.")
    print("⚠️  Install with: pip install google-genai")
    print("⚠️  Falling back to manual state management.")


@dataclass
class InteractionResult:
    """Result from an interaction with Gemini"""
    interaction_id: str
    text_response: str
    function_calls: List[Dict]
    status: str
    usage: Optional[Dict] = None
    outputs: Optional[List] = None


class GeminiInteractionsAdapter:
    """
    Gemini Interactions API wrapper for stateful conversation management

    This adapter provides helpers for:
    - Starting new conversations (startInteraction)
    - Continuing existing conversations (continueInteraction)
    - Reloading conversation history (getInteraction)
    - Function calling with automatic state management

    The adapter is stateless - it doesn't store conversation state internally.
    Instead, it relies on Google's server-side state management via interaction IDs.
    """

    def __init__(self, api_key: Optional[str] = None, default_model: str = "gemini-2.5-flash"):
        """
        Initialize Gemini Interactions API adapter

        Args:
            api_key: Optional Google API key (defaults to env var)
            default_model: Default model to use for interactions
        """
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")

        # Check if Interactions API is available
        if not INTERACTIONS_API_AVAILABLE:
            raise ImportError(
                "Interactions API not available. Install google-genai package:\n"
                "pip install google-genai\n\n"
                "Alternatively, use GeminiLLMAdapter without previous_interaction_id parameter."
            )

        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)
        self.default_model = default_model

        print(f"✅ Gemini Interactions API adapter initialized (model: {default_model})")

    def start_interaction(
        self,
        input_text: str,
        model: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        system_instruction: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> InteractionResult:
        """
        Start a new conversation interaction (first turn)

        This creates a new interaction without a previous_interaction_id.
        Returns an interaction_id that should be used for subsequent turns.

        Args:
            input_text: User's input message
            model: Model to use (defaults to self.default_model)
            tools: Optional list of tools/functions for function calling
            system_instruction: Optional system prompt
            config: Optional generation config (temperature, etc.)

        Returns:
            InteractionResult with interaction_id and response

        Example:
            >>> adapter = GeminiInteractionsAdapter()
            >>> result = adapter.start_interaction("What is IRR?")
            >>> print(result.interaction_id)  # Save this for next turn
            >>> print(result.text_response)
        """
        model_name = model or self.default_model

        # Build interaction parameters
        params = {
            "model": model_name,
            "input": input_text
        }

        # Add optional parameters
        if tools:
            params["tools"] = tools

        # Note: system_instruction and config not supported in current Interactions API version
        # They will be added in future versions
        if system_instruction:
            print(f"⚠️  system_instruction not yet supported in Interactions API (will be ignored)")

        if config:
            print(f"⚠️  config parameter not yet supported in Interactions API (will be ignored)")

        # Create interaction
        try:
            interaction = self.client.interactions.create(**params)
            return self._parse_interaction(interaction)
        except Exception as e:
            print(f"❌ Interaction creation failed: {e}")
            raise

    def continue_interaction(
        self,
        previous_interaction_id: str,
        input_text: str,
        model: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        config: Optional[Dict] = None
    ) -> InteractionResult:
        """
        Continue an existing conversation (subsequent turns)

        This creates a new interaction linked to the previous one via previous_interaction_id.
        The conversation context is automatically maintained server-side by Google.

        Args:
            previous_interaction_id: ID from the previous interaction
            input_text: User's input message
            model: Model to use (defaults to self.default_model)
            tools: Optional list of tools/functions
            config: Optional generation config

        Returns:
            InteractionResult with new interaction_id and response

        Example:
            >>> # First turn
            >>> result1 = adapter.start_interaction("My name is Phil")
            >>>
            >>> # Second turn - links to first
            >>> result2 = adapter.continue_interaction(
            ...     previous_interaction_id=result1.interaction_id,
            ...     input_text="What's my name?"
            ... )
            >>> print(result2.text_response)  # "Your name is Phil"
        """
        model_name = model or self.default_model

        # Build interaction parameters with previous_interaction_id
        params = {
            "model": model_name,
            "input": input_text,
            "previous_interaction_id": previous_interaction_id
        }

        # Add optional parameters
        if tools:
            params["tools"] = tools

        # Note: config not supported in current Interactions API version
        if config:
            print(f"⚠️  config parameter not yet supported in Interactions API (will be ignored)")

        # Create chained interaction
        try:
            interaction = self.client.interactions.create(**params)
            return self._parse_interaction(interaction)
        except Exception as e:
            print(f"❌ Interaction continuation failed: {e}")
            raise

    def get_interaction(self, interaction_id: str) -> Dict[str, Any]:
        """
        Retrieve a past interaction by ID

        Useful for:
        - Reloading conversation history after app restart
        - Debugging conversation flow
        - Auditing model responses

        Args:
            interaction_id: ID of the interaction to retrieve

        Returns:
            Full interaction object with inputs, outputs, and metadata

        Example:
            >>> interaction = adapter.get_interaction("abc123")
            >>> print(interaction["inputs"])
            >>> print(interaction["outputs"])
        """
        try:
            interaction = self.client.interactions.get(interaction_id)
            return {
                "id": interaction.id,
                "model": interaction.model if hasattr(interaction, 'model') else None,
                "outputs": [self._parse_content(out) for out in interaction.outputs] if hasattr(interaction, 'outputs') else [],
                "status": interaction.status if hasattr(interaction, 'status') else None,
                "usage": self._parse_usage(interaction.usage) if hasattr(interaction, 'usage') else None,
                "created": interaction.created if hasattr(interaction, 'created') else None,
                "updated": interaction.updated if hasattr(interaction, 'updated') else None,
                "previous_interaction_id": interaction.previous_interaction_id if hasattr(interaction, 'previous_interaction_id') else None
            }
        except Exception as e:
            print(f"❌ Failed to retrieve interaction {interaction_id}: {e}")
            raise

    def start_interaction_with_functions(
        self,
        input_text: str,
        function_declarations: List[FunctionDeclaration],
        system_instruction: Optional[str] = None,
        model: Optional[str] = None
    ) -> InteractionResult:
        """
        Start a new interaction with function calling enabled

        Args:
            input_text: User's input message
            function_declarations: List of function schemas for the model to call
            system_instruction: Optional system prompt
            model: Model to use

        Returns:
            InteractionResult with function calls (if any) and response
        """
        tools = [Tool(function_declarations=function_declarations)]

        return self.start_interaction(
            input_text=input_text,
            model=model,
            tools=tools,
            system_instruction=system_instruction
        )

    def continue_interaction_with_functions(
        self,
        previous_interaction_id: str,
        input_text: str,
        function_declarations: List[FunctionDeclaration],
        model: Optional[str] = None
    ) -> InteractionResult:
        """
        Continue an interaction with function calling enabled

        Args:
            previous_interaction_id: ID from previous interaction
            input_text: User's input message
            function_declarations: List of function schemas
            model: Model to use

        Returns:
            InteractionResult with function calls (if any) and response
        """
        tools = [Tool(function_declarations=function_declarations)]

        return self.continue_interaction(
            previous_interaction_id=previous_interaction_id,
            input_text=input_text,
            model=model,
            tools=tools
        )

    def _parse_interaction(self, interaction) -> InteractionResult:
        """
        Parse Gemini interaction response into structured result

        Args:
            interaction: Raw interaction object from Gemini API

        Returns:
            InteractionResult with parsed data
        """
        # Extract text response from outputs (official pattern: outputs[-1].text)
        text_response = ""
        function_calls = []

        if hasattr(interaction, 'outputs') and interaction.outputs:
            for output in interaction.outputs:
                # Check output type (official API uses .type attribute)
                if hasattr(output, 'type'):
                    if output.type == "text" and hasattr(output, 'text'):
                        text_response += output.text
                    elif output.type == "function_call":
                        # Function call detected
                        function_calls.append({
                            "name": output.name if hasattr(output, 'name') else "",
                            "arguments": dict(output.arguments) if hasattr(output, 'arguments') else {},
                            "id": output.id if hasattr(output, 'id') else None
                        })
                else:
                    # Fallback for older format
                    if hasattr(output, 'text') and output.text:
                        text_response += output.text

                    # Extract function calls from parts (older format)
                    if hasattr(output, 'parts'):
                        for part in output.parts:
                            if hasattr(part, 'function_call'):
                                function_calls.append({
                                    "name": part.function_call.name,
                                    "arguments": dict(part.function_call.args)
                                })

        # Parse usage metadata
        usage = None
        if hasattr(interaction, 'usage'):
            usage = self._parse_usage(interaction.usage)

        return InteractionResult(
            interaction_id=interaction.id,
            text_response=text_response.strip(),
            function_calls=function_calls,
            status=interaction.status if hasattr(interaction, 'status') else "completed",
            usage=usage,
            outputs=interaction.outputs if hasattr(interaction, 'outputs') else None
        )

    def _parse_content(self, content) -> Dict:
        """Parse content object into dict"""
        result = {}

        if hasattr(content, 'text') and content.text:
            result['text'] = content.text

        if hasattr(content, 'parts'):
            result['parts'] = []
            for part in content.parts:
                part_dict = {}
                if hasattr(part, 'text'):
                    part_dict['text'] = part.text
                if hasattr(part, 'function_call'):
                    part_dict['function_call'] = {
                        'name': part.function_call.name,
                        'args': dict(part.function_call.args)
                    }
                if hasattr(part, 'function_response'):
                    part_dict['function_response'] = {
                        'name': part.function_response.name,
                        'response': part.function_response.response
                    }
                result['parts'].append(part_dict)

        return result

    def _parse_usage(self, usage) -> Dict:
        """Parse usage metadata into dict"""
        if not usage:
            return None

        return {
            "prompt_tokens": usage.prompt_token_count if hasattr(usage, 'prompt_token_count') else 0,
            "candidates_tokens": usage.candidates_token_count if hasattr(usage, 'candidates_token_count') else 0,
            "total_tokens": usage.total_token_count if hasattr(usage, 'total_token_count') else 0,
            "cached_tokens": usage.cached_content_token_count if hasattr(usage, 'cached_content_token_count') else 0
        }


# Global singleton instance
_gemini_interactions_adapter = None


def get_gemini_interactions_adapter(api_key: Optional[str] = None) -> GeminiInteractionsAdapter:
    """
    Get or create global Gemini Interactions API adapter instance

    Args:
        api_key: Optional Google API key

    Returns:
        GeminiInteractionsAdapter singleton instance
    """
    global _gemini_interactions_adapter

    if _gemini_interactions_adapter is None:
        _gemini_interactions_adapter = GeminiInteractionsAdapter(api_key=api_key)

    return _gemini_interactions_adapter
