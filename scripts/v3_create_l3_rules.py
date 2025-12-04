"""
V3.0.0: Layer 3 Rules Creation Script
======================================

Creates configurable L3 rules in Neo4j for evaluating L2 metrics.

Rules define thresholds for each L2 metric and determine when to:
- Generate positive template insights (GOOD, EXCELLENT assessment)
- Trigger Gemini API for negative feedback (POOR, CRITICAL assessment)

Each rule is stored as an (:L3_Rule) node with:
- ruleId: Unique identifier
- metricName: L2 metric to evaluate
- thresholds: Assessment ranges (CRITICAL, POOR, GOOD, EXCELLENT)
- configurable: Whether business users can modify thresholds
"""

import os
from typing import Dict, List
from neo4j import GraphDatabase
from datetime import datetime


class L3RuleCreator:
    """Create and manage L3 rules in Neo4j"""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.creation_timestamp = datetime.now().isoformat()

    def close(self):
        self.driver.close()

    def clear_l3_rules(self):
        """Remove all existing L3 rules"""
        with self.driver.session() as session:
            result = session.run("MATCH (r:L3_Rule) DETACH DELETE r RETURN count(r) as deletedCount")
            record = result.single()
            deleted = record["deletedCount"] if record else 0
            print(f"✓ Cleared {deleted} existing L3 rules")

    def create_l3_rule(self, rule: Dict):
        """Create a single L3 rule in Neo4j"""
        with self.driver.session() as session:
            session.run("""
                CREATE (r:L3_Rule {
                    ruleId: $ruleId,
                    metricName: $metricName,
                    metricLayer: $metricLayer,
                    description: $description,
                    thresholds: $thresholds,
                    configurable: $configurable,
                    createdAt: $createdAt,
                    lastUpdated: $lastUpdated
                })
            """,
                ruleId=rule["ruleId"],
                metricName=rule["metricName"],
                metricLayer=rule["metricLayer"],
                description=rule["description"],
                thresholds=str(rule["thresholds"]),  # Store as JSON string
                configurable=rule["configurable"],
                createdAt=self.creation_timestamp,
                lastUpdated=self.creation_timestamp
            )

    def get_core_rules(self) -> List[Dict]:
        """Define the 10 core L3 rules for L2 metrics"""
        return [
            {
                "ruleId": "R001",
                "metricName": "absorptionRate",
                "metricLayer": "L2",
                "description": "Evaluate monthly absorption rate (fraction of units sold per month)",
                "thresholds": [
                    {"min": None, "max": 0.005, "assessment": "CRITICAL", "isNegative": True,
                     "template": "Absorption rate is critically low at {value:.4f} per month. Immediate action required."},
                    {"min": 0.005, "max": 0.010, "assessment": "POOR", "isNegative": True,
                     "template": "Absorption rate is poor at {value:.4f} per month. Significant improvement needed."},
                    {"min": 0.010, "max": 0.015, "assessment": "GOOD", "isNegative": False,
                     "template": "Absorption rate is good at {value:.4f} per month, indicating healthy market dynamics."},
                    {"min": 0.015, "max": None, "assessment": "EXCELLENT", "isNegative": False,
                     "template": "Absorption rate is excellent at {value:.4f} per month, showing strong project performance."}
                ],
                "configurable": True
            },
            {
                "ruleId": "R002",
                "metricName": "monthsInventory",
                "metricLayer": "L2",
                "description": "Evaluate remaining months of inventory at current sales velocity",
                "thresholds": [
                    {"min": 36, "max": None, "assessment": "CRITICAL", "isNegative": True,
                     "template": "Months of inventory is critically high at {value:.1f} months (>3 years). Urgent intervention required."},
                    {"min": 24, "max": 36, "assessment": "POOR", "isNegative": True,
                     "template": "Months of inventory is poor at {value:.1f} months (2-3 years). Improvement needed."},
                    {"min": 12, "max": 24, "assessment": "GOOD", "isNegative": False,
                     "template": "Months of inventory is good at {value:.1f} months (1-2 years), showing balanced supply."},
                    {"min": None, "max": 12, "assessment": "EXCELLENT", "isNegative": False,
                     "template": "Months of inventory is excellent at {value:.1f} months (<1 year), indicating strong sales velocity."}
                ],
                "configurable": True
            },
            {
                "ruleId": "R003",
                "metricName": "priceAppreciation",
                "metricLayer": "L2",
                "description": "Evaluate price appreciation from launch PSF to current PSF",
                "thresholds": [
                    {"min": None, "max": 0.0, "assessment": "CRITICAL", "isNegative": True,
                     "template": "Price appreciation is negative at {value:.2%}. Price depreciation detected."},
                    {"min": 0.0, "max": 0.05, "assessment": "POOR", "isNegative": True,
                     "template": "Price appreciation is poor at {value:.2%} (<5%). Below market expectations."},
                    {"min": 0.05, "max": 0.15, "assessment": "GOOD", "isNegative": False,
                     "template": "Price appreciation is good at {value:.2%} (5-15%), showing healthy growth."},
                    {"min": 0.15, "max": None, "assessment": "EXCELLENT", "isNegative": False,
                     "template": "Price appreciation is excellent at {value:.2%} (>15%), exceeding market expectations."}
                ],
                "configurable": True
            },
            {
                "ruleId": "R004",
                "metricName": "salesVelocity",
                "metricLayer": "L2",
                "description": "Evaluate sales velocity in units sold per month",
                "thresholds": [
                    {"min": None, "max": 5, "assessment": "POOR", "isNegative": True,
                     "template": "Sales velocity is poor at {value:.1f} units/month (<5). Improvement needed."},
                    {"min": 5, "max": 10, "assessment": "GOOD", "isNegative": False,
                     "template": "Sales velocity is good at {value:.1f} units/month (5-10), showing steady sales."},
                    {"min": 10, "max": None, "assessment": "EXCELLENT", "isNegative": False,
                     "template": "Sales velocity is excellent at {value:.1f} units/month (>10), indicating high demand."}
                ],
                "configurable": True
            },
            {
                "ruleId": "R005",
                "metricName": "landEfficiency",
                "metricLayer": "L2",
                "description": "Evaluate land efficiency in units per acre",
                "thresholds": [
                    {"min": None, "max": 50, "assessment": "POOR", "isNegative": True,
                     "template": "Land efficiency is poor at {value:.1f} units/acre (<50). Low density development."},
                    {"min": 50, "max": 100, "assessment": "GOOD", "isNegative": False,
                     "template": "Land efficiency is good at {value:.1f} units/acre (50-100), showing balanced density."},
                    {"min": 100, "max": None, "assessment": "EXCELLENT", "isNegative": False,
                     "template": "Land efficiency is excellent at {value:.1f} units/acre (>100), indicating high-density development."}
                ],
                "configurable": True
            },
            {
                "ruleId": "R006",
                "metricName": "sellThroughRate",
                "metricLayer": "L2",
                "description": "Evaluate sell-through rate (fraction of units sold)",
                "thresholds": [
                    {"min": None, "max": 0.50, "assessment": "POOR", "isNegative": True,
                     "template": "Sell-through rate is poor at {value:.1%} (<50%). Low market acceptance."},
                    {"min": 0.50, "max": 0.75, "assessment": "GOOD", "isNegative": False,
                     "template": "Sell-through rate is good at {value:.1%} (50-75%), showing moderate success."},
                    {"min": 0.75, "max": None, "assessment": "EXCELLENT", "isNegative": False,
                     "template": "Sell-through rate is excellent at {value:.1%} (>75%), indicating high market acceptance."}
                ],
                "configurable": True
            },
            {
                "ruleId": "R007",
                "metricName": "psfGrowthRate",
                "metricLayer": "L2",
                "description": "Evaluate PSF growth rate per year",
                "thresholds": [
                    {"min": None, "max": 0.05, "assessment": "POOR", "isNegative": True,
                     "template": "PSF growth rate is poor at {value:.2%}/year (<5%). Below inflation."},
                    {"min": 0.05, "max": 0.10, "assessment": "GOOD", "isNegative": False,
                     "template": "PSF growth rate is good at {value:.2%}/year (5-10%), matching market growth."},
                    {"min": 0.10, "max": None, "assessment": "EXCELLENT", "isNegative": False,
                     "template": "PSF growth rate is excellent at {value:.2%}/year (>10%), outpacing market."}
                ],
                "configurable": True
            },
            {
                "ruleId": "R008",
                "metricName": "revenuePerMonth",
                "metricLayer": "L2",
                "description": "Evaluate revenue per month in INR Cr",
                "thresholds": [
                    {"min": None, "max": 5, "assessment": "POOR", "isNegative": True,
                     "template": "Revenue per month is poor at ₹{value:.2f} Cr/month (<₹5 Cr). Low cash flow."},
                    {"min": 5, "max": 10, "assessment": "GOOD", "isNegative": False,
                     "template": "Revenue per month is good at ₹{value:.2f} Cr/month (₹5-10 Cr), showing healthy cash flow."},
                    {"min": 10, "max": None, "assessment": "EXCELLENT", "isNegative": False,
                     "template": "Revenue per month is excellent at ₹{value:.2f} Cr/month (>₹10 Cr), indicating strong revenue generation."}
                ],
                "configurable": True
            },
            {
                "ruleId": "R009",
                "metricName": "averageUnitSize",
                "metricLayer": "L2",
                "description": "Evaluate average unit size in sqft/unit (context-dependent)",
                "thresholds": [
                    {"min": None, "max": 300, "assessment": "COMPACT", "isNegative": False,
                     "template": "Average unit size is compact at {value:.0f} sqft/unit. Suitable for affordable housing."},
                    {"min": 300, "max": 500, "assessment": "STANDARD", "isNegative": False,
                     "template": "Average unit size is standard at {value:.0f} sqft/unit. Typical 1-2 BHK configuration."},
                    {"min": 500, "max": 1000, "assessment": "SPACIOUS", "isNegative": False,
                     "template": "Average unit size is spacious at {value:.0f} sqft/unit. Premium 2-3 BHK configuration."},
                    {"min": 1000, "max": None, "assessment": "LUXURY", "isNegative": False,
                     "template": "Average unit size is luxury at {value:.0f} sqft/unit. High-end large units."}
                ],
                "configurable": True
            },
            {
                "ruleId": "R010",
                "metricName": "costPerUnit",
                "metricLayer": "L2",
                "description": "Evaluate cost per unit in INR",
                "thresholds": [
                    {"min": None, "max": 2000000, "assessment": "AFFORDABLE", "isNegative": False,
                     "template": "Cost per unit is affordable at ₹{value:,.0f} (<₹20 Lakh). Budget segment."},
                    {"min": 2000000, "max": 5000000, "assessment": "MID-RANGE", "isNegative": False,
                     "template": "Cost per unit is mid-range at ₹{value:,.0f} (₹20-50 Lakh). Mass market segment."},
                    {"min": 5000000, "max": 10000000, "assessment": "PREMIUM", "isNegative": False,
                     "template": "Cost per unit is premium at ₹{value:,.0f} (₹50 Lakh-₹1 Cr). Upper mid-market segment."},
                    {"min": 10000000, "max": None, "assessment": "LUXURY", "isNegative": False,
                     "template": "Cost per unit is luxury at ₹{value:,.0f} (>₹1 Cr). High-end segment."}
                ],
                "configurable": True
            }
        ]

    def load_all_rules(self):
        """Load all core L3 rules into Neo4j"""
        rules = self.get_core_rules()

        print(f"\nLoading {len(rules)} L3 rules into Neo4j...")
        print("=" * 70)

        for rule in rules:
            self.create_l3_rule(rule)
            print(f"✓ Created rule {rule['ruleId']}: {rule['metricName']}")
            print(f"  Thresholds: {len(rule['thresholds'])} assessment levels")

        print("=" * 70)
        print(f"✅ Successfully loaded {len(rules)} L3 rules")

    def verify_rules(self):
        """Verify L3 rules were created correctly"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (r:L3_Rule)
                RETURN r.ruleId as ruleId, r.metricName as metricName, r.configurable as configurable
                ORDER BY r.ruleId
            """)

            rules = list(result)
            print(f"\n{'='*70}")
            print(f"L3 Rules Verification")
            print(f"{'='*70}")
            print(f"Total rules: {len(rules)}\n")

            for record in rules:
                print(f"  ✓ {record['ruleId']}: {record['metricName']} (configurable: {record['configurable']})")

            return len(rules)


def main():
    """Main execution: Create L3 rules in Neo4j"""
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "liasesforas123")

    creator = L3RuleCreator(neo4j_uri, neo4j_user, neo4j_password)

    try:
        print("=" * 70)
        print("V3.0.0: Layer 3 Rules Creation")
        print("=" * 70)
        print()

        # Clear existing rules
        creator.clear_l3_rules()

        # Load core rules
        creator.load_all_rules()

        # Verify
        rule_count = creator.verify_rules()

        print(f"\n{'='*70}")
        print(f"✅ L3 Rules Creation Complete: {rule_count} rules loaded")
        print(f"{'='*70}")

    finally:
        creator.close()


if __name__ == "__main__":
    main()
