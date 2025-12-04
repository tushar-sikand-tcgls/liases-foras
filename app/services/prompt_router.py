"""
Dynamic Prompt Router for Calculator Selection

This module analyzes user prompts and intelligently routes them to the
appropriate calculator or retrieval mechanism without hardcoded logic.
Uses semantic matching and keyword analysis for dynamic routing.
"""

from typing import Dict, List, Tuple, Optional, Any
import re
from dataclasses import dataclass
from enum import Enum
from app.config.defaults import defaults


class LayerType(Enum):
    """Knowledge graph layers"""
    LAYER_0 = 0  # Raw dimensions (U, L², T, CF)
    LAYER_1 = 1  # Derived metrics (PSF, ASP, etc.)
    LAYER_2 = 2  # Financial & Statistical
    LAYER_3 = 3  # Optimization & Scenarios
    LAYER_4 = 4  # Market insights (Vector search)
    UNKNOWN = -1


@dataclass
class RouteDecision:
    """Routing decision for a query"""
    layer: LayerType
    capability: str
    confidence: float  # 0.0 to 1.0
    reason: str
    requires_vector_search: bool
    parameters_needed: List[str]


class PromptRouter:
    """
    Dynamically routes prompts to appropriate calculators
    without hardcoded logic
    """

    def __init__(self):
        """Initialize the prompt router with capability patterns"""

        # Dynamic capability patterns - easily extensible
        self.capability_patterns = {
            # Layer 0: Raw dimensions (RETRIEVAL, not calculation)
            "get_project_dimensions": {
                "keywords": ["dimensions", "raw", "units", "area", "time", "cash flow", "U", "L2", "CF", "T",
                           "project size", "total units", "how many units", "number of units"],
                "patterns": [
                    r"what.*dimensions",
                    r"get.*project.*data",
                    r"show.*raw.*values",
                    r"what\s+(is|are)\s+the\s+(project\s+)?size",
                    r"what\s+(is|are)\s+the\s+total\s+units",
                    r"how\s+many\s+units",
                    r"project\s+size\s+of",
                    r"total\s+units\s+(of|in|for)"
                ],
                "layer": LayerType.LAYER_0
            },

            # Layer 1: Derived metrics
            "calculate_psf": {
                "keywords": ["psf", "price per", "per sqft", "square foot"],
                "patterns": [
                    r"price\s+per\s+sq",
                    r"psf",
                    r"per\s+square\s+foot"
                ],
                "layer": LayerType.LAYER_1
            },
            "calculate_asp": {
                "keywords": ["asp", "average selling", "selling price", "per unit"],
                "patterns": [
                    r"average\s+selling",
                    r"asp",
                    r"price\s+per\s+unit"
                ],
                "layer": LayerType.LAYER_1
            },
            "calculate_absorption_rate": {
                "keywords": ["absorption", "rate", "sold", "percentage"],
                "patterns": [
                    r"absorption\s+rate",
                    r"how\s+fast.*selling",
                    r"sales\s+rate"
                ],
                "layer": LayerType.LAYER_1
            },
            "calculate_sales_velocity": {
                "keywords": ["velocity", "sales", "units per month", "speed"],
                "patterns": [
                    r"sales\s+velocity",
                    r"units.*month",
                    r"selling\s+speed"
                ],
                "layer": LayerType.LAYER_1
            },

            # Layer 2: Financial metrics
            "calculate_npv": {
                "keywords": ["npv", "net present value", "present value"],
                "patterns": [
                    r"npv",
                    r"net\s+present\s+value",
                    r"calculate.*present\s+value"
                ],
                "layer": LayerType.LAYER_2
            },
            "calculate_irr": {
                "keywords": ["irr", "internal rate", "return rate"],
                "patterns": [
                    r"irr",
                    r"internal\s+rate",
                    r"rate\s+of\s+return"
                ],
                "layer": LayerType.LAYER_2
            },
            "calculate_payback_period": {
                "keywords": ["payback", "recovery", "break even"],
                "patterns": [
                    r"payback",
                    r"recover.*investment",
                    r"break\s*even"
                ],
                "layer": LayerType.LAYER_2
            },

            # Layer 2: Statistical operations
            "calculate_statistics": {
                "keywords": ["average", "mean", "median", "standard deviation", "variance",
                           "total", "sum", "mode", "percentile", "distribution", "outlier"],
                "patterns": [
                    r"(average|mean|median|mode)",
                    r"standard\s+deviation",
                    r"variance",
                    r"percentile",
                    r"distribution",
                    r"outlier",
                    r"statistical\s+analysis",
                    r"total|sum"
                ],
                "layer": LayerType.LAYER_2
            },
            "aggregate_by_region": {
                "keywords": ["aggregate", "region", "micromarket", "all projects"],
                "patterns": [
                    r"aggregate.*region",
                    r"all\s+projects\s+in",
                    r"total.*micromarket"
                ],
                "layer": LayerType.LAYER_2
            },
            "get_top_n_projects": {
                "keywords": ["top", "best", "highest", "lowest", "ranking", "bottom"],
                "patterns": [
                    r"top\s+\d+",
                    r"best\s+\d+",
                    r"highest.*projects",
                    r"lowest.*projects",
                    r"rank.*projects"
                ],
                "layer": LayerType.LAYER_2
            },

            # Layer 3: Optimization
            "optimize_product_mix": {
                "keywords": ["optimize", "product mix", "unit mix", "best combination"],
                "patterns": [
                    r"optimize.*mix",
                    r"best.*combination",
                    r"optimal.*units",
                    r"maximize.*irr"
                ],
                "layer": LayerType.LAYER_3
            },
            "market_opportunity_scoring": {
                "keywords": ["opportunity", "scoring", "opps", "market potential"],
                "patterns": [
                    r"opportunity\s+scor",
                    r"market.*potential",
                    r"opps\s+score"
                ],
                "layer": LayerType.LAYER_3
            },

            # Layer 4: Market insights (Vector search)
            "get_market_insights": {
                "keywords": ["market", "insights", "trends", "report", "intelligence",
                           "infrastructure", "economy", "demographics"],
                "patterns": [
                    r"market.*insights",
                    r"city.*report",
                    r"infrastructure",
                    r"economic.*outlook",
                    r"demographic"
                ],
                "layer": LayerType.LAYER_4,
                "requires_vector": True
            }
        }

        # Financial keywords for context
        self.financial_keywords = set([
            "investment", "cash flow", "revenue", "cost", "profit",
            "discount", "financial", "money", "budget", "capital"
        ])

        # Statistical keywords for context
        self.statistical_keywords = set([
            "data", "analysis", "distribution", "sample", "population",
            "correlation", "regression", "probability", "statistics"
        ])

        # Location keywords
        self.location_keywords = set([
            "pune", "mumbai", "bangalore", "delhi", "chakan", "hinjewadi",
            "kharadi", "wakad", "baner", "city", "location", "region"
        ])

    def analyze_prompt(self, prompt: str) -> RouteDecision:
        """
        Analyze a user prompt and determine the best routing

        Args:
            prompt: User's natural language query

        Returns:
            RouteDecision with layer, capability, and confidence
        """
        prompt_lower = prompt.lower().strip()

        # Track best match
        best_match = None
        best_score = 0.0

        # Check each capability
        for capability, config in self.capability_patterns.items():
            score = self._calculate_match_score(prompt_lower, config)

            if score > best_score:
                best_score = score
                best_match = (capability, config)

        # If we have a good match
        if best_match and best_score > 0.3:  # Confidence threshold
            capability, config = best_match

            # Extract parameters needed
            parameters = self._extract_parameters(prompt_lower, capability)

            # Check if vector search is needed
            requires_vector = config.get("requires_vector", False) or \
                             self._needs_vector_search(prompt_lower)

            return RouteDecision(
                layer=config["layer"],
                capability=capability,
                confidence=best_score,
                reason=f"Matched patterns for {capability}",
                requires_vector_search=requires_vector,
                parameters_needed=parameters
            )

        # Default to vector search for unknown queries
        return RouteDecision(
            layer=LayerType.LAYER_4,
            capability="get_market_insights",
            confidence=0.5,
            reason="No specific calculator matched - using semantic search",
            requires_vector_search=True,
            parameters_needed=["query"]
        )

    def _calculate_match_score(self, prompt: str, config: Dict) -> float:
        """
        Calculate match score for a capability configuration

        Args:
            prompt: Lowercase prompt
            config: Capability configuration

        Returns:
            Match score between 0.0 and 1.0
        """
        score = 0.0
        max_score = 0.0

        # Check keyword matches (40% weight)
        keywords = config.get("keywords", [])
        if keywords:
            keyword_matches = sum(1 for kw in keywords if kw in prompt)
            keyword_score = keyword_matches / len(keywords) if keywords else 0
            score += keyword_score * 0.4
            max_score += 0.4

        # Check pattern matches (60% weight)
        patterns = config.get("patterns", [])
        if patterns:
            pattern_matches = sum(1 for pattern in patterns
                                 if re.search(pattern, prompt, re.IGNORECASE))
            pattern_score = pattern_matches / len(patterns) if patterns else 0
            score += pattern_score * 0.6
            max_score += 0.6

        # Normalize score
        return score / max_score if max_score > 0 else 0.0

    def _extract_parameters(self, prompt: str, capability: str) -> List[str]:
        """
        Extract required parameters from the prompt

        Args:
            prompt: User prompt
            capability: Selected capability

        Returns:
            List of parameter names that need to be collected
        """
        parameters = []

        # Common number extraction
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', prompt)

        # Location extraction
        locations = [loc for loc in self.location_keywords if loc in prompt]

        # Based on capability, determine what's needed
        if capability == "calculate_irr":
            if not numbers:
                parameters.extend(["cashFlows", "initialInvestment"])
        elif capability == "calculate_npv":
            if not numbers:
                parameters.extend(["cashFlows", "initialInvestment", "discountRate"])
        elif capability == "optimize_product_mix":
            if not locations:
                parameters.append("location")
            parameters.extend(["totalUnits", "totalArea"])
        elif capability == "get_top_n_projects":
            # Extract N from prompt
            n_match = re.search(r'top\s+(\d+)', prompt)
            if not n_match:
                parameters.append("n")
            if not locations:
                parameters.extend(["region", "city"])
            parameters.append("attribute_path")
        elif capability in ["calculate_statistics", "aggregate_by_region"]:
            if "calculate_statistics" == capability:
                parameters.append("values")
            if not locations:
                parameters.extend(["region", "city"])

        return parameters

    def _needs_vector_search(self, prompt: str) -> bool:
        """
        Determine if the query needs vector search for context

        Args:
            prompt: User prompt

        Returns:
            True if vector search is recommended
        """
        # Keywords that suggest need for contextual information
        context_keywords = [
            "why", "how", "explain", "tell me about", "what is",
            "describe", "insights", "trends", "market", "economy",
            "infrastructure", "demographics", "report", "intelligence"
        ]

        return any(keyword in prompt for keyword in context_keywords)

    def get_capability_info(self, capability: str) -> Dict[str, Any]:
        """
        Get detailed information about a capability

        Args:
            capability: Capability name

        Returns:
            Dictionary with capability details
        """
        if capability not in self.capability_patterns:
            return {"error": f"Unknown capability: {capability}"}

        config = self.capability_patterns[capability]
        return {
            "capability": capability,
            "layer": config["layer"].value,
            "keywords": config.get("keywords", []),
            "requires_vector": config.get("requires_vector", False),
            "description": self._generate_capability_description(capability)
        }

    def _generate_capability_description(self, capability: str) -> str:
        """Generate human-readable description for a capability"""
        descriptions = {
            "calculate_irr": "Calculate Internal Rate of Return for cash flows",
            "calculate_npv": "Calculate Net Present Value of an investment",
            "calculate_statistics": "Perform statistical analysis on data series",
            "optimize_product_mix": "Optimize unit mix to maximize returns",
            "get_market_insights": "Retrieve market intelligence and insights",
            "aggregate_by_region": "Aggregate metrics across a region",
            "get_top_n_projects": "Get top performing projects by metric",
            # Add more as needed
        }
        return descriptions.get(capability, f"Execute {capability.replace('_', ' ')}")

    def list_all_capabilities(self) -> List[Dict[str, Any]]:
        """
        List all available capabilities organized by layer

        Returns:
            List of capability information
        """
        capabilities_by_layer = {}

        for capability, config in self.capability_patterns.items():
            layer = config["layer"].value
            if layer not in capabilities_by_layer:
                capabilities_by_layer[layer] = []

            capabilities_by_layer[layer].append({
                "capability": capability,
                "description": self._generate_capability_description(capability),
                "keywords": config.get("keywords", [])[:5],  # First 5 keywords
                "requires_vector": config.get("requires_vector", False)
            })

        return capabilities_by_layer


# Singleton instance for easy import
prompt_router = PromptRouter()