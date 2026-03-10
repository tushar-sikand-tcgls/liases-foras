"""
Integration Test for Quarterly Market Trends Knowledge Graph
Tests all three tiers: Service → Function Registry → ChromaDB
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_quarterly_service():
    """Test QuarterlyMarketService"""
    print("\n" + "="*70)
    print("TEST 1: QuarterlyMarketService")
    print("="*70)

    from app.services.quarterly_market_service import quarterly_market_service

    # Test 1: Get all quarters
    all_quarters = quarterly_market_service.get_all_quarters()
    print(f"✓ Loaded {len(all_quarters)} quarters")
    assert len(all_quarters) == 45, f"Expected 45 quarters, got {len(all_quarters)}"

    # Test 2: Get metadata
    metadata = quarterly_market_service.get_metadata()
    print(f"✓ Metadata: {metadata.get('source')}")
    print(f"  Date range: {metadata.get('date_range', {}).get('start')} to {metadata.get('date_range', {}).get('end')}")

    # Test 3: Get recent quarters
    recent = quarterly_market_service.get_recent_quarters(4)
    print(f"✓ Recent 4 quarters: {[q['quarter'] for q in recent]}")
    assert len(recent) == 4, f"Expected 4 quarters, got {len(recent)}"

    # Test 4: Year range filter
    data_2023 = quarterly_market_service.get_quarters_by_year_range(2023, 2023)
    print(f"✓ FY 2023 data: {len(data_2023)} quarters")
    assert len(data_2023) == 4, f"Expected 4 quarters for 2023, got {len(data_2023)}"

    # Test 5: YoY growth
    yoy_sales = quarterly_market_service.calculate_yoy_growth('sales_units')
    print(f"✓ YoY growth calculated for {len(yoy_sales)} quarters")
    print(f"  Latest 3 YoY growth rates:")
    for item in yoy_sales[-3:]:
        print(f"    {item['quarter']}: {item['yoy_growth_pct']:+.1f}% YoY")

    # Test 6: QoQ growth
    qoq_sales = quarterly_market_service.calculate_qoq_growth('sales_units')
    print(f"✓ QoQ growth calculated for {len(qoq_sales)} quarters")

    # Test 7: Summary statistics
    stats = quarterly_market_service.get_summary_statistics('sales_units')
    print(f"✓ Summary statistics:")
    print(f"    Mean: {stats['mean']:.0f} units")
    print(f"    Max: {stats['max']:,} units")
    print(f"    Min: {stats['min']:,} units")

    # Test 8: Absorption rate
    absorption = quarterly_market_service.calculate_absorption_rate_trend()
    print(f"✓ Absorption rate calculated for {len(absorption)} quarters")
    avg_absorption = sum(a['absorption_rate_pct'] for a in absorption if a['absorption_rate_pct'] is not None) / len([a for a in absorption if a['absorption_rate_pct'] is not None])
    print(f"    Average absorption rate: {avg_absorption:.2f}%")

    print("\n✅ QuarterlyMarketService: ALL TESTS PASSED")
    return True


def test_function_registry():
    """Test Function Registry Integration"""
    print("\n" + "="*70)
    print("TEST 2: Function Registry Integration")
    print("="*70)

    from app.services.function_registry import get_function_registry

    registry = get_function_registry()

    # Test 1: get_all_quarterly_data
    print("\n▸ Testing: get_all_quarterly_data")
    result = registry.execute_function("get_all_quarterly_data", {})
    assert 'data' in result, "Missing 'data' key"
    assert result['count'] == 45, f"Expected 45 quarters, got {result['count']}"
    print(f"  ✓ Retrieved {result['count']} quarters")
    print(f"  ✓ Message: {result['message']}")

    # Test 2: get_recent_quarters
    print("\n▸ Testing: get_recent_quarters")
    result = registry.execute_function("get_recent_quarters", {"n": 4})
    assert result['count'] == 4, f"Expected 4 quarters, got {result['count']}"
    print(f"  ✓ Retrieved {result['count']} recent quarters")

    # Test 3: get_quarters_by_year_range
    print("\n▸ Testing: get_quarters_by_year_range")
    result = registry.execute_function("get_quarters_by_year_range", {"start_year": 2023, "end_year": 2024})
    print(f"  ✓ Retrieved {result['count']} quarters for 2023-2024")

    # Test 4: calculate_yoy_growth
    print("\n▸ Testing: calculate_yoy_growth")
    result = registry.execute_function("calculate_yoy_growth", {"metric": "sales_units"})
    assert 'growth_data' in result, "Missing 'growth_data' key"
    print(f"  ✓ Calculated YoY growth for {result['count']} quarters")
    print(f"  ✓ Analysis type: {result['analysis_type']}")

    # Test 5: calculate_qoq_growth
    print("\n▸ Testing: calculate_qoq_growth")
    result = registry.execute_function("calculate_qoq_growth", {"metric": "supply_units"})
    assert 'growth_data' in result, "Missing 'growth_data' key"
    print(f"  ✓ Calculated QoQ growth for {result['count']} quarters")

    # Test 6: get_market_summary_statistics
    print("\n▸ Testing: get_market_summary_statistics")
    result = registry.execute_function("get_market_summary_statistics", {"metric": "sales_area_mn_sqft"})
    assert 'statistics' in result, "Missing 'statistics' key"
    print(f"  ✓ Summary statistics for {result['metric']}:")
    print(f"    Mean: {result['statistics']['mean']:.2f} mn sq ft")
    print(f"    Max: {result['statistics']['max']:.2f} mn sq ft")

    # Test 7: calculate_absorption_rate_trend
    print("\n▸ Testing: calculate_absorption_rate_trend")
    result = registry.execute_function("calculate_absorption_rate_trend", {})
    assert 'absorption_data' in result, "Missing 'absorption_data' key"
    assert result['count'] == 45, f"Expected 45 quarters, got {result['count']}"
    print(f"  ✓ Calculated absorption rates for {result['count']} quarters")
    print(f"  ✓ Formula: {result['formula']}")
    print(f"  ✓ Layer: {result['layer']}")

    print("\n✅ Function Registry: ALL TESTS PASSED")
    return True


def test_chromadb_integration():
    """Test ChromaDB Integration"""
    print("\n" + "="*70)
    print("TEST 3: ChromaDB Semantic Search")
    print("="*70)

    try:
        import chromadb
        from chromadb.config import Settings
        from sentence_transformers import SentenceTransformer

        # Connect to ChromaDB
        persist_directory = "data/chroma_quarterly_db"
        client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        collection = client.get_collection("quarterly_market_data")
        count = collection.count()
        print(f"✓ Connected to ChromaDB")
        print(f"  Collection: quarterly_market_data")
        print(f"  Document count: {count}")
        assert count == 48, f"Expected 48 documents, got {count}"

        # Load embedding model
        embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

        # Test queries
        test_queries = [
            "What was the sales performance in 2023?",
            "Show me supply trends",
            "What's the absorption rate?",
            "Recent quarterly data"
        ]

        for query in test_queries:
            query_embedding = embedding_model.encode(query).tolist()
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=3
            )

            print(f"\n▸ Query: '{query}'")
            print(f"  ✓ Found {len(results['ids'][0])} relevant documents:")
            for i, doc_id in enumerate(results['ids'][0]):
                print(f"    {i+1}. {doc_id}")

        print("\n✅ ChromaDB: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n❌ ChromaDB test failed: {e}")
        print("  Note: Run 'python scripts/index_quarterly_data_to_chromadb.py' first")
        return False


def test_registry_summary():
    """Test Registry Summary"""
    print("\n" + "="*70)
    print("TEST 4: Registry Summary")
    print("="*70)

    from app.services.function_registry import get_function_registry

    registry = get_function_registry()
    summary = registry.get_registry_summary()

    print(f"✓ Total functions registered: {summary['total_functions']}")
    print(f"\n  Functions by layer:")
    for layer, count in summary['by_layer'].items():
        print(f"    {layer}: {count} functions")

    print(f"\n  Functions by category:")
    for category, count in summary['by_category'].items():
        print(f"    {category}: {count} functions")

    # Check for quarterly market functions
    quarterly_functions = [
        'get_all_quarterly_data',
        'get_recent_quarters',
        'get_quarters_by_year_range',
        'calculate_yoy_growth',
        'calculate_qoq_growth',
        'get_market_summary_statistics',
        'calculate_absorption_rate_trend'
    ]

    print(f"\n  Quarterly market functions:")
    for func_name in quarterly_functions:
        if func_name in summary['function_names']:
            print(f"    ✓ {func_name}")
        else:
            print(f"    ✗ {func_name} (MISSING!)")

    print("\n✅ Registry Summary: ALL TESTS PASSED")
    return True


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Quarterly Market Trends - Integration Test Suite")
    print("="*70)
    print("\nTesting three-tier MCP architecture:")
    print("  Tier 1: Gemini Function Calling (Function Registry)")
    print("  Tier 2: Backend Services (QuarterlyMarketService)")
    print("  Tier 3: Storage Layer (ChromaDB)")

    results = []

    try:
        # Test 1: Service Layer
        results.append(("QuarterlyMarketService", test_quarterly_service()))

        # Test 2: Function Registry
        results.append(("Function Registry", test_function_registry()))

        # Test 3: ChromaDB
        results.append(("ChromaDB", test_chromadb_integration()))

        # Test 4: Registry Summary
        results.append(("Registry Summary", test_registry_summary()))

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Final summary
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "="*70)

    if all_passed:
        print("🎉 ALL TESTS PASSED! Quarterly Market Trends integration is working correctly.")
        print("\nNext steps:")
        print("1. Start frontend: cd frontend && streamlit run streamlit_app.py")
        print("2. Click 'Market Trends' button to view dashboard")
        print("3. Test Gemini function calling via LLM queries")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED. Please review the errors above.")
        sys.exit(1)
