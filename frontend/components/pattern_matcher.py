"""
Pattern Matcher for Dynamic Widget System

Matches JSON patterns to appropriate widget templates.
"""

from typing import List, Type
from components.schema_analyzer import StructureMetadata
from components.widget_templates import (
    WidgetTemplate,
    SingleMetricTemplate,
    KeyValuePanelTemplate,
    ScenarioComparisonTemplate,
    OptimizationResultTemplate,
    MarketScoringTemplate,
    FallbackTemplate
)


class PatternMatcher:
    """Matches JSON patterns to widget templates"""
    
    # Template priority order (higher priority first)
    TEMPLATES: List[Type[WidgetTemplate]] = [
        ScenarioComparisonTemplate,  # Most specific
        OptimizationResultTemplate,
        MarketScoringTemplate,
        SingleMetricTemplate,
        KeyValuePanelTemplate,       # Generic
        FallbackTemplate             # Always matches (last resort)
    ]
    
    def match(self, data: dict, metadata: StructureMetadata) -> WidgetTemplate:
        """
        Match data to the best widget template
        
        Args:
            data: JSON data to render
            metadata: Structure metadata from SchemaAnalyzer
        
        Returns:
            Instance of matching WidgetTemplate
        """
        for template_class in self.TEMPLATES:
            template = template_class()
            if template.can_render(data, metadata):
                return template
        
        # Fallback (should never reach here since FallbackTemplate always matches)
        return FallbackTemplate()
    
    def match_all(self, data: dict, metadata: StructureMetadata) -> List[WidgetTemplate]:
        """
        Get all templates that can render the data
        
        Args:
            data: JSON data
            metadata: Structure metadata
        
        Returns:
            List of matching template instances
        """
        matching_templates = []
        for template_class in self.TEMPLATES:
            template = template_class()
            if template.can_render(data, metadata):
                matching_templates.append(template)
        
        return matching_templates
