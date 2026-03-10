"""
Enriched Layers Service

Loads and manages the enriched layers knowledge base (67 attributes from Excel).
Provides dynamic access to Layer 0 and Layer 1 attribute definitions, formulas,
and prompt patterns for query routing.

Source: change-request/enriched-layers/enriched_layers_knowledge.json
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class EnrichedAttribute:
    """Represents a single attribute from enriched layers"""
    id: str
    layer: str
    target_attribute: str
    unit: str
    dimension: str
    description: str
    sample_prompt: str
    variation_in_prompt: str
    assumption_in_prompt: str
    formula_derivation: str
    sample_values: str
    expected_answer: str
    is_atomic: bool
    requires_calculation: bool


class EnrichedLayersService:
    """
    Service for managing enriched layers knowledge base

    Responsibilities:
    1. Load enriched layers from JSON
    2. Provide attribute lookup by name/prompt
    3. Generate capability patterns for prompt_router
    4. Execute Layer 1 calculations
    """

    def __init__(self, json_path: Optional[str] = None):
        """
        Initialize service and load enriched layers

        Args:
            json_path: Path to enriched_layers_knowledge.json
                      If None, uses default location
        """
        if json_path is None:
            # Default path relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            json_path = os.path.join(
                project_root,
                "change-request",
                "enriched-layers",
                "enriched_layers_knowledge.json"
            )

        self.json_path = json_path
        self.knowledge = self._load_knowledge()

        # Build indexes for fast lookup
        self.layer0_by_name = {}
        self.layer1_by_name = {}
        self.all_attributes_by_name = {}

        self._build_indexes()

    def _load_knowledge(self) -> Dict:
        """Load knowledge base from JSON file"""
        try:
            with open(self.json_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Enriched layers file not found at {self.json_path}")
            return {
                "metadata": {},
                "layer0_attributes": [],
                "layer1_attributes": []
            }
        except json.JSONDecodeError as e:
            print(f"Error parsing enriched layers JSON: {e}")
            return {
                "metadata": {},
                "layer0_attributes": [],
                "layer1_attributes": []
            }

    def _build_indexes(self):
        """Build fast lookup indexes"""
        # Index Layer 0 attributes
        for attr_data in self.knowledge.get("layer0_attributes", []):
            attr = EnrichedAttribute(**attr_data)
            self.layer0_by_name[attr.target_attribute.lower()] = attr
            self.all_attributes_by_name[attr.target_attribute.lower()] = attr

        # Index Layer 1 attributes
        for attr_data in self.knowledge.get("layer1_attributes", []):
            attr = EnrichedAttribute(**attr_data)
            self.layer1_by_name[attr.target_attribute.lower()] = attr
            self.all_attributes_by_name[attr.target_attribute.lower()] = attr

    def get_attribute(self, name: str) -> Optional[EnrichedAttribute]:
        """Get attribute by name (case-insensitive)"""
        return self.all_attributes_by_name.get(name.lower())

    def get_layer1_attributes(self) -> List[EnrichedAttribute]:
        """Get all Layer 1 attributes"""
        return list(self.layer1_by_name.values())

    def get_layer0_attributes(self) -> List[EnrichedAttribute]:
        """Get all Layer 0 attributes"""
        return list(self.layer0_by_name.values())

    def get_all_attributes(self) -> List[EnrichedAttribute]:
        """Get all attributes (Layer 0 + Layer 1)"""
        return list(self.all_attributes_by_name.values())

    def search_by_prompt(self, query: str) -> Optional[Tuple[EnrichedAttribute, float]]:
        """
        Search for attribute matching a user query

        Args:
            query: User's natural language query

        Returns:
            Tuple of (EnrichedAttribute, confidence_score) if match found
            None if no match
        """
        query_lower = query.lower()
        best_match = None
        best_score = 0.0

        for attr in self.all_attributes_by_name.values():
            score = self._calculate_prompt_match_score(query_lower, attr)

            if score > best_score:
                best_score = score
                best_match = attr

        # Return match if confidence is above threshold
        if best_match and best_score > 0.3:
            return (best_match, best_score)

        return None

    def _calculate_prompt_match_score(self, query: str, attr: EnrichedAttribute) -> float:
        """Calculate how well a query matches an attribute's prompts"""
        score = 0.0

        # Check target attribute name (exact match gets high score)
        if attr.target_attribute.lower() in query:
            score += 0.5

        # Check sample prompt
        sample_prompt_lower = attr.sample_prompt.lower()
        if query in sample_prompt_lower or sample_prompt_lower in query:
            score += 0.3

        # Check prompt variations (split by | and ;)
        variations = re.split(r'[|;]', attr.variation_in_prompt)
        for variation in variations:
            variation = variation.strip().lower()
            if variation and (query in variation or variation in query):
                score += 0.2
                break

        # Check keywords from attribute name
        attr_keywords = set(attr.target_attribute.lower().split())
        query_keywords = set(query.split())
        keyword_overlap = len(attr_keywords & query_keywords)
        if keyword_overlap > 0:
            score += 0.2 * (keyword_overlap / len(attr_keywords))

        return min(score, 1.0)  # Cap at 1.0

    def generate_capability_patterns(self) -> Dict[str, Dict]:
        """
        Generate capability patterns for prompt_router

        Returns:
            Dictionary of capability patterns compatible with PromptRouter format
        """
        patterns = {}

        for attr in self.layer1_by_name.values():
            # Create capability name (snake_case)
            capability_name = f"calculate_{attr.target_attribute.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('%', 'percent')}"

            # Extract keywords from attribute name and prompts
            keywords = self._extract_keywords(attr)

            # Generate regex patterns
            regex_patterns = self._generate_regex_patterns(attr)

            # Determine layer (Layer 1 for all enriched attributes)
            layer_num = 1

            patterns[capability_name] = {
                "keywords": keywords,
                "patterns": regex_patterns,
                "layer": layer_num,  # Will need to convert to LayerType enum
                "enriched_attribute": attr.target_attribute,
                "formula": attr.formula_derivation,
                "unit": attr.unit,
                "dimension": attr.dimension
            }

        return patterns

    def _extract_keywords(self, attr: EnrichedAttribute) -> List[str]:
        """Extract keywords from attribute for matching"""
        keywords = set()

        # Add words from attribute name (most important)
        attr_words = attr.target_attribute.lower().replace('(', '').replace(')', '').replace('%', 'percent').split()
        # Filter out very common words
        stop_words = {'of', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'per'}
        attr_words = [w for w in attr_words if w not in stop_words]
        keywords.update(attr_words)

        # Add time-related keywords for time-based metrics
        attr_lower = attr.target_attribute.lower()
        if any(time_word in attr_lower for time_word in ['time', 'months', 'years', 'period', 'duration']):
            keywords.update(['long', 'time', 'duration'])

        # Add only most specific words from variations (not full text)
        # Extract key action/concept words
        variations = re.split(r'[|;]', attr.variation_in_prompt)
        for variation in variations[:2]:  # Only first 2 variations
            variation = variation.strip().lower()
            # Clean punctuation
            variation = re.sub(r'[?.!,]', '', variation)
            # Extract specific keywords (nouns, adjectives)
            specific_words = []
            for word in variation.split():
                # Skip common question words and articles
                if len(word) > 4 and word not in {
                    'what', 'the', 'for', 'this', 'show', 'give', 'tell',
                    'how', 'many', 'much', 'will', 'take', 'does', 'about'
                }:
                    specific_words.append(word)
            keywords.update(specific_words[:3])  # Max 3 words per variation

        return list(keywords)[:10]  # Limit total keywords to 10

    def _generate_regex_patterns(self, attr: EnrichedAttribute) -> List[str]:
        """Generate regex patterns for attribute matching"""
        patterns = []

        # Pattern 1: Attribute name itself
        attr_name_normalized = attr.target_attribute.lower().replace('(', '').replace(')', '').replace('%', 'percent')
        patterns.append(rf"\b{re.escape(attr_name_normalized)}\b")

        # Pattern 2: Key words from attribute name
        words = attr_name_normalized.split()
        if len(words) >= 2:
            patterns.append(r"\s+".join([re.escape(w) for w in words]))

        # Pattern 2b: Core concept without unit (for attributes like "Project Age (Months)")
        # Remove common unit words to match queries like "project age" without "months"
        unit_words = {'months', 'years', 'units', 'percent', 'cr', 'lakh', 'sqft', 'acres'}
        core_words = [w for w in words if w not in unit_words]
        if len(core_words) >= 2 and core_words != words:
            # Add pattern for core concept (e.g., "project.*age" instead of "project.*age.*months")
            patterns.append(r".*".join([re.escape(w) for w in core_words]))
            # Also add simpler consecutive pattern
            patterns.append(r"\s+".join([re.escape(w) for w in core_words]))

        # Pattern 3: Special patterns for common attributes
        attr_lower = attr.target_attribute.lower()

        # Months of Inventory specific patterns
        if 'months of inventory' in attr_lower:
            patterns.extend([
                r"how\s+long.*sell.*remaining",
                r"how\s+long.*sell.*unsold",
                r"time.*sell.*remaining",
                r"months.*remain",
                r"inventory.*months"
            ])

        # Sellout Time specific patterns
        elif 'sellout time' in attr_lower:
            patterns.extend([
                r"sellout.*time",
                r"time.*sellout",
                r"how\s+long.*sell\s+all",
                r"time.*complete.*sales",
                r"sellout.*period"
            ])

        # Price Growth specific patterns
        elif 'price growth' in attr_lower:
            patterns.extend([
                r"price.*growth",
                r"price.*increase",
                r"appreciation",
                r"growth.*price"
            ])

        # Time to Possession specific patterns
        elif 'time to possession' in attr_lower or 'possession' in attr_lower:
            patterns.extend([
                r"months.*until.*possession",
                r"months.*to.*possession",
                r"time.*to.*possession",
                r"time.*until.*possession",
                r"when.*possession",
                r"how.*long.*until.*possession",
                r"possession.*date"
            ])

        # Pattern 4: Extract key phrases from variations
        variations = re.split(r'[|;]', attr.variation_in_prompt)
        for i, variation in enumerate(variations[:3]):  # First 3 variations
            variation = variation.strip().lower()
            if variation:
                # Extract main question structure
                if '?' in variation:
                    variation = variation.split('?')[0].strip()

                # Create simple pattern
                key_words = [w for w in variation.split() if len(w) > 3 and w not in {
                    'what', 'the', 'for', 'this', 'show', 'give', 'me', 'is', 'are', 'can', 'you', 'tell'
                }]
                if key_words:
                    patterns.append(r".*".join([re.escape(w) for w in key_words[:3]]))

        return patterns[:8]  # Limit to 8 patterns per attribute

    def execute_layer1_calculation(self, attr_name: str, project_data: Dict) -> Optional[Dict]:
        """
        Execute a Layer 1 calculation for a specific project

        Args:
            attr_name: Name of the attribute to calculate
            project_data: Dictionary with project's Layer 0 data

        Returns:
            Calculation result with value, unit, formula, etc.
            None if calculation fails
        """
        attr = self.get_attribute(attr_name)

        if not attr or attr.layer != "L1":
            return None

        # Parse formula and execute
        try:
            result = self._parse_and_execute_formula(
                attr.formula_derivation,
                project_data,
                attr
            )

            return {
                "attribute": attr.target_attribute,
                "value": result,
                "unit": attr.unit,
                "dimension": attr.dimension,
                "formula": attr.formula_derivation,
                "layer": 1
            }

        except Exception as e:
            print(f"Error calculating {attr_name}: {e}")
            return None

    def _parse_and_execute_formula(self, formula: str, data: Dict, attr: EnrichedAttribute) -> float:
        """
        Parse and execute a Layer 1 formula

        Examples:
        - "Supply / Annual Sales" → data['supply'] / data['annual_sales']
        - "Unsold × Size × PSF / 1e7" → data['unsold'] * data['size'] * data['psf'] / 1e7
        """
        # Normalize formula
        formula_lower = formula.lower()

        # Handle specific formulas based on attribute name
        attr_name_lower = attr.target_attribute.lower()

        # SELLOUT TIME
        if 'sellout time' in attr_name_lower:
            supply = data.get('supply') or data.get('totalUnits') or 0
            annual_sales = data.get('annual_sales') or data.get('annualSales') or 1
            return supply / annual_sales if annual_sales > 0 else 0

        # MONTHS OF INVENTORY
        elif 'months of inventory' in attr_name_lower or 'moi' in attr_name_lower:
            unsold = data.get('unsold') or data.get('unsoldUnits') or 0
            monthly_sold = data.get('monthly_units_sold') or data.get('monthlySales') or 1
            return unsold / monthly_sold if monthly_sold > 0 else 0

        # MONTHLY UNITS SOLD
        elif 'monthly units sold' in attr_name_lower:
            annual_sales = data.get('annual_sales') or data.get('annualSales') or 0
            return annual_sales / 12

        # UNSOLD UNITS
        elif 'unsold units' in attr_name_lower:
            supply = data.get('supply') or data.get('totalUnits') or 0
            unsold_percent = data.get('unsold_percent') or data.get('unsoldPercent') or 0
            return supply * (unsold_percent / 100)

        # SOLD UNITS
        elif 'sold units' in attr_name_lower and 'monthly' not in attr_name_lower:
            supply = data.get('supply') or data.get('totalUnits') or 0
            sold_percent = data.get('sold_percent') or data.get('soldPercent') or 0
            return supply * (sold_percent / 100)

        # PRICE GROWTH RATE (% per Year) - CHECK THIS FIRST (more specific than "price growth")
        elif 'price growth rate' in attr_name_lower or ('price growth' in attr_name_lower and 'year' in attr_name_lower):
            current_psf = data.get('current_psf') or data.get('currentPSF') or 0
            launch_psf = data.get('launch_psf') or data.get('launchPSF') or 0

            # Get project age in months
            from datetime import datetime
            from dateutil import parser as date_parser

            launch_date_str = data.get('launchDate') or data.get('launch_date') or ""
            if launch_date_str and launch_psf > 0 and current_psf > launch_psf:
                try:
                    # Calculate project age in years
                    launch_date = date_parser.parse(launch_date_str)
                    current_date = datetime.now()
                    months_difference = ((current_date.year - launch_date.year) * 12
                                        + (current_date.month - launch_date.month))
                    years = months_difference / 12

                    if years > 0:
                        # Annual growth rate: ((Current PSF - Launch PSF) / Launch PSF) / Years * 100
                        total_growth_pct = ((current_psf - launch_psf) / launch_psf) * 100
                        annual_growth_rate = total_growth_pct / years
                        return annual_growth_rate
                except Exception as e:
                    print(f"Error calculating price growth rate: {e}")

            return 0

        # PRICE GROWTH (%) - Total price appreciation percentage
        elif 'price growth' in attr_name_lower:
            current_psf = data.get('current_psf') or data.get('currentPSF') or 0
            launch_psf = data.get('launch_psf') or data.get('launchPSF') or 0

            if launch_psf > 0:
                # Total growth percentage: ((Current PSF - Launch PSF) / Launch PSF) * 100
                return ((current_psf - launch_psf) / launch_psf) * 100

            return 0

        # REALIZED PSF
        elif 'realised psf' in attr_name_lower or 'realized psf' in attr_name_lower:
            value_cr = data.get('value') or data.get('totalRevenue') or 0
            units = data.get('units') or data.get('soldUnits') or 1
            size = data.get('size') or data.get('avgUnitSize') or 1
            return (value_cr * 1e7) / (units * size) if (units * size) > 0 else 0

        # REVENUE PER UNIT
        elif 'revenue per unit' in attr_name_lower:
            value_cr = data.get('value') or data.get('totalRevenue') or 0
            units = data.get('units') or data.get('soldUnits') or 1
            return (value_cr * 1e7) / units / 1e5 if units > 0 else 0  # Convert to lakh

        # ANNUAL CLEARANCE RATE
        elif 'clearance rate' in attr_name_lower or 'annual clearance' in attr_name_lower:
            annual_sales = data.get('annual_sales') or data.get('annualSales') or 0
            supply = data.get('supply') or data.get('totalUnits') or 1
            return (annual_sales / supply) * 100 if supply > 0 else 0

        # ABSORPTION RATE
        elif 'absorption rate' in attr_name_lower or 'absorption' in attr_name_lower:
            # Formula: (Sold Units / Total Supply) / Duration Months × 100
            sold_units = data.get('sold_units') or data.get('soldUnits') or 0
            supply = data.get('supply') or data.get('totalUnits') or 1
            duration_months = data.get('duration_months') or data.get('durationMonths') or data.get('project_age_months') or 1

            if supply > 0 and duration_months > 0:
                return ((sold_units / supply) / duration_months) * 100
            return 0

        # PSF GAP
        elif 'psf gap' in attr_name_lower:
            current_psf = data.get('current_psf') or data.get('currentPSF') or 0
            launch_psf = data.get('launch_psf') or data.get('launchPSF') or 0
            return current_psf - launch_psf

        # AVERAGE TICKET SIZE
        elif 'average ticket size' in attr_name_lower or 'ticket size' in attr_name_lower:
            size = data.get('size') or data.get('avgUnitSize') or 0
            current_psf = data.get('current_psf') or data.get('currentPSF') or 0
            return (size * current_psf) / 1e5  # Convert to lakh

        # UNSOLD INVENTORY VALUE
        elif 'unsold inventory value' in attr_name_lower:
            unsold = data.get('unsold') or data.get('unsoldUnits') or 0
            size = data.get('size') or data.get('avgUnitSize') or 0
            psf = data.get('current_psf') or data.get('currentPSF') or 0
            return (unsold * size * psf) / 1e7  # Convert to Cr

        # PROJECT AGE (MONTHS)
        elif 'project age' in attr_name_lower:
            from datetime import datetime
            from dateutil import parser as date_parser

            launch_date_str = data.get('launchDate') or data.get('launch_date') or ""
            if launch_date_str:
                try:
                    # Parse launch date (handles "Nov 2007", "Apr 2023" etc.)
                    launch_date = date_parser.parse(launch_date_str)
                    current_date = datetime.now()

                    # Calculate months difference
                    months_difference = ((current_date.year - launch_date.year) * 12
                                        + (current_date.month - launch_date.month))
                    return months_difference
                except Exception as e:
                    print(f"Error parsing launch date '{launch_date_str}': {e}")
                    return 0
            return 0

        # TIME TO POSSESSION (MONTHS)
        elif 'time to possession' in attr_name_lower or 'months until possession' in attr_name_lower or 'months to possession' in attr_name_lower:
            from datetime import datetime
            from dateutil import parser as date_parser

            possession_date_str = data.get('possessionDate') or data.get('possession_date') or ""
            if possession_date_str:
                try:
                    # Parse possession date
                    possession_date = date_parser.parse(possession_date_str)
                    current_date = datetime.now()

                    # Calculate months until possession (can be negative if overdue)
                    months_until = ((possession_date.year - current_date.year) * 12
                                   + (possession_date.month - current_date.month))
                    return months_until
                except Exception as e:
                    print(f"Error parsing possession date '{possession_date_str}': {e}")
                    return 0
            return 0

        # MONTHS TO SELL REMAINING
        elif 'months to sell remaining' in attr_name_lower or 'remaining sellout time' in attr_name_lower:
            unsold = data.get('unsold') or data.get('unsoldUnits') or 0
            monthly_units_sold = data.get('monthly_units_sold') or data.get('monthlyUnitsSold') or 0

            # Calculate from monthly velocity if available
            if monthly_units_sold == 0:
                annual_sales = data.get('annual_sales') or data.get('annualSales') or 0
                if annual_sales > 0:
                    monthly_units_sold = annual_sales / 12

            if monthly_units_sold > 0:
                return unsold / monthly_units_sold
            return 0

        # Default: Try to evaluate simple formulas
        else:
            # This is a fallback - try to parse simple arithmetic
            # Replace common terms with data keys
            formula_eval = formula_lower
            for key in data.keys():
                formula_eval = formula_eval.replace(key.lower(), f"data['{key}']")

            try:
                return eval(formula_eval, {"data": data, "__builtins__": {}})
            except:
                return 0.0


# Global instance
_enriched_layers_service = None


def get_enriched_layers_service() -> EnrichedLayersService:
    """Get global enriched layers service instance"""
    global _enriched_layers_service
    if _enriched_layers_service is None:
        _enriched_layers_service = EnrichedLayersService()
    return _enriched_layers_service
