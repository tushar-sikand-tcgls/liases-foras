"""
Test ATLAS Analytical Output Requirements

Validates that ATLAS provides:
1. ANALYSIS (What the data shows)
2. INSIGHTS (Why things are the way they are)
3. RECOMMENDATIONS (What to do about it)

NOT just raw data or calculations!
"""

import os
import json
import re
os.environ['GOOGLE_API_KEY'] = 'AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM'

from app.services.sirrus_langchain_service import get_sirrus_service

def analyze_response_quality(response_text):
    """
    Check if response contains analytical elements (not just data dump)

    Returns:
        dict with scores for analysis, insights, recommendations
    """
    if not response_text:
        return {"analysis": 0, "insights": 0, "recommendations": 0}

    response_lower = response_text.lower()

    scores = {
        "analysis": 0,
        "insights": 0,
        "recommendations": 0,
        "data_dump": 0
    }

    # Analysis indicators (comparing, synthesizing, patterns)
    analysis_signals = [
        "average", "compared to", "vs", "versus", "indicates", "shows",
        "variance", "range", "below", "above", "trend", "pattern",
        "positioned", "fragmented", "premium", "value market"
    ]
    for signal in analysis_signals:
        if signal in response_lower:
            scores["analysis"] += 1

    # Insight indicators (explaining why, root causes, factors)
    insight_signals = [
        "driven by", "due to", "because", "caused by", "factors",
        "influenced by", "resulting from", "attributed to", "stems from",
        "impact", "proximity", "access", "infrastructure", "demographics"
    ]
    for signal in insight_signals:
        if signal in response_lower:
            scores["insights"] += 1

    # Recommendation indicators (should, target, strategy, timing)
    recommendation_signals = [
        "recommend", "should", "target", "strategy", "timing",
        "for developers", "for investors", "best", "optimal",
        "consider", "focus on", "entry opportunity", "launch",
        "risk mitigation", "diversify"
    ]
    for signal in recommendation_signals:
        if signal in response_lower:
            scores["recommendations"] += 1

    # Data dump indicators (BAD - just listing data)
    data_dump_signals = [
        "there are", "projects in", "the projects are", "list of",
        "following projects", "here are the"
    ]
    for signal in data_dump_signals:
        if signal in response_lower:
            scores["data_dump"] += 1

    return scores

def test_atlas_analytical():
    """Test ATLAS analytical requirements"""

    print("=" * 80)
    print("TESTING ATLAS ANALYTICAL OUTPUT")
    print("=" * 80)
    print("\nATLAS = Analytical Tool built around real estate strategy")
    print("Must provide: ANALYSIS + INSIGHTS + RECOMMENDATIONS")
    print("NOT just: Data dumps or raw calculations")
    print()

    sirrus_service = get_sirrus_service()

    # Test cases that should generate analytical responses
    test_queries = [
        {
            "query": "Tell me about Chakan",
            "region": "Chakan",
            "expected": "Comprehensive analysis with market insights and recommendations"
        },
        {
            "query": "What's the market situation in Hinjewadi?",
            "region": "Hinjewadi",
            "expected": "Analysis + insights on market dynamics"
        },
        {
            "query": "Should I invest in Wakad?",
            "region": "Wakad",
            "expected": "Strategic recommendation with rationale"
        }
    ]

    results = []

    for i, test in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_queries)}")
        print(f"{'='*80}")
        print(f"Query: \"{test['query']}\"")
        print(f"Expected: {test['expected']}")
        print()

        try:
            # Execute query
            result = sirrus_service.process_query(
                query=test['query'],
                region=test['region']
            )

            # Get response text
            response_text = result.get("summary", "")

            # Analyze quality
            quality_scores = analyze_response_quality(response_text)

            print(f"Quality Analysis:")
            print(f"  Analysis signals: {quality_scores['analysis']}")
            print(f"  Insight signals: {quality_scores['insights']}")
            print(f"  Recommendation signals: {quality_scores['recommendations']}")
            print(f"  Data dump signals: {quality_scores['data_dump']} (lower is better)")
            print()

            # Determine if response meets ATLAS requirements
            is_analytical = (
                quality_scores['analysis'] >= 3 and
                quality_scores['insights'] >= 2 and
                quality_scores['recommendations'] >= 2
            )

            is_data_dump = quality_scores['data_dump'] > quality_scores['analysis']

            if is_analytical and not is_data_dump:
                verdict = "✅ PASS - Analytical response"
                print(f"Verdict: {verdict}")
            elif is_data_dump:
                verdict = "❌ FAIL - Data dump detected"
                print(f"Verdict: {verdict}")
                print(f"⚠️  Response is just listing data without analysis!")
            else:
                verdict = "⚠️  PARTIAL - Lacks some analytical elements"
                print(f"Verdict: {verdict}")
                if quality_scores['analysis'] < 3:
                    print(f"   Missing: More analysis of what data shows")
                if quality_scores['insights'] < 2:
                    print(f"   Missing: Insights into why/how factors")
                if quality_scores['recommendations'] < 2:
                    print(f"   Missing: Strategic recommendations")

            # Show excerpt of response
            print(f"\nResponse Excerpt:")
            if len(response_text) > 500:
                print(response_text[:500] + "...")
            else:
                print(response_text if response_text else "[Empty response]")

            results.append({
                "query": test['query'],
                "quality_scores": quality_scores,
                "verdict": verdict,
                "response_length": len(response_text)
            })

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append({
                "query": test['query'],
                "verdict": "ERROR",
                "error": str(e)
            })

    # Final summary
    print("\n" + "=" * 80)
    print("ATLAS ANALYTICAL QUALITY SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results if "✅ PASS" in r.get("verdict", ""))
    partial = sum(1 for r in results if "⚠️  PARTIAL" in r.get("verdict", ""))
    failed = sum(1 for r in results if "❌ FAIL" in r.get("verdict", ""))

    print(f"\nResults:")
    print(f"  ✅ Fully Analytical: {passed}/{len(test_queries)}")
    print(f"  ⚠️  Partially Analytical: {partial}/{len(test_queries)}")
    print(f"  ❌ Data Dump / Failed: {failed}/{len(test_queries)}")

    print(f"\nAverage Quality Scores:")
    avg_analysis = sum(r.get("quality_scores", {}).get("analysis", 0) for r in results) / len(results)
    avg_insights = sum(r.get("quality_scores", {}).get("insights", 0) for r in results) / len(results)
    avg_recommendations = sum(r.get("quality_scores", {}).get("recommendations", 0) for r in results) / len(results)

    print(f"  Analysis signals: {avg_analysis:.1f} (target: ≥3)")
    print(f"  Insight signals: {avg_insights:.1f} (target: ≥2)")
    print(f"  Recommendation signals: {avg_recommendations:.1f} (target: ≥2)")

    print(f"\n{'='*80}")

    # Save results
    with open("atlas_analytical_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Detailed results saved to: atlas_analytical_test_results.json")

    return results

if __name__ == "__main__":
    test_atlas_analytical()
