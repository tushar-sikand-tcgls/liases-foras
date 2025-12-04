"""
Test Dynamic Prompt Routing

Demonstrates how natural language prompts are dynamically routed
to the correct calculators without hardcoded logic.
"""

import pytest
from app.services.prompt_router import prompt_router, LayerType, RouteDecision


class TestPromptRouting:
    """Test suite for dynamic prompt routing"""

    def test_irr_routing(self):
        """Test IRR calculation routing"""
        prompts = [
            "Calculate IRR for my investment",
            "What's the internal rate of return?",
            "Find the IRR with these cash flows",
            "Calculate internal rate of return for the project"
        ]

        for prompt in prompts:
            decision = prompt_router.analyze_prompt(prompt)
            assert decision.capability == "calculate_irr"
            assert decision.layer == LayerType.LAYER_2
            assert decision.confidence > 0.5

    def test_statistical_routing(self):
        """Test statistical analysis routing"""
        prompts = [
            "What's the average price across all projects?",
            "Calculate standard deviation of sales",
            "Show me the median value",
            "Find outliers in the data",
            "What's the total sum of all investments?"
        ]

        for prompt in prompts:
            decision = prompt_router.analyze_prompt(prompt)
            assert decision.capability == "calculate_statistics"
            assert decision.layer == LayerType.LAYER_2

    def test_optimization_routing(self):
        """Test optimization routing"""
        prompts = [
            "Optimize the product mix for maximum IRR",
            "What's the best unit combination?",
            "Find the optimal mix of 1BHK, 2BHK and 3BHK",
            "Maximize returns through unit optimization"
        ]

        for prompt in prompts:
            decision = prompt_router.analyze_prompt(prompt)
            assert decision.capability == "optimize_product_mix"
            assert decision.layer == LayerType.LAYER_3

    def test_vector_search_routing(self):
        """Test vector search routing"""
        prompts = [
            "Tell me about the Pune market",
            "What's the infrastructure like in Chakan?",
            "Show me economic trends for Mumbai",
            "Explain the demographics of this region",
            "Give me market insights for Bangalore"
        ]

        for prompt in prompts:
            decision = prompt_router.analyze_prompt(prompt)
            assert decision.layer == LayerType.LAYER_4
            assert decision.requires_vector_search is True

    def test_top_n_routing(self):
        """Test top N projects routing"""
        prompts = [
            "Show me the top 5 projects by absorption rate",
            "What are the best 10 performing projects?",
            "List the highest revenue projects",
            "Find the bottom 3 projects by sales"
        ]

        for prompt in prompts:
            decision = prompt_router.analyze_prompt(prompt)
            assert decision.capability == "get_top_n_projects"
            assert decision.layer == LayerType.LAYER_2

    def test_aggregation_routing(self):
        """Test regional aggregation routing"""
        prompts = [
            "Aggregate all projects in Chakan",
            "What's the total for the micromarket?",
            "Sum up all projects in this region"
        ]

        for prompt in prompts:
            decision = prompt_router.analyze_prompt(prompt)
            assert decision.capability == "aggregate_by_region"
            assert decision.layer == LayerType.LAYER_2

    def test_psf_asp_routing(self):
        """Test PSF and ASP routing"""
        psf_prompts = [
            "Calculate price per square foot",
            "What's the PSF?",
            "Price per sqft for this project"
        ]

        for prompt in psf_prompts:
            decision = prompt_router.analyze_prompt(prompt)
            assert decision.capability == "calculate_psf"
            assert decision.layer == LayerType.LAYER_1

        asp_prompts = [
            "Calculate average selling price",
            "What's the ASP per unit?",
            "Average price per unit"
        ]

        for prompt in asp_prompts:
            decision = prompt_router.analyze_prompt(prompt)
            assert decision.capability == "calculate_asp"
            assert decision.layer == LayerType.LAYER_1

    def test_unknown_query_defaults_to_vector(self):
        """Test that unknown queries default to vector search"""
        prompts = [
            "Random question about something",
            "Tell me a story",
            "What do you think about this?"
        ]

        for prompt in prompts:
            decision = prompt_router.analyze_prompt(prompt)
            assert decision.layer == LayerType.LAYER_4
            assert decision.requires_vector_search is True
            assert decision.confidence <= 0.5

    def test_parameter_extraction(self):
        """Test parameter extraction from prompts"""
        # Test with numbers
        decision = prompt_router.analyze_prompt("Calculate IRR with cash flows 100, 200, 300")
        assert decision.capability == "calculate_irr"

        # Test with location
        decision = prompt_router.analyze_prompt("Show top 5 projects in Pune")
        assert decision.capability == "get_top_n_projects"
        assert "Pune" in prompt_router._extract_parameters(
            "show top 5 projects in pune",
            "get_top_n_projects"
        ) or "city" in prompt_router._extract_parameters(
            "show top 5 projects in pune",
            "get_top_n_projects"
        )

    def test_confidence_scoring(self):
        """Test confidence scoring for routing decisions"""
        # High confidence - exact match
        decision = prompt_router.analyze_prompt("Calculate IRR")
        assert decision.confidence > 0.7

        # Medium confidence - partial match
        decision = prompt_router.analyze_prompt("What about the return rate?")
        assert 0.3 < decision.confidence <= 0.7

        # Low confidence - vague query
        decision = prompt_router.analyze_prompt("Show me something interesting")
        assert decision.confidence <= 0.5


def test_integration_examples():
    """Test real-world integration examples"""

    test_cases = [
        {
            "prompt": "Calculate the average PSF for all projects in Chakan",
            "expected_capability": "calculate_statistics",
            "expected_layer": LayerType.LAYER_2
        },
        {
            "prompt": "What's the IRR if I invest 500Cr with returns of 100Cr per year?",
            "expected_capability": "calculate_irr",
            "expected_layer": LayerType.LAYER_2
        },
        {
            "prompt": "Show me market insights for Pune including infrastructure",
            "expected_capability": "get_market_insights",
            "expected_layer": LayerType.LAYER_4,
            "requires_vector": True
        },
        {
            "prompt": "Optimize unit mix for a 100-unit project to maximize returns",
            "expected_capability": "optimize_product_mix",
            "expected_layer": LayerType.LAYER_3
        },
        {
            "prompt": "Find outliers in the price distribution",
            "expected_capability": "calculate_statistics",
            "expected_layer": LayerType.LAYER_2
        }
    ]

    for test in test_cases:
        decision = prompt_router.analyze_prompt(test["prompt"])

        print(f"\nPrompt: {test['prompt']}")
        print(f"Routed to: {decision.capability} (Layer {decision.layer.value})")
        print(f"Confidence: {decision.confidence:.2f}")
        print(f"Reason: {decision.reason}")

        assert decision.capability == test["expected_capability"]
        assert decision.layer == test["expected_layer"]

        if "requires_vector" in test:
            assert decision.requires_vector_search == test["requires_vector"]


if __name__ == "__main__":
    # Run integration examples
    print("="*80)
    print("DYNAMIC PROMPT ROUTING TEST")
    print("="*80)

    test_integration_examples()

    print("\n" + "="*80)
    print("✅ All routing tests passed!")
    print("="*80)

    # Show capability listing
    print("\n📊 Available Capabilities by Layer:")
    capabilities = prompt_router.list_all_capabilities()

    for layer, caps in sorted(capabilities.items()):
        print(f"\nLayer {layer}:")
        for cap in caps:
            print(f"  • {cap['capability']}: {cap['description']}")
            if cap.get('requires_vector'):
                print(f"    (Requires vector search)")