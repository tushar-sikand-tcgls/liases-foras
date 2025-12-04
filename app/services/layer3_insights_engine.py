"""
Layer 3: Non-LLM Insights Engine
=================================

Applies rule-based thresholds to L1 and L2 metrics to generate
Excellent/Okay/Bad insights WITHOUT using LLM.

Architecture:
- L0: Dimensions (U, L², T, C)
- L1: Raw data from PDF
- L2: Calculated financial metrics (NPV, IRR, etc)
- Rules: Thresholds for Excellent/Okay/Bad
- L3: Apply rules → Generate insights (NON-LLM)

AI is only used for recommendations on "Okay" and "Bad" insights at runtime.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from app.services.data_service import data_service


class Layer3InsightsEngine:
    """NON-LLM rule-based insights generator"""

    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict:
        """Load metric evaluation rules from config"""
        rules_file = Path("data/config/metric_rules.json")
        
        if not rules_file.exists():
            print(f"Warning: Rules file not found: {rules_file}")
            return {"L1_metrics": {}, "L2_metrics": {}}
        
        with open(rules_file, 'r') as f:
            return json.load(f)

    def evaluate_metric(self, metric_name: str, value: float, layer: str = "L1") -> Dict:
        """
        Evaluate a single metric against thresholds (NON-LLM)

        Args:
            metric_name: Name of metric (e.g., "npvCr", "irrPct")
            value: Metric value
            layer: "L1" or "L2"

        Returns:
            {
                "metric": "npvCr",
                "value": 50.5,
                "evaluation": "Okay",
                "description": "0 to ₹100 Cr NPV",
                "requires_llm_recommendation": True
            }
        """
        layer_key = f"{layer}_metrics"
        rules = self.rules.get(layer_key, {})
        
        if metric_name not in rules:
            return {
                "metric": metric_name,
                "value": value,
                "evaluation": "Unknown",
                "description": "No rules defined",
                "requires_llm_recommendation": False
            }

        metric_rules = rules[metric_name]
        thresholds = metric_rules.get("thresholds", {})

        # Evaluate against thresholds
        for level in ["Excellent", "Okay", "Bad"]:
            threshold = thresholds.get(level, {})
            min_val = threshold.get("min", float('-inf'))
            max_val = threshold.get("max", float('inf'))

            if min_val <= value < max_val:
                return {
                    "metric": metric_name,
                    "metric_name": metric_rules.get("metric_name", metric_name),
                    "value": value,
                    "unit": metric_rules.get("unit", ""),
                    "dimension": metric_rules.get("dimension", ""),
                    "evaluation": level,
                    "description": threshold.get("description", ""),
                    "threshold_min": min_val,
                    "threshold_max": max_val,
                    "requires_llm_recommendation": level in ["Okay", "Bad"],  # Only Okay/Bad get LLM recommendations
                    "layer": layer
                }

        # Fallback if value doesn't match any threshold
        return {
            "metric": metric_name,
            "value": value,
            "evaluation": "Unknown",
            "description": "Value outside defined thresholds",
            "requires_llm_recommendation": False
        }

    def generate_project_insights(self, project: Dict, l2_metrics: Dict) -> Dict:
        """
        Generate all L3 insights for a project (NON-LLM)

        Args:
            project: Project dict with L1 attributes
            l2_metrics: L2 calculated metrics

        Returns:
            {
                "L1_insights": [...],
                "L2_insights": [...],
                "summary": {
                    "excellent_count": 3,
                    "okay_count": 4,
                    "bad_count": 2,
                    "needs_llm_recommendations": ["npvCr", "irrPct"]
                }
            }
        """
        l1_insights = []
        l2_insights = []

        # Evaluate L1 metrics
        for metric_name in self.rules.get("L1_metrics", {}).keys():
            attr = project.get(metric_name)
            if attr and isinstance(attr, dict):
                value = data_service.get_value(attr)
                if value is not None:
                    insight = self.evaluate_metric(metric_name, value, layer="L1")
                    l1_insights.append(insight)

        # Evaluate L2 metrics
        for metric_name in self.rules.get("L2_metrics", {}).keys():
            attr = l2_metrics.get(metric_name)
            if attr and isinstance(attr, dict):
                value = data_service.get_value(attr)
                if value is not None:
                    insight = self.evaluate_metric(metric_name, value, layer="L2")
                    l2_insights.append(insight)

        # Generate summary
        all_insights = l1_insights + l2_insights
        excellent_count = len([i for i in all_insights if i.get("evaluation") == "Excellent"])
        okay_count = len([i for i in all_insights if i.get("evaluation") == "Okay"])
        bad_count = len([i for i in all_insights if i.get("evaluation") == "Bad"])
        needs_recommendations = [i.get("metric") for i in all_insights if i.get("requires_llm_recommendation")]

        return {
            "L1_insights": l1_insights,
            "L2_insights": l2_insights,
            "summary": {
                "excellent_count": excellent_count,
                "okay_count": okay_count,
                "bad_count": bad_count,
                "total_evaluated": len(all_insights),
                "needs_llm_recommendations": needs_recommendations,
                "overall_health": self._calculate_overall_health(excellent_count, okay_count, bad_count)
            },
            "layer": "L3",
            "source": "RuleEngine_NonLLM",
            "generated_at": str(Path("data/config/metric_rules.json").stat().st_mtime)
        }

    @staticmethod
    def _calculate_overall_health(excellent: int, okay: int, bad: int) -> str:
        """Calculate overall project health score (NON-LLM)"""
        total = excellent + okay + bad
        if total == 0:
            return "Unknown"

        excellent_pct = excellent / total
        bad_pct = bad / total

        if excellent_pct >= 0.6:
            return "Excellent"
        elif bad_pct >= 0.5:
            return "Bad"
        else:
            return "Okay"

    def get_metrics_needing_recommendations(self, insights: Dict) -> List[Dict]:
        """
        Get list of metrics that need LLM recommendations (Okay or Bad)

        Args:
            insights: Output from generate_project_insights()

        Returns:
            List of insights that require LLM recommendations
        """
        all_insights = insights.get("L1_insights", []) + insights.get("L2_insights", [])
        return [i for i in all_insights if i.get("requires_llm_recommendation")]


# Global insights engine instance
layer3_engine = Layer3InsightsEngine()
