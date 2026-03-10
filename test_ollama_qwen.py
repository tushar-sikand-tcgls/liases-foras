"""
Test script for Ollama Qwen 2.5 integration
Demonstrates basic usage and validates connection
"""

from app.services.ollama_service import get_ollama_service, OllamaConfig


def test_basic_generation():
    """Test 1: Basic text generation"""
    print("=" * 60)
    print("TEST 1: Basic Generation")
    print("=" * 60)

    service = get_ollama_service()

    prompt = "What is absorption rate in real estate? Give a brief answer."
    print(f"\n📝 Prompt: {prompt}")

    response = service.generate(prompt, temperature=0.7)
    print(f"\n🤖 Qwen 2.5 Response:\n{response}\n")


def test_chat_mode():
    """Test 2: Chat with conversation history"""
    print("=" * 60)
    print("TEST 2: Chat Mode")
    print("=" * 60)

    service = get_ollama_service()

    messages = [
        {"role": "user", "content": "What is PSF in real estate?"},
    ]

    print(f"\n📝 User: {messages[0]['content']}")
    response = service.chat(messages)
    print(f"\n🤖 Qwen 2.5: {response}\n")

    # Continue conversation
    messages.append({"role": "assistant", "content": response})
    messages.append({"role": "user", "content": "Can you give me an example calculation?"})

    print(f"📝 User: {messages[-1]['content']}")
    response2 = service.chat(messages)
    print(f"\n🤖 Qwen 2.5: {response2}\n")


def test_rag_query():
    """Test 3: RAG-style query with context"""
    print("=" * 60)
    print("TEST 3: RAG Query (Context-Based)")
    print("=" * 60)

    service = get_ollama_service()

    context = """
    Project: Pristine Heights
    Total Units: 150
    Sold Units: 45
    Project Duration: 3 years
    Annual Sales: 15 units/year
    Absorption Rate: 10% per year
    Price Per Sqft: ₹4,500
    """

    query = "What is the absorption rate of Pristine Heights and is it performing well?"

    print(f"\n📚 Context:\n{context}")
    print(f"\n📝 Query: {query}")

    response = service.generate_with_context(query, context)
    print(f"\n🤖 Qwen 2.5 Response:\n{response}\n")


def test_real_estate_analysis():
    """Test 4: Real estate financial analysis"""
    print("=" * 60)
    print("TEST 4: Real Estate Financial Analysis")
    print("=" * 60)

    service = get_ollama_service()

    system_prompt = """You are an expert real estate financial analyst.
Provide concise, data-driven insights based on the given metrics."""

    prompt = """Analyze this project:
- Total Investment: ₹50 Cr
- Annual Revenue: ₹12 Cr
- Project Duration: 5 years
- Absorption Rate: 15% per year
- Market Average Absorption: 12% per year

What are the key insights and should the developer be concerned?"""

    print(f"\n📝 Prompt:\n{prompt}")

    response = service.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.5  # Lower temp for factual analysis
    )

    print(f"\n🤖 Qwen 2.5 Analysis:\n{response}\n")


def test_model_info():
    """Test 5: Check available models"""
    print("=" * 60)
    print("TEST 5: Model Information")
    print("=" * 60)

    service = get_ollama_service()

    models = service.get_available_models()
    print(f"\n📦 Available Ollama models:")
    for model in models:
        marker = "✅" if model == service.config.model else "  "
        print(f"  {marker} {model}")

    print(f"\n🔧 Current configuration:")
    print(f"  Model: {service.config.model}")
    print(f"  Base URL: {service.config.base_url}")
    print(f"  Temperature: {service.config.temperature}")
    print(f"  Max Tokens: {service.config.max_tokens}")
    print()


def run_all_tests():
    """Run all tests"""
    try:
        test_model_info()
        test_basic_generation()
        test_chat_mode()
        test_rag_query()
        test_real_estate_analysis()

        print("=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        print("\n💡 Next steps:")
        print("  1. Integrate with your existing LLM services")
        print("  2. Use Ollama for rate-limit-free testing")
        print("  3. Configure via environment variables (optional)")
        print()

    except ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("\n💡 Troubleshooting:")
        print("  1. Check if Ollama is running: ollama serve")
        print("  2. Verify Qwen 2.5 is available: ollama list")
        print("  3. Pull the model if needed: ollama pull qwen2.5")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
