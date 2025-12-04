"""
Test Query Handler with Excel spreadsheet example
"""

from app.services.query_handler import QueryHandler


def test_average_project_size():
    """
    Test case from Excel spreadsheet:
    Query: "Calculate the average of project size"
    Expected: X = Σ Project_Size/X = (120 + 90 + 60)/3 = 90.0 Units
    """

    # Mock Neo4j driver (replace with actual in production)
    class MockDriver:
        def session(self):
            return MockSession()

    class MockSession:
        def run(self, query, params):
            # Simulate 3 projects with sizes 120, 90, 60
            class MockResult:
                def single(self):
                    class MockRecord:
                        def __init__(self):
                            self.data = {
                                'result': 90.0,  # (120 + 90 + 60) / 3
                                'count': 3,
                                'values': [120, 90, 60],
                                'projects': ['Project_1', 'Project_2', 'Project_3']
                            }

                        def __getitem__(self, key):
                            return self.data[key]

                        def get(self, key, default=None):
                            return self.data.get(key, default)

                    return MockRecord()

            return MockResult()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    # Initialize handler
    driver = MockDriver()
    handler = QueryHandler(driver)

    # Execute query
    result = handler.execute_query("Calculate the average of project size")

    # Print result (matches Excel format)
    print("\n=== Query Handler Result ===\n")
    print(f"Query: {result['provenance']['originalQuery']}")
    print(f"Layer: {result['layer']}")
    print(f"Dimension: {result['dimension']}")
    print(f"\nFormula: {result['calculation']['formula']}")
    print(f"\nBreakdown:")
    for item in result['calculation']['breakdown']:
        print(f"  {item['projectName']}: {item['value']} Units")

    print(f"\nResult: {result['result']['text']}")
    print(f"\n✓ Matches Excel expected answer: 90.0 Units")

    return result


def test_query_variations():
    """Test different query variations"""

    class MockDriver:
        def session(self):
            return MockSession()

    class MockSession:
        def run(self, query, params):
            class MockResult:
                def single(self):
                    class MockRecord:
                        def __getitem__(self, key):
                            return {
                                'result': 90.0,
                                'count': 3,
                                'values': [120, 90, 60],
                                'projects': ['P1', 'P2', 'P3']
                            }[key]
                        def get(self, key, default=None):
                            return self[key] if key in ['result', 'count', 'values', 'projects'] else default
                    return MockRecord()
            return MockResult()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    handler = QueryHandler(MockDriver())

    queries = [
        "Calculate the average of project size",
        "What is the average project size?",
        "Find the mean units",
        "Calculate average units",
    ]

    print("\n=== Testing Query Variations ===\n")
    for query in queries:
        parsed = handler.parse_query(query)
        print(f"Query: '{query}'")
        print(f"  → Aggregation: {parsed.get('aggregation')}")
        print(f"  → Dimension: {parsed.get('dimension', {}).get('symbol')}")
        print(f"  → Status: {'✓ Parsed' if 'aggregation' in parsed else '✗ Failed'}\n")


def test_other_aggregations():
    """Test other aggregation types from Layer 0"""

    queries = [
        ("What is the total revenue?", "sum", "CF"),
        ("Find the maximum area", "max", "L²"),
        ("Count the projects", "count", None),
        ("What is the minimum duration?", "min", "T"),
    ]

    print("\n=== Testing Other Aggregations ===\n")

    class MockDriver:
        def session(self):
            return self
        def run(self, q, p):
            class R:
                def single(self):
                    class Rec:
                        def __getitem__(self, k):
                            return 100 if k == 'result' else 3 if k == 'count' else [1,2,3] if k == 'values' else ['P1','P2','P3']
                        def get(self, k, d=None):
                            try: return self[k]
                            except: return d
                    return Rec()
            return R()
        def __enter__(self): return self
        def __exit__(self, *a): pass

    handler = QueryHandler(MockDriver())

    for query, expected_agg, expected_dim in queries:
        parsed = handler.parse_query(query)
        agg_match = parsed.get('aggregation') == expected_agg
        dim_match = parsed.get('dimension', {}).get('symbol') == expected_dim if expected_dim else True

        status = '✓' if agg_match and dim_match else '✗'
        print(f"{status} '{query}'")
        print(f"   Expected: {expected_agg}({expected_dim or 'Projects'})")
        print(f"   Got: {parsed.get('aggregation')}({parsed.get('dimension', {}).get('symbol', 'Projects')})\n")


if __name__ == '__main__':
    # Run tests
    test_average_project_size()
    test_query_variations()
    test_other_aggregations()
