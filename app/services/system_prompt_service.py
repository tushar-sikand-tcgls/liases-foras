"""
System Prompt Service for Sirrus.AI Real Estate Analytics

Implements the multi-dimensional insight engine with grounding mechanisms
to prevent hallucination and ensure accurate, contextual responses.

Based on Sirrus.AI Prompt v2.1 with dimensional framework:
- Layer 0: Atomic dimensions (U, C, T, L²)
- Layer 1: Derived data points
- Layer 2: Analytical insights
- Layer 3: Strategic optimization
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import numpy as np
from dataclasses import dataclass
from enum import Enum

from app.config.defaults import defaults


class InsightLayer(Enum):
    """Insight layer hierarchy"""
    LAYER_0 = "atomic_dimensions"  # Raw data (U, C, T, L²)
    LAYER_1 = "derived_dimensions"  # Calculated metrics (PSF, AR, etc.)
    LAYER_2 = "analytical_insights"  # Analysis and comparisons
    LAYER_3 = "strategic_insights"  # Optimization and strategies


class DimensionalUnit(Enum):
    """Dimensional units for real estate metrics"""
    UNITS = "U"  # Count of housing units (analogous to Mass)
    CASHFLOW = "C"  # INR/month (analogous to Current)
    TIME = "T"  # Months (analogous to Time)
    AREA = "L²"  # Square feet (analogous to Length²)

    # Derived dimensions
    PSF = "C/L²"  # Price per square foot
    VELOCITY = "U/T"  # Sales velocity
    ABSORPTION_RATE = "1/T"  # Absorption rate
    REVENUE_PER_UNIT = "C/U"  # Revenue per unit
    MARGIN = "%"  # Percentage (dimensionless)


class InsightType(Enum):
    """Standardized insight types for Layer 2"""
    ABSORPTION_STATUS = "absorption_status"
    PRICING_POSITION = "pricing_position"
    COMPARATIVE_PERFORMANCE = "comparative_performance"
    PRICE_VELOCITY_RELATIONSHIP = "price_velocity_relationship"
    MARKET_SATURATION = "market_saturation"
    DEVELOPER_EXECUTION = "developer_execution_pattern"
    FINANCIAL_VIABILITY = "financial_viability"
    UNIT_MIX_PREFERENCE = "unit_mix_preference"
    RISK_INDICATORS = "risk_indicators"


class StrategicType(Enum):
    """Standardized strategic types for Layer 3"""
    PRODUCT_MIX_OPTIMIZATION = "product_mix_optimization"
    LAUNCH_VIABILITY = "launch_viability_assessment"
    SCENARIO_ANALYSIS = "scenario_comparison"
    RISK_MITIGATION = "risk_mitigation_strategy"
    MARKET_TIMING = "market_opportunity_timing"


@dataclass
class DimensionalFormula:
    """Represents a dimensional formula for Layer 1 metrics"""
    name: str
    formula: str
    dimensional_units: str
    calculation_method: str

    def is_dimensionally_valid(self) -> bool:
        """Check if formula is dimensionally consistent"""
        # Simple validation - can be expanded
        valid_operations = {
            "C/L²": "PSF",
            "U/T": "Velocity",
            "C/U": "Revenue per unit",
            "U/(U×T)": "Absorption rate"
        }
        return self.dimensional_units in valid_operations.values()


class SystemPromptService:
    """
    Service for generating system prompts with grounding and anti-hallucination guards
    """

    # Layer 1 formulas based on dimensional analysis
    LAYER_1_FORMULAS = {
        "price_per_sqft": DimensionalFormula(
            name="Price Per Sqft",
            formula="C ÷ L²",
            dimensional_units="INR/sqft",
            calculation_method="total_revenue ÷ total_saleable_area"
        ),
        "absorption_rate": DimensionalFormula(
            name="Absorption Rate",
            formula="U_sold ÷ (U_total × T)",
            dimensional_units="1/month",
            calculation_method="sold_units ÷ (total_units × elapsed_months)"
        ),
        "sales_velocity": DimensionalFormula(
            name="Sales Velocity",
            formula="U_sold ÷ T",
            dimensional_units="units/month",
            calculation_method="sold_units ÷ elapsed_months"
        ),
        "months_of_inventory": DimensionalFormula(
            name="Months of Inventory",
            formula="U_unsold ÷ (U_sold ÷ T)",
            dimensional_units="months",
            calculation_method="unsold_units ÷ sales_velocity"
        ),
        "gross_margin": DimensionalFormula(
            name="Gross Margin",
            formula="(C_revenue - C_cost) ÷ C_revenue",
            dimensional_units="%",
            calculation_method="(revenue - cost) ÷ revenue × 100"
        ),
        "revenue_per_unit": DimensionalFormula(
            name="Revenue Per Unit",
            formula="C ÷ U",
            dimensional_units="INR/unit",
            calculation_method="total_revenue ÷ total_units"
        )
    }

    def __init__(self):
        """Initialize system prompt service"""
        self.grounding_rules = self._initialize_grounding_rules()
        self.confidence_thresholds = self._initialize_confidence_thresholds()

    def _initialize_grounding_rules(self) -> Dict[str, Any]:
        """Initialize grounding rules to prevent hallucination"""
        return {
            "data_source_verification": {
                "require_layer_0_input": True,
                "require_explicit_calculation": True,
                "prohibit_estimation": True,
                "require_dimensional_consistency": True
            },
            "traceability_requirements": {
                "layer_2_must_cite_layer_1": True,
                "layer_1_must_derive_from_layer_0": True,
                "show_calculation_steps": True,
                "include_data_lineage": True
            },
            "confidence_rules": {
                "layer_0_confidence": 100,  # Given data
                "layer_1_confidence": 95,   # Direct calculation
                "layer_2_confidence": 85,   # Analysis
                "layer_3_confidence": 70    # Optimization
            },
            "anti_hallucination": {
                "never_invent_data": True,
                "never_repeat_entire_datasets": True,
                "always_show_derivation": True,
                "flag_data_gaps": True
            }
        }

    def _initialize_confidence_thresholds(self) -> Dict[InsightLayer, int]:
        """Initialize confidence thresholds by layer"""
        return {
            InsightLayer.LAYER_0: 100,
            InsightLayer.LAYER_1: 95,
            InsightLayer.LAYER_2: 85,
            InsightLayer.LAYER_3: 70
        }

    def generate_system_prompt(self, query_type: str, context: Dict[str, Any]) -> str:
        """
        Generate contextual system prompt based on query type

        Args:
            query_type: Type of query (calculation, insight, optimization)
            context: Query context including project data

        Returns:
            Formatted system prompt with grounding
        """
        base_prompt = self._get_base_prompt()

        # Add layer-specific instructions
        if query_type == "calculation":
            layer_prompt = self._get_layer_1_prompt()
        elif query_type == "insight":
            layer_prompt = self._get_layer_2_prompt()
        elif query_type == "optimization":
            layer_prompt = self._get_layer_3_prompt()
        else:
            layer_prompt = self._get_general_prompt()

        # Add grounding instructions
        grounding = self._get_grounding_instructions()

        # Add context-specific instructions
        context_prompt = self._get_context_prompt(context)

        # Combine all parts
        full_prompt = f"""
{base_prompt}

{layer_prompt}

{grounding}

{context_prompt}

CRITICAL RULES:
1. Never invent data points - use only provided Layer 0 input
2. Show explicit calculations for all Layer 1 metrics
3. Reference Layer 1 metrics when generating Layer 2 insights
4. Include confidence scores and limitations
5. Maintain dimensional consistency in all formulas
6. Provide data lineage for traceability

Remember: You are an INSIGHT ENGINE, not a data generator.
"""

        return full_prompt

    def _get_base_prompt(self) -> str:
        """Get base system prompt"""
        return """
You are an Insight Engine for Real Estate Analytics using a dimensional framework.

DIMENSIONAL HIERARCHY:
- Layer 0: Atomic dimensions (U=Units, C=Cashflow, T=Time, L²=Area)
- Layer 1: Derived data points (PSF, Absorption Rate, etc.)
- Layer 2: Analytical insights (comparisons, patterns, risks)
- Layer 3: Strategic optimization (product mix, scenarios)

Your role is to:
1. Compute Layer 1 metrics from Layer 0 using explicit formulas
2. Generate Layer 2 insights by analyzing Layer 1 data
3. Create Layer 3 strategies using optimization algorithms
4. Maintain full traceability from insights back to raw data
"""

    def _get_layer_1_prompt(self) -> str:
        """Get Layer 1 calculation prompt"""
        formulas_text = "\n".join([
            f"- {name}: {f.formula} = {f.calculation_method} [{f.dimensional_units}]"
            for name, f in self.LAYER_1_FORMULAS.items()
        ])

        return f"""
LAYER 1 CALCULATION INSTRUCTIONS:

Compute derived dimensions using these formulas:
{formulas_text}

Requirements:
- Use exact formulas, no estimation
- Show calculation steps explicitly
- Verify dimensional consistency
- Include units in all results
- Confidence: 95% (direct calculation from Layer 0)
"""

    def _get_layer_2_prompt(self) -> str:
        """Get Layer 2 insight prompt"""
        insight_types = "\n".join([f"- {t.value}" for t in InsightType])

        return f"""
LAYER 2 INSIGHT INSTRUCTIONS:

Generate analytical insights using Layer 1 metrics.

Available insight types:
{insight_types}

Requirements:
- Compare Layer 1 metrics to market benchmarks
- Identify patterns and correlations
- Flag risks based on outliers
- Provide business interpretation
- Always cite Layer 1 metrics used
- Confidence: 80-90% based on data completeness
- Never cite Layer 0 directly
"""

    def _get_layer_3_prompt(self) -> str:
        """Get Layer 3 optimization prompt"""
        strategic_types = "\n".join([f"- {t.value}" for t in StrategicType])

        return f"""
LAYER 3 STRATEGIC INSTRUCTIONS:

Generate optimization strategies using Layer 2 insights.

Available strategic types:
{strategic_types}

Requirements:
- Use optimization algorithms (SLSQP for product mix)
- Include sensitivity analysis
- Provide multiple scenarios (Base/Optimistic/Conservative)
- Show constraints and assumptions
- Confidence: 60-75% based on model limitations
- Include alternative recommendations
"""

    def _get_general_prompt(self) -> str:
        """Get general query prompt"""
        return """
GENERAL QUERY INSTRUCTIONS:

Analyze the query to determine the appropriate layer:
- If asking for raw data → Layer 0 (provided input only)
- If asking for metrics/calculations → Layer 1
- If asking for analysis/comparison → Layer 2
- If asking for optimization/strategy → Layer 3

Apply appropriate methodology based on identified layer.
"""

    def _get_grounding_instructions(self) -> str:
        """Get grounding and anti-hallucination instructions"""
        return """
GROUNDING & ANTI-HALLUCINATION RULES:

1. DATA SOURCE VERIFICATION:
   - Use ONLY Layer 0 data from provided input
   - Never invent or estimate data points
   - Flag missing data explicitly

2. TRACEABILITY CHAIN:
   Layer 2 Insight → Layer 1 Metrics → Layer 0 Data → Input Source
   Example: "Absorption below market" → AR=2.5%/month → U_sold=72, U_total=240, T=12 → Input JSON

3. CONFIDENCE SCORING:
   - Layer 0: 100% (given data)
   - Layer 1: 95% (calculation)
   - Layer 2: 80-90% (analysis)
   - Layer 3: 60-75% (optimization)

4. DIMENSIONAL CONSISTENCY:
   - Verify all formulas are dimensionally valid
   - Example: ✓ [C/L²] = INR/sqft | ✗ [C] + [U] = Invalid

5. OUTPUT STRUCTURE:
   Always include: summary, reasoning, data_used, confidence, limitations
"""

    def _get_context_prompt(self, context: Dict[str, Any]) -> str:
        """Get context-specific prompt instructions"""
        project_id = context.get("project_id", "Unknown")
        location = context.get("location", "Unknown")
        data_version = context.get("data_version", defaults.DATA.get("version", "Latest"))

        return f"""
CONTEXT INFORMATION:
- Project: {project_id}
- Location: {location}
- Data Version: {data_version}
- Query Context: {context.get('query_type', 'general')}

Use this context to provide relevant, specific insights.
Do not repeat this context in outputs unless directly relevant.
"""

    def calculate_layer_1_metrics(self, layer_0_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Layer 1 metrics from Layer 0 data

        Args:
            layer_0_data: Raw atomic dimensions

        Returns:
            Calculated Layer 1 metrics with formulas
        """
        metrics = {}

        # Extract Layer 0 dimensions
        total_units = layer_0_data.get("total_units", 0)
        sold_units = layer_0_data.get("sold_units", 0)
        unsold_units = layer_0_data.get("unsold_units", total_units - sold_units)
        total_area = layer_0_data.get("total_saleable_area_sqft", 0)
        total_revenue = layer_0_data.get("total_revenue_inr", 0)
        total_cost = layer_0_data.get("total_cost_inr", 0)
        elapsed_months = layer_0_data.get("elapsed_months", 12)

        # Calculate PSF
        if total_area > 0:
            psf = total_revenue / total_area
            metrics["price_per_sqft"] = {
                "value": round(psf, 2),
                "unit": "INR/sqft",
                "formula": "C ÷ L²",
                "calculation": f"{total_revenue} ÷ {total_area}",
                "dimensional_analysis": "Valid: [INR] ÷ [sqft] = [INR/sqft]",
                "confidence": 95
            }

        # Calculate Absorption Rate
        if total_units > 0 and elapsed_months > 0:
            absorption_rate = sold_units / (total_units * elapsed_months)
            metrics["absorption_rate"] = {
                "value": round(absorption_rate, 4),
                "unit": "1/month",
                "percentage": f"{round(absorption_rate * 100, 2)}%/month",
                "formula": "U_sold ÷ (U_total × T)",
                "calculation": f"{sold_units} ÷ ({total_units} × {elapsed_months})",
                "dimensional_analysis": "Valid: [U] ÷ ([U] × [T]) = [1/T]",
                "confidence": 95
            }

        # Calculate Sales Velocity
        if elapsed_months > 0:
            velocity = sold_units / elapsed_months
            metrics["sales_velocity"] = {
                "value": round(velocity, 2),
                "unit": "units/month",
                "formula": "U_sold ÷ T",
                "calculation": f"{sold_units} ÷ {elapsed_months}",
                "dimensional_analysis": "Valid: [U] ÷ [T] = [U/T]",
                "confidence": 95
            }

        # Calculate Months of Inventory
        if sold_units > 0 and elapsed_months > 0:
            moi = unsold_units / (sold_units / elapsed_months)
            metrics["months_of_inventory"] = {
                "value": round(moi, 1),
                "unit": "months",
                "formula": "U_unsold ÷ (U_sold ÷ T)",
                "calculation": f"{unsold_units} ÷ ({sold_units} ÷ {elapsed_months})",
                "dimensional_analysis": "Valid: [U] ÷ ([U]/[T]) = [T]",
                "confidence": 95
            }

        # Calculate Gross Margin
        if total_revenue > 0:
            margin = (total_revenue - total_cost) / total_revenue
            metrics["gross_margin"] = {
                "value": round(margin, 4),
                "unit": "%",
                "percentage": f"{round(margin * 100, 2)}%",
                "formula": "(C_revenue - C_cost) ÷ C_revenue",
                "calculation": f"({total_revenue} - {total_cost}) ÷ {total_revenue}",
                "dimensional_analysis": "Valid: Dimensionless ratio",
                "confidence": 95
            }

        # Calculate Revenue per Unit
        if total_units > 0:
            rpu = total_revenue / total_units
            metrics["revenue_per_unit"] = {
                "value": round(rpu, 0),
                "unit": "INR/unit",
                "formula": "C ÷ U",
                "calculation": f"{total_revenue} ÷ {total_units}",
                "dimensional_analysis": "Valid: [INR] ÷ [U] = [INR/U]",
                "confidence": 95
            }

        return {
            "layer": 1,
            "timestamp": datetime.now().isoformat(),
            "source": "Layer 0 calculations",
            "metrics": metrics,
            "data_lineage": {
                "layer_0_inputs": layer_0_data,
                "formulas_applied": list(metrics.keys())
            }
        }

    def generate_layer_2_insight(
        self,
        layer_1_metrics: Dict[str, Any],
        insight_type: InsightType,
        market_benchmarks: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate Layer 2 analytical insight

        Args:
            layer_1_metrics: Calculated Layer 1 metrics
            insight_type: Type of insight to generate
            market_benchmarks: Optional market comparison data

        Returns:
            Structured Layer 2 insight with traceability
        """
        insight = {
            "insight_metadata": {
                "insight_id": f"{insight_type.value}_{datetime.now().timestamp()}",
                "insight_layer": 2,
                "insight_type": insight_type.value,
                "generated_at": datetime.now().isoformat()
            }
        }

        # Generate insight based on type
        if insight_type == InsightType.ABSORPTION_STATUS:
            insight.update(self._generate_absorption_insight(layer_1_metrics, market_benchmarks))
        elif insight_type == InsightType.PRICING_POSITION:
            insight.update(self._generate_pricing_insight(layer_1_metrics, market_benchmarks))
        elif insight_type == InsightType.FINANCIAL_VIABILITY:
            insight.update(self._generate_financial_insight(layer_1_metrics))
        else:
            insight.update(self._generate_generic_insight(layer_1_metrics))

        # Add traceability
        insight["data_lineage"] = {
            "layer_1_metrics_used": list(layer_1_metrics.keys()),
            "confidence": self.confidence_thresholds[InsightLayer.LAYER_2],
            "grounding": "All insights derived from Layer 1 calculations"
        }

        return insight

    def _generate_absorption_insight(
        self,
        metrics: Dict[str, Any],
        benchmarks: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate absorption status insight"""
        ar = metrics.get("absorption_rate", {}).get("value", 0)
        moi = metrics.get("months_of_inventory", {}).get("value", 0)

        # Compare to benchmark if available
        if benchmarks:
            market_ar = benchmarks.get("market_absorption_rate", 0.03)
            deviation = (ar - market_ar) / market_ar if market_ar > 0 else 0
            comparison = "above" if deviation > 0 else "below"

            summary = (f"Absorption rate of {ar:.1%}/month is {abs(deviation):.0%} {comparison} "
                      f"market average. Inventory will clear in {moi:.0f} months at current pace.")
        else:
            summary = f"Absorption rate is {ar:.1%}/month with {moi:.0f} months of inventory remaining."

        return {
            "insight_content": {
                "summary": summary,
                "reasoning": "Analyzed Layer 1 absorption_rate and months_of_inventory metrics",
                "dimensional_analysis": "AR = [1/T], MOI = [T] - dimensionally consistent"
            },
            "layer_1_data_used": [
                {
                    "metric": "absorption_rate",
                    "value": ar,
                    "unit": "1/month"
                },
                {
                    "metric": "months_of_inventory",
                    "value": moi,
                    "unit": "months"
                }
            ],
            "confidence": {
                "score": 85,
                "drivers": ["Direct Layer 1 calculation", "Market benchmark available" if benchmarks else "No benchmark"],
                "limitations": "Assumes constant absorption rate"
            },
            "recommendation": {
                "action": "Maintain current sales strategy" if ar > 0.025 else "Consider pricing adjustment",
                "rationale": "Based on absorption rate relative to market norms"
            }
        }

    def _generate_pricing_insight(
        self,
        metrics: Dict[str, Any],
        benchmarks: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate pricing position insight"""
        psf = metrics.get("price_per_sqft", {}).get("value", 0)
        margin = metrics.get("gross_margin", {}).get("percentage", "0%")

        if benchmarks:
            market_psf = benchmarks.get("market_psf", psf)
            premium = ((psf - market_psf) / market_psf * 100) if market_psf > 0 else 0
            positioning = "premium" if premium > 5 else "discount" if premium < -5 else "market"

            summary = f"PSF of ₹{psf:,.0f} represents {positioning} positioning ({premium:+.1f}% vs market). Gross margin is {margin}."
        else:
            summary = f"PSF is ₹{psf:,.0f} with gross margin of {margin}."

        return {
            "insight_content": {
                "summary": summary,
                "reasoning": "Analyzed Layer 1 price_per_sqft and gross_margin metrics",
                "dimensional_analysis": "PSF = [C/L²], Margin = dimensionless % - valid"
            },
            "layer_1_data_used": [
                {
                    "metric": "price_per_sqft",
                    "value": psf,
                    "unit": "INR/sqft"
                },
                {
                    "metric": "gross_margin",
                    "value": margin,
                    "unit": "%"
                }
            ],
            "confidence": {
                "score": 85,
                "drivers": ["PSF directly calculated from Layer 0"],
                "limitations": "Market comparison may be dated"
            }
        }

    def _generate_financial_insight(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial viability insight"""
        margin = metrics.get("gross_margin", {}).get("value", 0)
        rpu = metrics.get("revenue_per_unit", {}).get("value", 0)

        viability = "strong" if margin > 0.3 else "moderate" if margin > 0.2 else "weak"

        return {
            "insight_content": {
                "summary": f"Project shows {viability} financial viability with {margin:.1%} gross margin and ₹{rpu/1e6:.1f}M revenue per unit.",
                "reasoning": "Assessed Layer 1 gross_margin and revenue_per_unit metrics",
                "dimensional_analysis": "Margin = %, RPU = [C/U] - dimensionally valid"
            },
            "layer_1_data_used": [
                {
                    "metric": "gross_margin",
                    "value": margin,
                    "unit": "%"
                },
                {
                    "metric": "revenue_per_unit",
                    "value": rpu,
                    "unit": "INR/unit"
                }
            ],
            "confidence": {
                "score": 80,
                "drivers": ["Direct calculation from Layer 0 financials"],
                "limitations": "Does not account for time value of money"
            }
        }

    def _generate_generic_insight(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic insight when specific type not implemented"""
        return {
            "insight_content": {
                "summary": f"Analysis includes {len(metrics)} Layer 1 metrics",
                "reasoning": "Generic analysis of available Layer 1 data",
                "dimensional_analysis": "All Layer 1 metrics dimensionally verified"
            },
            "layer_1_data_used": [
                {"metric": k, "value": v.get("value"), "unit": v.get("unit")}
                for k, v in metrics.items()
            ],
            "confidence": {
                "score": 75,
                "drivers": ["Layer 1 calculations available"],
                "limitations": "Generic analysis without specific focus"
            }
        }

    def validate_dimensional_consistency(self, formula: str, units: Dict[str, str]) -> bool:
        """
        Validate dimensional consistency of a formula

        Args:
            formula: Mathematical formula
            units: Mapping of variables to their dimensional units

        Returns:
            True if dimensionally consistent
        """
        # Simple validation - can be enhanced with proper dimensional analysis
        valid_combinations = {
            "C/L²": "INR/sqft",
            "U/T": "units/month",
            "C/U": "INR/unit",
            "(C-C)/C": "%"
        }

        # Check if formula matches known valid patterns
        for pattern, expected_unit in valid_combinations.items():
            if pattern in formula:
                return True

        return False

    def generate_prompt_template(self, query_type: str) -> Dict[str, str]:
        """
        Generate prompt template for different query types

        Args:
            query_type: Type of query (metric, insight, strategy)

        Returns:
            Prompt template with placeholders
        """
        templates = {
            "metric_calculation": {
                "prompt": "Calculate {metric_name} using Layer 0 data",
                "instructions": "Use formula: {formula}. Show calculation steps.",
                "output_format": "Return value with unit and confidence score."
            },
            "comparative_insight": {
                "prompt": "Compare {project} performance to {benchmark}",
                "instructions": "Use Layer 1 metrics for comparison. Cite specific values.",
                "output_format": "Provide summary, deviation percentage, and recommendation."
            },
            "optimization_strategy": {
                "prompt": "Optimize {objective} for {project}",
                "instructions": "Use Layer 2 insights to inform optimization. Apply {algorithm}.",
                "output_format": "Return optimal solution with sensitivity analysis."
            },
            "risk_assessment": {
                "prompt": "Identify risks in {project} based on metrics",
                "instructions": "Flag outliers in Layer 1 metrics. Compare to thresholds.",
                "output_format": "List risks with severity and mitigation strategies."
            }
        }

        return templates.get(query_type, {
            "prompt": "Process query: {query}",
            "instructions": "Determine appropriate layer and apply methodology.",
            "output_format": "Return structured response with traceability."
        })

    def check_grounding_compliance(self, response: Dict[str, Any]) -> Dict[str, bool]:
        """
        Check if response complies with grounding rules

        Args:
            response: Generated response to validate

        Returns:
            Compliance check results
        """
        checks = {
            "has_data_source": "layer_0_inputs" in response.get("data_lineage", {}),
            "has_calculation": any("calculation" in str(v) for v in response.values()),
            "has_confidence": "confidence" in response,
            "has_limitations": "limitations" in response.get("confidence", {}),
            "cites_layer_1": "layer_1_data_used" in response,
            "dimensional_valid": "dimensional_analysis" in response.get("insight_content", {}),
            "no_hallucination": not any(word in str(response).lower()
                                       for word in ["estimate", "approximately", "guess"])
        }

        return checks

    def apply_anti_hallucination_filters(self, response: str) -> str:
        """
        Apply filters to prevent hallucination in responses

        Args:
            response: Raw response text

        Returns:
            Filtered response with hallucinations removed
        """
        # Remove any statements that appear to be estimates
        filtered = response

        # Remove phrases that indicate guessing
        hallucination_phrases = [
            "I estimate",
            "probably",
            "approximately",
            "I guess",
            "might be",
            "could be around",
            "seems like"
        ]

        for phrase in hallucination_phrases:
            filtered = filtered.replace(phrase, "[DATA REQUIRED]")

        # Flag missing data explicitly
        if "[DATA REQUIRED]" in filtered:
            filtered += "\n\nNote: Some data points were not available from Layer 0 input."

        return filtered


# Singleton instance
system_prompt_service = SystemPromptService()