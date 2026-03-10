"""
Formula Adapter - Wraps dynamic_formula_service to implement ports

This adapter makes dynamic_formula_service compatible with the hexagonal
architecture by implementing the port interfaces.
"""

from typing import Dict, List, Optional, Any
from app.ports.input_ports import QueryAttributePort, CalculateFormulaPort
from app.ports.output_ports import FormulaRepositoryPort
from app.services.dynamic_formula_service import get_dynamic_formula_service


class FormulaServiceAdapter(QueryAttributePort, CalculateFormulaPort, FormulaRepositoryPort):
    """
    Adapter that wraps dynamic_formula_service to implement multiple ports

    Implements:
    - QueryAttributePort (input port for querying attributes)
    - CalculateFormulaPort (input port for calculations)
    - FormulaRepositoryPort (output port for formula storage)
    """

    def __init__(self):
        self.service = get_dynamic_formula_service()

    # QueryAttributePort implementation
    def get_attribute(self, attribute_name: str) -> Optional[Dict]:
        """Get attribute definition by name"""
        attr = self.service.get_attribute(attribute_name)
        if attr:
            return {
                'name': attr.target_attribute,
                'layer': attr.layer,
                'unit': attr.unit,
                'dimension': attr.dimension,
                'description': attr.description,
                'formula': attr.formula_derivation,
                'requires_calculation': attr.requires_calculation,
                'sample_prompt': attr.sample_prompt,
            }
        return None

    def search_attributes(self, query: str) -> List[Dict]:
        """Search attributes by natural language query"""
        result = self.service.search_attribute(query)
        if result:
            attr, confidence = result
            return [{
                'name': attr.target_attribute,
                'layer': attr.layer,
                'unit': attr.unit,
                'dimension': attr.dimension,
                'formula': attr.formula_derivation,
                'confidence': confidence,
                'requires_calculation': attr.requires_calculation,
            }]
        return []

    def list_all_attributes(self, layer: Optional[str] = None) -> List[Dict]:
        """List all available attributes, optionally filtered by layer"""
        all_attrs = self.service.list_all_attributes()

        if layer:
            return [attr for attr in all_attrs if attr['layer'] == layer]

        return all_attrs

    # CalculateFormulaPort implementation
    def calculate(
        self,
        attribute_name: str,
        project_data: Dict[str, Any]
    ) -> Optional[Dict]:
        """Calculate an attribute using its formula"""
        attr = self.service.get_attribute(attribute_name)
        if not attr:
            return None

        if not attr.requires_calculation:
            # Direct extraction - return field from project_data
            # Try multiple field name variations for flexible matching
            attr_normalized = attribute_name.lower().replace(' ', '').replace('(', '').replace(')', '')

            # Handle percentage naming variations
            attr_pct = attr_normalized.replace('%', 'pct')
            attr_percent = attr_normalized.replace('%', 'percent')
            attr_percentage = attr_normalized.replace('%', 'percentage')

            # Try different field name patterns
            field_name_candidates = [
                attr_normalized,  # projectsize
                attribute_name.replace(' ', ''),  # ProjectSize (preserve case)
                attr_normalized + 'units',  # projectsizeunits
                attr_normalized[0].lower() + attribute_name.replace(' ', '')[1:] + 'Units',  # projectSizeUnits (camelCase with Units)
                attr_pct,  # sold% → soldpct
                attr_percent,  # sold% → soldpercent
                attr_percentage,  # sold% → soldpercentage
            ]

            # Also try case-insensitive fuzzy match on all keys
            value = None
            matched_field = None
            for key in project_data.keys():
                key_normalized = key.lower().replace('_', '').replace('-', '').replace('(', '').replace(')', '')
                if (key_normalized == attr_normalized or
                    key_normalized == attr_normalized + 'units' or
                    key_normalized == attr_pct or
                    key_normalized == attr_percent or
                    key_normalized == attr_percentage):
                    value = project_data[key]
                    matched_field = key
                    break

            # If still not found, try the candidate list
            if value is None:
                for candidate in field_name_candidates:
                    if candidate in project_data:
                        value = project_data[candidate]
                        matched_field = candidate
                        break

            if value is not None:
                # Handle nested dict format
                if isinstance(value, dict):
                    value = value.get('value')

                return {
                    'attribute': attr.target_attribute,
                    'value': value,
                    'unit': attr.unit,
                    'dimension': attr.dimension,
                    'formula': 'Direct extraction',
                    'layer': attr.layer,
                    'matched_field': matched_field  # For debugging
                }
            return None

        # Requires calculation
        return self.service.execute_formula(attr, project_data)

    def batch_calculate(
        self,
        attribute_names: List[str],
        project_data: Dict[str, Any]
    ) -> Dict[str, Optional[Dict]]:
        """Calculate multiple attributes at once"""
        results = {}
        for attr_name in attribute_names:
            results[attr_name] = self.calculate(attr_name, project_data)
        return results

    # FormulaRepositoryPort implementation
    def find_by_name(self, attribute_name: str) -> Optional[Dict]:
        """Find attribute definition by name"""
        return self.get_attribute(attribute_name)

    def find_all(self) -> List[Dict]:
        """Get all attribute definitions"""
        return self.list_all_attributes()

    def find_by_layer(self, layer: str) -> List[Dict]:
        """Find attributes by layer"""
        return self.list_all_attributes(layer=layer)
