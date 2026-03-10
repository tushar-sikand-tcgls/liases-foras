"""
LLM Factory: Unified interface for switching between LLM providers

This factory allows you to easily switch between:
- Gemini (cloud-based, requires API key)
- Ollama (local, no API key needed)
- Future providers (OpenAI, Claude, etc.)

Usage:
    from app.services.llm_factory import get_llm

    # Use Ollama (local Qwen 2.5)
    llm = get_llm(provider="ollama")
    response = llm.generate("What is absorption rate?")

    # Use Gemini (cloud)
    llm = get_llm(provider="gemini")
    response = llm.generate("What is absorption rate?")
"""

import os
from typing import Literal, Optional
from abc import ABC, abstractmethod


LLMProvider = Literal["gemini", "ollama", "openai"]


class BaseLLM(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text from prompt"""
        pass

    @abstractmethod
    def chat(
        self,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Chat with conversation history"""
        pass


class OllamaLLM(BaseLLM):
    """Ollama LLM wrapper"""

    def __init__(self, model: str = "qwen2.5:latest", base_url: str = "http://localhost:11434"):
        from app.services.ollama_service import get_ollama_service, OllamaConfig
        config = OllamaConfig(model=model, base_url=base_url)
        self.service = get_ollama_service(model=model, base_url=base_url)
        self.provider_name = "Ollama Qwen 2.5 (Local)"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        return self.service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def chat(
        self,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        return self.service.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )


class GeminiLLM(BaseLLM):
    """Gemini LLM wrapper"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.provider_name = "Google Gemini (Cloud)"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        generation_config = {}
        if temperature is not None:
            generation_config['temperature'] = temperature
        if max_tokens is not None:
            generation_config['max_output_tokens'] = max_tokens

        response = self.model.generate_content(
            full_prompt,
            generation_config=generation_config if generation_config else None
        )
        return response.text

    def chat(
        self,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        # Convert messages to Gemini format
        chat = self.model.start_chat(history=[])

        generation_config = {}
        if temperature is not None:
            generation_config['temperature'] = temperature
        if max_tokens is not None:
            generation_config['max_output_tokens'] = max_tokens

        # Send all messages
        for msg in messages:
            if msg['role'] == 'user':
                response = chat.send_message(
                    msg['content'],
                    generation_config=generation_config if generation_config else None
                )

        return response.text


def get_llm(
    provider: Optional[LLMProvider] = None,
    **kwargs
) -> BaseLLM:
    """
    Get LLM instance based on provider

    Args:
        provider: LLM provider to use ("gemini", "ollama", "openai")
                 If None, uses environment variable LLM_PROVIDER or defaults to "gemini"
        **kwargs: Provider-specific arguments
            For Ollama:
                - model: Model name (default: "qwen2.5:latest")
                - base_url: Ollama server URL (default: "http://localhost:11434")
            For Gemini:
                - api_key: Gemini API key (default: from GEMINI_API_KEY env var)
                - model: Model name (default: "gemini-2.0-flash-exp")

    Returns:
        BaseLLM: LLM instance

    Examples:
        # Use Gemini (default)
        llm = get_llm()

        # Use Gemini explicitly
        llm = get_llm(provider="gemini", api_key="your-key")

        # Use Ollama with custom model
        llm = get_llm(provider="ollama", model="mistral:latest")
    """
    # Determine provider from argument or environment
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "ollama":
        model = kwargs.get("model", os.getenv("OLLAMA_MODEL", "qwen2.5:latest"))
        base_url = kwargs.get("base_url", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        return OllamaLLM(model=model, base_url=base_url)

    elif provider == "gemini":
        api_key = kwargs.get("api_key", os.getenv("GEMINI_API_KEY"))
        if not api_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY or pass api_key parameter.")
        model = kwargs.get("model", os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"))
        return GeminiLLM(api_key=api_key, model=model)

    elif provider == "openai":
        raise NotImplementedError("OpenAI provider not yet implemented")

    else:
        raise ValueError(f"Unknown provider: {provider}. Choose from: gemini, ollama")


def get_default_llm() -> BaseLLM:
    """
    Get default LLM based on environment configuration

    Priority:
    1. If LLM_PROVIDER is set, use that
    2. Otherwise, use Gemini if API key is available
    3. Fall back to Ollama if running

    Returns:
        BaseLLM: Default LLM instance
    """
    provider = os.getenv("LLM_PROVIDER")

    if provider:
        return get_llm(provider=provider)

    # Try Gemini first (preferred provider)
    if os.getenv("GEMINI_API_KEY"):
        return get_llm(provider="gemini")

    # Fall back to Ollama if available
    try:
        return get_llm(provider="ollama")
    except ConnectionError:
        pass

    raise RuntimeError(
        "No LLM provider available. Either:\n"
        "1. Set GEMINI_API_KEY environment variable (recommended)\n"
        "2. Start Ollama: 'ollama serve' (fallback)\n"
        "3. Set LLM_PROVIDER environment variable"
    )


# Example usage
if __name__ == "__main__":
    import sys

    print("Testing LLM Factory...\n")

    # Test Ollama
    try:
        print("=" * 60)
        print("Testing Ollama (Local Qwen 2.5)")
        print("=" * 60)
        llm = get_llm(provider="ollama")
        print(f"✅ Connected to: {llm.provider_name}\n")

        response = llm.generate("What is 2+2? Answer in one sentence.")
        print(f"Response: {response}\n")

    except Exception as e:
        print(f"❌ Ollama test failed: {e}\n")

    # Test Gemini (if API key available)
    if os.getenv("GEMINI_API_KEY"):
        try:
            print("=" * 60)
            print("Testing Gemini (Cloud)")
            print("=" * 60)
            llm = get_llm(provider="gemini")
            print(f"✅ Connected to: {llm.provider_name}\n")

            response = llm.generate("What is 3+3? Answer in one sentence.")
            print(f"Response: {response}\n")

        except Exception as e:
            print(f"❌ Gemini test failed: {e}\n")
    else:
        print("⚠️  Skipping Gemini test (no API key)")

    # Test default
    try:
        print("=" * 60)
        print("Testing Default LLM")
        print("=" * 60)
        llm = get_default_llm()
        print(f"✅ Using: {llm.provider_name}\n")

    except Exception as e:
        print(f"❌ Default LLM test failed: {e}\n")
