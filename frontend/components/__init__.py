"""
Dynamic Widget Derivation System for Liases Foras Real Estate Analytics

This package provides a modular system for automatically generating Streamlit widgets
based on JSON response structures from the backend API.

Components:
- formatters: Value formatting utilities (currency, percentages, units)
- styles: CSS constants and styling definitions
- schema_analyzer: JSON structure detection and analysis
- pattern_matcher: Pattern detection and matching logic
- widget_templates: Reusable widget template classes
- capability_config: Per-capability configurations and overrides
- dynamic_renderer: Main orchestrator for dynamic widget rendering
"""

__all__ = ["DynamicRenderer"]
