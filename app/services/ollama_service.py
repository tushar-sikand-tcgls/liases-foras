"""
Ollama Service: Local LLM Integration for Qwen 2.5

This service provides integration with locally-running Ollama models,
specifically optimized for Qwen 2.5 running on your machine.

Key Features:
- No API keys needed (runs locally)
- Fast inference with local GPU/CPU
- Privacy-preserving (data stays on your machine)
- Compatible with existing LLM service interface
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class OllamaConfig:
    """Configuration for Ollama service"""
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:3b"  # Using 3B model for 3-5x faster inference
    temperature: float = 0.3   # Lower temperature for faster, more deterministic responses
    max_tokens: int = 1024     # Reduced from 2048 for faster response
    timeout: int = 300  # seconds - increased to 5 minutes for complex answer composition


class OllamaService:
    """
    Service for interacting with local Ollama models

    Usage:
        ollama_service = OllamaService()
        response = ollama_service.generate("What is the absorption rate?")
    """

    def __init__(self, config: Optional[OllamaConfig] = None):
        """
        Initialize Ollama service

        Args:
            config: OllamaConfig object with custom settings
        """
        self.config = config or OllamaConfig()
        self._verify_ollama_connection()

    def _verify_ollama_connection(self) -> bool:
        """
        Verify that Ollama is running and accessible

        Returns:
            bool: True if connection successful

        Raises:
            ConnectionError: If Ollama is not accessible
        """
        try:
            response = requests.get(f"{self.config.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]

                if self.config.model not in model_names:
                    print(f"⚠️  Warning: Model '{self.config.model}' not found.")
                    print(f"Available models: {', '.join(model_names)}")
                    if model_names:
                        print(f"Using first available model: {model_names[0]}")
                        self.config.model = model_names[0]

                print(f"✅ Connected to Ollama - Using model: {self.config.model}")
                return True
            else:
                raise ConnectionError(f"Ollama returned status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Could not connect to Ollama at {self.config.base_url}. "
                f"Make sure Ollama is running (try: 'ollama serve'). Error: {e}"
            )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        Generate text using Ollama model

        Args:
            prompt: User prompt/question
            system_prompt: Optional system instruction
            temperature: Override default temperature (0.0-1.0)
            max_tokens: Override default max tokens
            stream: Whether to stream the response

        Returns:
            str: Generated text response
        """
        url = f"{self.config.base_url}/api/generate"

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()

            if stream:
                return self._handle_stream_response(response)
            else:
                result = response.json()
                return result.get('response', '')

        except requests.exceptions.Timeout:
            raise TimeoutError(
                f"Ollama request timed out after {self.config.timeout} seconds. "
                f"Try reducing max_tokens or increasing timeout."
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama generation failed: {e}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Chat completion with conversation history

        Args:
            messages: List of message dicts with 'role' and 'content'
                     e.g., [{"role": "user", "content": "Hello"}]
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            str: Model's response
        """
        url = f"{self.config.base_url}/api/chat"

        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens
            }
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()

            result = response.json()
            return result.get('message', {}).get('content', '')

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama chat failed: {e}")

    def generate_with_context(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate response with provided context (for RAG applications)

        Args:
            query: User question
            context: Retrieved context/knowledge
            system_prompt: Optional system instruction

        Returns:
            str: Generated answer based on context
        """
        default_system = """You are a helpful real estate analysis assistant.
Answer questions based on the provided context. If the context doesn't contain
enough information, say so clearly."""

        prompt = f"""Context:
{context}

Question: {query}

Answer based on the context above:"""

        return self.generate(
            prompt=prompt,
            system_prompt=system_prompt or default_system,
            temperature=0.3  # Lower temperature for factual responses
        )

    def _handle_stream_response(self, response) -> str:
        """Handle streaming response from Ollama"""
        full_response = ""
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                if 'response' in chunk:
                    full_response += chunk['response']
        return full_response

    def get_available_models(self) -> List[str]:
        """
        Get list of available Ollama models

        Returns:
            List[str]: Model names
        """
        try:
            response = requests.get(f"{self.config.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m['name'] for m in models]
            return []
        except requests.exceptions.RequestException:
            return []

    def pull_model(self, model_name: str) -> bool:
        """
        Pull/download a model from Ollama registry

        Args:
            model_name: Name of model to pull (e.g., 'qwen2.5:latest')

        Returns:
            bool: True if successful
        """
        url = f"{self.config.base_url}/api/pull"
        payload = {"name": model_name}

        try:
            response = requests.post(url, json=payload, timeout=300)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"Failed to pull model: {e}")
            return False


# Singleton instance for easy import
ollama_service = None

def get_ollama_service(
    model: str = "qwen2.5:latest",
    base_url: str = "http://localhost:11434"
) -> OllamaService:
    """
    Get or create Ollama service singleton

    Args:
        model: Model name to use
        base_url: Ollama server URL

    Returns:
        OllamaService instance
    """
    global ollama_service
    if ollama_service is None:
        config = OllamaConfig(model=model, base_url=base_url)
        ollama_service = OllamaService(config)
    return ollama_service


# Example usage
if __name__ == "__main__":
    # Test the service
    try:
        service = get_ollama_service()

        # Simple generation
        print("Testing simple generation:")
        response = service.generate("What is real estate absorption rate?")
        print(f"Response: {response}\n")

        # Chat with history
        print("Testing chat with history:")
        messages = [
            {"role": "user", "content": "What is PSF in real estate?"},
        ]
        chat_response = service.chat(messages)
        print(f"Chat Response: {chat_response}\n")

        # RAG-style query
        print("Testing RAG-style query:")
        context = "The project has 100 units with an absorption rate of 12% per year."
        query = "What is the absorption rate of this project?"
        rag_response = service.generate_with_context(query, context)
        print(f"RAG Response: {rag_response}")

    except Exception as e:
        print(f"Error: {e}")
