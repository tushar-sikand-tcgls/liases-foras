"""
Example: Using Qwen 2.5 (Ollama) for Testing to Avoid Rate Limits

This demonstrates how to replace Gemini calls with Ollama in your tests
to avoid hitting rate limits during development and testing.
"""

from app.services.llm_factory import get_llm, get_default_llm
from app.services.ollama_service import get_ollama_service
import os


def example_1_simple_replacement():
    """
    Example 1: Simple replacement of LLM provider
    """
    print("=" * 70)
    print("EXAMPLE 1: Simple LLM Provider Replacement")
    print("=" * 70)

    # Old way (Gemini - rate limited)
    # llm = get_llm(provider="gemini", api_key="your-key")

    # New way (Ollama - no rate limits)
    llm = get_llm(provider="ollama")

    question = "What is the formula for absorption rate in real estate?"
    print(f"\n📝 Question: {question}")

    response = llm.generate(question, temperature=0.5)
    print(f"\n🤖 Qwen 2.5: {response}\n")


def example_2_batch_testing():
    """
    Example 2: Batch testing without rate limits
    """
    print("=" * 70)
    print("EXAMPLE 2: Batch Testing (No Rate Limits)")
    print("=" * 70)

    llm = get_llm(provider="ollama")

    # Test multiple queries in a loop (would hit rate limit with Gemini)
    test_queries = [
        "What is PSF in real estate?",
        "Explain absorption rate briefly.",
        "What is NPV?",
        "Define IRR in finance.",
        "What is payback period?",
    ]

    print(f"\n🔄 Running {len(test_queries)} queries in sequence...")
    print("(This would hit Gemini rate limits, but Ollama has none!)\n")

    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}/{len(test_queries)}: {query}")
        response = llm.generate(query, temperature=0.3, max_tokens=150)
        print(f"Response: {response[:100]}...")  # First 100 chars

    print("\n✅ All queries completed without rate limits!\n")


def example_3_rag_with_context():
    """
    Example 3: RAG-style testing with project data
    """
    print("=" * 70)
    print("EXAMPLE 3: RAG Testing with Real Estate Data")
    print("=" * 70)

    llm = get_llm(provider="ollama")

    # Simulate retrieved context from your knowledge graph
    project_context = """
    Project Name: Serene Residency
    Location: Chakan, Pune
    Total Units: 200
    Sold Units: 60
    Unsold Units: 140
    Project Duration: 4 years
    Annual Sales: 15 units/year
    Absorption Rate: 7.5% per year
    Price Per Sqft: ₹4,200
    Total Investment: ₹80 Cr
    Annual Revenue: ₹18 Cr
    """

    queries = [
        "What is the absorption rate of Serene Residency?",
        "How many units are left to sell?",
        "Is the project performing well compared to market average of 10%?",
        "What is the revenue per year?",
    ]

    print("\n📚 Project Context:")
    print(project_context)

    for query in queries:
        print(f"\n📝 Query: {query}")

        # Generate response with context (RAG pattern)
        prompt = f"""Based on the following project data:

{project_context}

Question: {query}

Answer concisely based only on the provided data:"""

        response = llm.generate(prompt, temperature=0.3)
        print(f"🤖 Answer: {response}\n")


def example_4_environment_based_switching():
    """
    Example 4: Automatically switch based on environment
    """
    print("=" * 70)
    print("EXAMPLE 4: Environment-Based Provider Switching")
    print("=" * 70)

    # This automatically uses Ollama if available, falls back to Gemini
    llm = get_default_llm()

    print(f"\n🔧 Current LLM: {llm.provider_name}")

    # Check environment variable
    provider = os.getenv("LLM_PROVIDER", "auto")
    print(f"📋 LLM_PROVIDER env var: {provider}")

    query = "Calculate PSF if total revenue is ₹100 Cr and area is 2 lakh sqft"
    print(f"\n📝 Query: {query}")

    response = llm.generate(query, temperature=0.3)
    print(f"\n🤖 Response: {response}\n")


def example_5_direct_ollama_service():
    """
    Example 5: Using OllamaService directly for maximum control
    """
    print("=" * 70)
    print("EXAMPLE 5: Direct Ollama Service Usage")
    print("=" * 70)

    # Get direct access to Ollama service
    ollama = get_ollama_service()

    # Check available models
    print(f"\n📦 Available models: {ollama.get_available_models()}")
    print(f"🎯 Using model: {ollama.config.model}")

    # Chat with conversation history
    messages = [
        {
            "role": "user",
            "content": "If a project has 100 units and sells 15 units per year, what is the absorption rate?"
        }
    ]

    print(f"\n📝 User: {messages[0]['content']}")
    response1 = ollama.chat(messages)
    print(f"\n🤖 Qwen: {response1}")

    # Continue conversation
    messages.append({"role": "assistant", "content": response1})
    messages.append({
        "role": "user",
        "content": "Is that a good absorption rate compared to market average of 12%?"
    })

    print(f"\n📝 User: {messages[-1]['content']}")
    response2 = ollama.chat(messages)
    print(f"\n🤖 Qwen: {response2}\n")


def example_6_stress_test():
    """
    Example 6: Stress test - many rapid queries
    (Would definitely hit rate limits with cloud providers)
    """
    print("=" * 70)
    print("EXAMPLE 6: Stress Test (100 Rapid Queries)")
    print("=" * 70)

    llm = get_llm(provider="ollama")

    print("\n⚠️  Running 100 rapid queries...")
    print("This would hit Gemini's 60 requests/minute limit!\n")

    import time
    start_time = time.time()

    # Run 100 queries as fast as possible
    for i in range(100):
        if i % 10 == 0:
            print(f"Progress: {i}/100 queries...")

        # Simple query
        response = llm.generate(
            f"What is {i} + {i}? Answer with just the number.",
            temperature=0.1,
            max_tokens=10
        )

    elapsed = time.time() - start_time

    print(f"\n✅ Completed 100 queries in {elapsed:.2f} seconds")
    print(f"⚡ Average: {elapsed/100:.3f} seconds per query")
    print("🎉 No rate limits encountered!\n")


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("🚀 QWEN 2.5 (OLLAMA) FOR TESTING - EXAMPLES")
    print("=" * 70)
    print("\nThese examples show how to use local Qwen 2.5 via Ollama")
    print("to avoid rate limits during development and testing.\n")

    try:
        example_1_simple_replacement()
        example_2_batch_testing()
        example_3_rag_with_context()
        example_4_environment_based_switching()
        example_5_direct_ollama_service()

        # Uncomment to run stress test (takes a while)
        # example_6_stress_test()

        print("\n" + "=" * 70)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("\n💡 Key Takeaways:")
        print("  1. Use get_llm(provider='ollama') for rate-limit-free testing")
        print("  2. No API keys needed for local Ollama")
        print("  3. Data stays on your machine (privacy)")
        print("  4. Perfect for development, testing, and experimentation")
        print("  5. Switch to Gemini for production if needed")
        print("\n📚 See OLLAMA_QWEN_INTEGRATION.md for complete guide")
        print()

    except ConnectionError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure Ollama is running:")
        print("  1. Run: ollama serve")
        print("  2. Verify: ollama list")
        print("  3. Pull model if needed: ollama pull qwen2.5\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
