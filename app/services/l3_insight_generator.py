"""
V3.0.0: Layer 3 Insight Generator Service
==========================================

Evaluates L2 metrics against L3 rules and generates insights/recommendations.

Flow:
1. Fetch L3 rules from Neo4j
2. Evaluate L2 metric values against rule thresholds
3. For POSITIVE feedback (GOOD, EXCELLENT) → Use template-based insight
4. For NEGATIVE feedback (POOR, CRITICAL) → Call Gemini API for recommendation
5. Store insights as (:L3_Insight)-[:HAS_RECOMMENDATION]->(:L3_Recommendation) in Neo4j

Gemini API key: AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from neo4j import GraphDatabase

# Gemini API import
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not installed. Run: pip install google-generativeai")


class L3InsightGenerator:
    """Generate L3 insights and recommendations using rules + Gemini API"""

    def __init__(self, uri: str, user: str, password: str, gemini_api_key: str = None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM")

        # Initialize Gemini
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                print("✓ Gemini API initialized successfully")
            except Exception as e:
                self.model = None
                print(f"⚠️  Gemini API initialization failed: {e}")
        else:
            self.model = None

    def close(self):
        self.driver.close()

    def fetch_l3_rule(self, metric_name: str) -> Optional[Dict]:
        """Fetch L3 rule for a specific metric from Neo4j"""
        with self.driver.session() as session:
            query = """
            MATCH (r:L3_Rule {metricName: $metricName})
            RETURN r.ruleId as ruleId,
                   r.metricName as metricName,
                   r.description as description,
                   r.thresholds as thresholds,
                   r.configurable as configurable
            """
            result = session.run(query, metricName=metric_name)
            record = result.single()

            if not record:
                return None

            # Parse thresholds from JSON string
            thresholds_str = record["thresholds"]
            try:
                thresholds = eval(thresholds_str)  # Convert string representation to list
            except:
                thresholds = []

            return {
                "ruleId": record["ruleId"],
                "metricName": record["metricName"],
                "description": record["description"],
                "thresholds": thresholds,
                "configurable": record["configurable"]
            }

    def evaluate_metric_against_rule(self, metric_value: float, rule: Dict) -> Dict:
        """Evaluate metric value against rule thresholds"""
        thresholds = rule["thresholds"]

        for threshold in thresholds:
            min_val = threshold.get("min")
            max_val = threshold.get("max")

            # Check if value falls within threshold range
            if min_val is None and max_val is None:
                continue
            elif min_val is None:
                if metric_value < max_val:
                    return {
                        "assessment": threshold["assessment"],
                        "isNegative": threshold.get("isNegative", False),
                        "template": threshold.get("template", ""),
                        "value": metric_value,
                        "metricName": rule["metricName"]
                    }
            elif max_val is None:
                if metric_value >= min_val:
                    return {
                        "assessment": threshold["assessment"],
                        "isNegative": threshold.get("isNegative", False),
                        "template": threshold.get("template", ""),
                        "value": metric_value,
                        "metricName": rule["metricName"]
                    }
            else:
                if min_val <= metric_value < max_val:
                    return {
                        "assessment": threshold["assessment"],
                        "isNegative": threshold.get("isNegative", False),
                        "template": threshold.get("template", ""),
                        "value": metric_value,
                        "metricName": rule["metricName"]
                    }

        # Default: no threshold matched
        return {
            "assessment": "UNKNOWN",
            "isNegative": False,
            "template": f"Metric value {metric_value} does not match any threshold.",
            "value": metric_value,
            "metricName": rule["metricName"]
        }

    def generate_template_insight(self, evaluation: Dict, l1_data: Dict = None, l2_metrics: List[Dict] = None) -> Dict:
        """Generate template-based insight for positive feedback"""
        template = evaluation.get("template", "")
        value = evaluation["value"]

        # Format template with value
        try:
            narrative = template.format(value=value)
        except:
            narrative = template

        return {
            "insightType": "INSIGHT",
            "narrative": narrative,
            "assessment": evaluation["assessment"],
            "isNegative": evaluation["isNegative"],
            "metricName": evaluation["metricName"],
            "metricValue": value,
            "generatedBy": "Template",
            "timestamp": datetime.now().isoformat()
        }

    def generate_gemini_recommendation(self,
                                        project_name: str,
                                        evaluation: Dict,
                                        l1_data: Dict = None,
                                        l2_metrics: List[Dict] = None) -> Dict:
        """Generate AI-powered recommendation for negative feedback using Gemini"""

        if not self.model:
            return {
                "insightType": "RECOMMENDATION",
                "narrative": f"Gemini API not available. Metric {evaluation['metricName']} is {evaluation['assessment']}.",
                "assessment": evaluation["assessment"],
                "isNegative": evaluation["isNegative"],
                "metricName": evaluation["metricName"],
                "metricValue": evaluation["value"],
                "generatedBy": "Fallback",
                "timestamp": datetime.now().isoformat()
            }

        # Prepare L1 context
        l1_context = ""
        if l1_data:
            l1_context = "\n".join([f"- {k}: {v}" for k, v in l1_data.items()])

        # Prepare L2 context
        l2_context = ""
        if l2_metrics:
            l2_context = "\n".join([
                f"- {m['metric_name']}: {m['value']:.4f} {m['unit']} (dimension: {m['dimension']})"
                for m in l2_metrics
            ])

        # Construct Gemini prompt
        prompt = f"""You are a real estate analytics expert. Analyze this project and provide actionable recommendations.

**Project**: {project_name}

**Problem Detected**:
- Metric: {evaluation['metricName']}
- Current Value: {evaluation['value']:.4f}
- Assessment: {evaluation['assessment']}

**L1 Data (Facts from Liases Foras)**:
{l1_context if l1_context else "No L1 data provided"}

**L2 Metrics (Derived Calculations)**:
{l2_context if l2_context else "No L2 metrics provided"}

**Your Task**:
Generate a detailed recommendation with the following structure:

1. **Assessment** (1-2 sentences): Why is this metric {evaluation['assessment'].lower()}? What does it indicate about project performance?

2. **Root Cause Analysis** (2-3 bullet points): What factors are likely causing this issue?

3. **Recommendations** (3-5 actionable bullet points): What specific actions should be taken to address this issue?

Format your response in clean markdown.
"""

        try:
            response = self.model.generate_content(prompt)
            narrative = response.text
        except Exception as e:
            narrative = f"Gemini API call failed: {e}\n\nFallback: Metric {evaluation['metricName']} is {evaluation['assessment']} at {evaluation['value']:.4f}. Immediate attention required."

        return {
            "insightType": "RECOMMENDATION",
            "narrative": narrative,
            "assessment": evaluation["assessment"],
            "isNegative": evaluation["isNegative"],
            "metricName": evaluation["metricName"],
            "metricValue": evaluation["value"],
            "generatedBy": "Gemini-Pro",
            "timestamp": datetime.now().isoformat()
        }

    def generate_insight(self,
                         project_name: str,
                         metric_name: str,
                         metric_value: float,
                         l1_data: Dict = None,
                         l2_metrics: List[Dict] = None) -> Optional[Dict]:
        """
        Main method: Generate insight for a metric

        Returns:
        - Template insight for positive feedback
        - Gemini recommendation for negative feedback
        """
        # Fetch rule
        rule = self.fetch_l3_rule(metric_name)
        if not rule:
            print(f"⚠️  No rule found for metric: {metric_name}")
            return None

        # Evaluate metric against rule
        evaluation = self.evaluate_metric_against_rule(metric_value, rule)

        # Generate insight based on feedback type
        if evaluation["isNegative"]:
            # Negative feedback → Gemini API
            insight = self.generate_gemini_recommendation(
                project_name, evaluation, l1_data, l2_metrics
            )
        else:
            # Positive feedback → Template
            insight = self.generate_template_insight(
                evaluation, l1_data, l2_metrics
            )

        return insight

    def store_insight_in_neo4j(self, project_name: str, insight: Dict):
        """Store L3 insight in Neo4j linked to project"""
        with self.driver.session() as session:
            # Create L3_Insight node
            session.run("""
                MATCH (p:Project_L1 {projectName: $projectName})
                CREATE (i:L3_Insight {
                    insightType: $insightType,
                    metricName: $metricName,
                    metricValue: $metricValue,
                    assessment: $assessment,
                    isNegative: $isNegative,
                    generatedBy: $generatedBy,
                    timestamp: $timestamp
                })
                CREATE (p)-[:HAS_INSIGHT]->(i)
                CREATE (r:L3_Recommendation {
                    narrative: $narrative,
                    timestamp: $timestamp
                })
                CREATE (i)-[:HAS_RECOMMENDATION]->(r)
            """,
                projectName=project_name,
                insightType=insight["insightType"],
                metricName=insight["metricName"],
                metricValue=insight["metricValue"],
                assessment=insight["assessment"],
                isNegative=insight["isNegative"],
                generatedBy=insight["generatedBy"],
                narrative=insight["narrative"],
                timestamp=insight["timestamp"]
            )

            print(f"✓ Stored {insight['insightType']} for {insight['metricName']} ({insight['assessment']})")

    def generate_insights_for_project(self,
                                       project_name: str,
                                       l2_metrics: List[Dict],
                                       l1_data: Dict = None,
                                       store_in_neo4j: bool = True) -> List[Dict]:
        """
        Generate insights for all L2 metrics of a project

        Args:
            project_name: Project identifier
            l2_metrics: List of L2 metric dictionaries
            l1_data: Optional L1 context data
            store_in_neo4j: Whether to persist insights to Neo4j

        Returns:
            List of generated insights
        """
        insights = []

        print(f"\nGenerating L3 insights for project: {project_name}")
        print("=" * 70)

        for metric in l2_metrics:
            metric_name = metric["metric_name"]
            metric_value = metric["value"]

            insight = self.generate_insight(
                project_name,
                metric_name,
                metric_value,
                l1_data,
                l2_metrics
            )

            if insight:
                insights.append(insight)

                print(f"\n✓ {metric_name}: {insight['assessment']}")
                print(f"  Type: {insight['insightType']}")
                print(f"  Generated by: {insight['generatedBy']}")

                if store_in_neo4j:
                    self.store_insight_in_neo4j(project_name, insight)

        print("=" * 70)
        print(f"✅ Generated {len(insights)} L3 insights")

        return insights


def main():
    """Test L3 insight generator with Sara City project"""
    from app.calculators.layer2_calculator import Layer2Calculator

    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "liasesforas123")
    gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM")

    # Initialize services
    l2_calculator = Layer2Calculator(neo4j_uri, neo4j_user, neo4j_password)
    l3_generator = L3InsightGenerator(neo4j_uri, neo4j_user, neo4j_password, gemini_api_key)

    try:
        print("=" * 70)
        print("V3.0.0: Layer 3 Insight Generator Test")
        print("=" * 70)
        print()

        # Calculate L2 metrics for Sara City
        project_name = "3306"
        print(f"Calculating L2 metrics for project: {project_name}")
        l2_metrics = l2_calculator.calculate_all_l2_metrics(project_name)
        print(f"✓ Calculated {len(l2_metrics)} L2 metrics\n")

        # Generate L3 insights
        insights = l3_generator.generate_insights_for_project(
            project_name,
            l2_metrics,
            store_in_neo4j=True
        )

        # Display insights
        print("\n" + "=" * 70)
        print("Generated Insights:")
        print("=" * 70)

        for insight in insights:
            print(f"\n{'─' * 70}")
            print(f"Metric: {insight['metricName']}")
            print(f"Assessment: {insight['assessment']} ({'Negative' if insight['isNegative'] else 'Positive'})")
            print(f"Type: {insight['insightType']}")
            print(f"Generated by: {insight['generatedBy']}")
            print(f"\nNarrative:")
            print(insight['narrative'])

        print("\n" + "=" * 70)
        print(f"✅ L3 Insight Generation Complete: {len(insights)} insights")
        print("=" * 70)

    finally:
        l2_calculator.close()
        l3_generator.close()


if __name__ == "__main__":
    main()
