"""
Capability-Specific Configurations

Defines rendering configurations for each API capability endpoint.
"""

from typing import Dict, Any

# =============================================================================
# CAPABILITY CONFIGURATIONS
# =============================================================================

CAPABILITY_CONFIGS: Dict[str, Dict[str, Any]] = {
    # Layer 2: Financial Calculations
    "calculate_irr": {
        "title": "💎 Internal Rate of Return (IRR)",
        "description": "IRR is the discount rate where NPV = 0",
        "target_range": (20, 28),  # 20-28% IRR target for real estate
        "show_formula": True,
        "show_provenance": True,
        "show_calculation_steps": True,  # Show chain of thought
        "status_thresholds": {
            "excellent": 20,
            "good": 15,
            "moderate": 10
        }
    },

    "calculate_npv": {
        "title": "💰 Net Present Value (NPV)",
        "description": "Present value of future cash flows minus initial investment",
        "show_formula": True,
        "show_provenance": True,
        "show_calculation_steps": True  # Show chain of thought
    },

    "calculate_payback_period": {
        "title": "⏰ Payback Period",
        "description": "Time required to recover initial investment",
        "show_formula": True,
        "show_provenance": True
    },

    "calculate_profitability_index": {
        "title": "🎯 Profitability Index",
        "description": "Ratio of payoff to investment (PI > 1 means profitable)",
        "threshold": 1.0,
        "show_formula": True
    },

    "calculate_sensitivity_analysis": {
        "title": "🎭 Sensitivity Analysis",
        "description": "IRR/NPV under different absorption & price scenarios",
        "layout": "three_column",
        "color_coding": {
            "baseCase": "neutral",
            "optimisticCase": "success",
            "stressCase": "warning"
        },
        "scenario_icons": {
            "baseCase": "🎲",
            "optimisticCase": "🔥",
            "stressCase": "⚡",
            "conservative": "🛡️"
        },
        "show_delta": True,
        "show_calculation_steps": True  # Show chain of thought
    },

    # Layer 3: Optimization
    "optimize_product_mix": {
        "title": "🎰 Product Mix Optimization",
        "description": "Optimal unit distribution to maximize IRR",
        "show_scenarios": True,
        "scenario_layout": "expandable",
        "algorithm_info": True,
        "show_calculation_steps": True  # Show chain of thought
    },

    "market_opportunity_scoring": {
        "title": "🌟 Market Opportunity Assessment",
        "description": "OPPS score and recommended unit mix for location",
        "score_thresholds": {
            "high": 75,
            "medium": 50,
            "low": 0
        },
        "score_icons": {
            "high": "🏆",
            "medium": "⭐",
            "low": "💡"
        }
    },

    # Layer 4: Market Insights & Context
    "get_market_insights": {
        "title": "🏙️ Market Insights & Context",
        "description": "RAG-based market intelligence using city reports",
        "show_calculation_steps": True,
        "section_icons": {
            "city_overview": "🌆",
            "locality_insights": "📍",
            "price_context": "💰",
            "infrastructure": "🏗️",
            "future_outlook": "🔮",
            "positioning": "🎯"
        },
        "color_scheme": {
            "gradient": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            "border": "#f5576c"
        }
    },

    "enrich_irr_calculation": {
        "title": "💎 IRR with Market Context",
        "description": "Financial returns enriched with market intelligence",
        "show_calculation_steps": True,
        "enrichment_icons": {
            "city_context": "🌆",
            "locality_context": "📍",
            "comparable_projects": "🏢",
            "market_positioning": "🎯"
        },
        "color_scheme": {
            "gradient": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
            "border": "#fa709a"
        }
    },

    "semantic_search": {
        "title": "🔍 Semantic Search",
        "description": "AI-powered search across city market reports",
        "show_calculation_steps": False,
        "result_icons": {
            "executive_summary": "📊",
            "data_table": "📈",
            "regional_analysis": "🗺️",
            "social_infrastructure": "🏗️",
            "future_outlook": "🔮",
            "general": "📄"
        },
        "color_scheme": {
            "gradient": "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
            "border": "#a8edea"
        }
    },

    # Layer 1: Basic Metrics
    "calculate_psf": {
        "title": "📐 Price Per Square Foot (PSF)",
        "description": "Average price per saleable square foot",
        "show_formula": True
    },

    "calculate_asp": {
        "title": "💵 Average Selling Price (ASP)",
        "description": "Average price per unit",
        "show_formula": True
    },

    "calculate_absorption_rate": {
        "title": "🎪 Absorption Rate",
        "description": "Rate at which units are sold",
        "show_formula": True
    }
}


def get_capability_config(capability: str) -> Dict[str, Any]:
    """
    Get configuration for a capability
    
    Args:
        capability: Capability name
    
    Returns:
        Configuration dictionary (or default if not found)
    """
    default_config = {
        "title": f"📋 {capability.replace('_', ' ').title()}",
        "description": "",
        "show_formula": False,
        "show_provenance": True
    }
    
    return CAPABILITY_CONFIGS.get(capability, default_config)
