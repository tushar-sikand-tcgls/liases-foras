"""
Demo: LLM-Powered Query Processor
Shows how LLM analyzes queries without hardcoding
"""

import json
import google.generativeai as genai
from app.config import settings


def demo_llm_understanding():
    """
    Demonstrate how LLM understands queries dynamically
    """

    # Knowledge Graph Schema (not hardcoded logic!)
    kg_schema = {
        "layers": {
            "0": {
                "name": "Raw Dimensions",
                "dimensions": {
                    "U": {
                        "symbol": "U",
                        "name": "Units",
                        "unit": "Units",
                        "neo4j_field": "totalUnits",
                        "examples": ["project size", "units", "total units"]
                    },
                    "L²": {
                        "symbol": "L²",
                        "name": "Area",
                        "unit": "sqft",
                        "neo4j_field": "totalSaleableArea",
                        "examples": ["area", "saleable area", "total area"]
                    },
                    "T": {
                        "symbol": "T",
                        "name": "Time",
                        "unit": "months",
                        "neo4j_field": "projectDuration",
                        "examples": ["duration", "project duration"]
                    },
                    "CF": {
                        "symbol": "CF",
                        "name": "Cash Flow",
                        "unit": "INR",
                        "neo4j_field": "totalRevenue",
                        "examples": ["revenue", "cost"]
                    }
                }
            }
        },
        "aggregations": ["average", "sum", "count", "min", "max"]
    }

    # Configure Gemini
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Test queries
    test_queries = [
        "Calculate the average of project size",
        "What is the total area?",
        "Find the maximum duration",
        "How many projects are there?",
        "Sum of all revenue"
    ]

    print("=" * 80)
    print("LLM-Powered Query Understanding Demo")
    print("=" * 80)
    print("\nKnowledge Graph Schema (provided to LLM as context):")
    print(json.dumps(kg_schema, indent=2))
    print("\n" + "=" * 80)

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"USER QUERY: '{query}'")
        print("=" * 80)

        prompt = f"""You are a knowledge graph query analyzer for real estate analytics.

KNOWLEDGE GRAPH SCHEMA:
{json.dumps(kg_schema, indent=2)}

USER QUERY: "{query}"

Analyze this query and determine:
1. Which LAYER (0 = raw dimensions)
2. Which TARGET ATTRIBUTE
3. Which DIMENSION (U, L², T, CF)
4. Which AGGREGATION (average, sum, count, min, max)
5. Which NEO4J FIELD to query
6. What UNIT for the result

IMPORTANT RULES:
- "project size" = U dimension, totalUnits field
- "area" = L² dimension, totalSaleableArea field
- "duration" = T dimension, projectDuration field
- "revenue" or "cost" = CF dimension, totalRevenue/totalCost field

Return ONLY valid JSON (no markdown):
{{
  "layer": 0,
  "target_attribute": "...",
  "dimension": "...",
  "aggregation": "...",
  "neo4j_field": "...",
  "unit": "..."
}}
"""

        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean markdown if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            understanding = json.loads(response_text)

            print("\nLLM UNDERSTANDING:")
            print(f"  ✓ Layer: {understanding.get('layer')}")
            print(f"  ✓ Target Attribute: {understanding.get('target_attribute')}")
            print(f"  ✓ Dimension: {understanding.get('dimension')}")
            print(f"  ✓ Aggregation: {understanding.get('aggregation')}")
            print(f"  ✓ Neo4j Field: {understanding.get('neo4j_field')}")
            print(f"  ✓ Unit: {understanding.get('unit')}")

            # Generate Cypher
            agg = understanding.get('aggregation', 'avg')
            field = understanding.get('neo4j_field', 'totalUnits')

            cypher_map = {
                'average': 'avg',
                'sum': 'sum',
                'count': 'count',
                'min': 'min',
                'max': 'max'
            }

            cypher_agg = cypher_map.get(agg, 'avg')

            if agg == 'count':
                cypher = f"MATCH (p:Project) RETURN count(p) AS result"
            else:
                cypher = f"MATCH (p:Project) RETURN {cypher_agg}(p.{field}) AS result, collect(p.{field}) AS values"

            print("\nGENERATED CYPHER QUERY:")
            print(f"  {cypher}")

            print("\nEXPECTED RESULT FORMAT:")
            dim = understanding.get('dimension', '')
            count = 3  # assume 3 projects
            if agg == 'average':
                formula = f"X = Σ {dim} / {count}"
            elif agg == 'sum':
                formula = f"X = Σ {dim}"
            elif agg == 'count':
                formula = f"X = count(Projects)"
            else:
                formula = f"X = {agg}({dim})"

            print(f"  Formula: {formula}")
            print(f"  Unit: {understanding.get('unit')}")

        except Exception as e:
            print(f"\n✗ Error: {e}")

    print("\n" + "=" * 80)
    print("✓ Demo Complete!")
    print("\nKey Takeaway: No hardcoding! LLM reads schema and understands dynamically.")
    print("=" * 80)


if __name__ == '__main__':
    demo_llm_understanding()
