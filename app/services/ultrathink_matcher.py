"""
UltraThink Matcher - LLM-Assisted Intelligent Query Disambiguation

This service uses LLM reasoning to handle:
- Spelling variations (Shrinivas vs Shriniwas)
- Phonetic similarities (Sara vs Sarah)
- Ambiguous queries
- Format variations

Architecture:
1. Quick fuzzy match (fast path)
2. LLM disambiguation if needed (smart path)
3. Knowledge graph fetch (source of truth)
4. Template-based formatting (consistent output)

The LLM NEVER invents data - it only helps match queries to KG entities.
"""

import os
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import google.generativeai as genai


@dataclass
class DisambiguationResult:
    """Result from LLM disambiguation"""
    attribute: str
    attribute_matched: str
    attribute_confidence: float
    project: Optional[str]
    project_matched: Optional[str]
    project_confidence: float
    template: str
    enrichment_fields: List[str]
    reasoning: str
    raw_response: Dict


class UltraThinkMatcher:
    """
    LLM-assisted intelligent matcher for ambiguous queries

    Uses Gemini to disambiguate when fuzzy matching is uncertain.
    Combines LLM intelligence with KG reliability.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Gemini API"""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def disambiguate(
        self,
        query: str,
        available_attributes: List[str],
        available_projects: List[str],
        fuzzy_attribute_match: Optional[Tuple[str, float]] = None,
        fuzzy_project_match: Optional[Tuple[str, float]] = None
    ) -> DisambiguationResult:
        """
        Use LLM to disambiguate ambiguous queries

        Args:
            query: User's natural language query
            available_attributes: List of known attributes
            available_projects: List of known projects
            fuzzy_attribute_match: Optional fuzzy match result (name, score)
            fuzzy_project_match: Optional fuzzy match result (name, score)

        Returns:
            DisambiguationResult with matched entities and template
        """

        # Build context for LLM
        context = self._build_disambiguation_prompt(
            query,
            available_attributes,
            available_projects,
            fuzzy_attribute_match,
            fuzzy_project_match
        )

        # Call LLM
        response = self.model.generate_content(context)

        # Parse structured output
        try:
            # Extract JSON from response (might be wrapped in markdown)
            response_text = response.text

            # Try to extract JSON if wrapped in code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            result_json = json.loads(response_text)

            return DisambiguationResult(
                attribute=result_json.get("attribute", ""),
                attribute_matched=result_json.get("attribute_matched", ""),
                attribute_confidence=result_json.get("attribute_confidence", 0.0),
                project=result_json.get("project"),
                project_matched=result_json.get("project_matched"),
                project_confidence=result_json.get("project_confidence", 0.0),
                template=result_json.get("template", "{VALUE}"),
                enrichment_fields=result_json.get("enrichment_fields", []),
                reasoning=result_json.get("reasoning", ""),
                raw_response=result_json
            )

        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to fuzzy matches if LLM parsing fails
            return DisambiguationResult(
                attribute=fuzzy_attribute_match[0] if fuzzy_attribute_match else "",
                attribute_matched=fuzzy_attribute_match[0] if fuzzy_attribute_match else "",
                attribute_confidence=fuzzy_attribute_match[1] if fuzzy_attribute_match else 0.0,
                project=fuzzy_project_match[0] if fuzzy_project_match else None,
                project_matched=fuzzy_project_match[0] if fuzzy_project_match else None,
                project_confidence=fuzzy_project_match[1] if fuzzy_project_match else 0.0,
                template="{VALUE}",
                enrichment_fields=[],
                reasoning=f"LLM parsing failed: {e}. Using fuzzy fallback.",
                raw_response={"error": str(e), "raw_text": response.text if response else "No response"}
            )

    def _build_disambiguation_prompt(
        self,
        query: str,
        available_attributes: List[str],
        available_projects: List[str],
        fuzzy_attribute_match: Optional[Tuple[str, float]] = None,
        fuzzy_project_match: Optional[Tuple[str, float]] = None
    ) -> str:
        """Build the prompt for LLM disambiguation"""

        # Limit lists for prompt size
        attributes_sample = available_attributes[:50] if len(available_attributes) > 50 else available_attributes
        projects_sample = available_projects[:20] if len(available_projects) > 20 else available_projects

        prompt = f"""You are a query disambiguation assistant for a real estate knowledge graph.

**User Query:** "{query}"

**Available Attributes (properties that can be queried):**
{', '.join(f'"{attr}"' for attr in attributes_sample)}
{f'... and {len(available_attributes) - 50} more' if len(available_attributes) > 50 else ''}

**Available Projects:**
{', '.join(f'"{proj}"' for proj in projects_sample)}
{f'... and {len(available_projects) - 20} more' if len(available_projects) > 20 else ''}

"""

        if fuzzy_attribute_match:
            prompt += f"""
**Fuzzy Attribute Match:** "{fuzzy_attribute_match[0]}" (confidence: {fuzzy_attribute_match[1]:.2f})
"""

        if fuzzy_project_match:
            prompt += f"""
**Fuzzy Project Match:** "{fuzzy_project_match[0]}" (confidence: {fuzzy_project_match[1]:.2f})
"""

        prompt += """
**Your Task:**
1. Identify which attribute is being asked about (handle spelling variations, abbreviations, units in parentheses)
2. Identify which project (if any) is mentioned (handle spelling variations, newlines, word order)
3. Provide a natural language template for the answer with placeholders
4. List any enrichment fields needed (launch_date, location, developer, etc.)

**Important Matching Rules:**
- "Annual Sales Value" matches "Annual Sales Value (Rs.Cr.)" (units are optional)
- "Pradnyesh Shrinivas" matches "Pradnyesh\\nShriniwas" (newlines = spaces)
- "Shrinivas" sounds like "Shriniwas" (phonetic similarity)
- "Sara" = "Sarah" (spelling variations)
- Be lenient with abbreviations: "PSF" = "Price Per Sqft" = "Price Per Square Foot"

**Response Format (JSON only, no other text):**
```json
{
  "attribute": "user's query term",
  "attribute_matched": "exact match from available attributes",
  "attribute_confidence": 0.0-1.0,
  "project": "user's query term (or null if not a project-specific query)",
  "project_matched": "exact match from available projects (or null)",
  "project_confidence": 0.0-1.0,
  "template": "The {attribute} of {project} in {location} is {VALUE}",
  "enrichment_fields": ["location", "developer", "launch_date"],
  "reasoning": "Brief explanation of matching logic used"
}
```

**Examples:**

Query: "What is the Annual Sales Value of Pradnyesh Shrinivas?"
Available attributes: ["Project Size", "Annual Sales Value (Rs.Cr.)", "Sold %", ...]
Available projects: ["Sara City", "Pradnyesh\\nShriniwas", ...]

Response:
```json
{
  "attribute": "Annual Sales Value",
  "attribute_matched": "Annual Sales Value (Rs.Cr.)",
  "attribute_confidence": 0.98,
  "project": "Pradnyesh Shrinivas",
  "project_matched": "Pradnyesh\\nShriniwas",
  "project_confidence": 0.92,
  "template": "The {attribute} of {project} in {location} is {VALUE}",
  "enrichment_fields": ["location", "developer"],
  "reasoning": "Exact attribute match with unit specification. Project name matched with newline normalization and phonetic similarity on 'Shrinivas/Shriniwas'."
}
```

Now disambiguate the user's query above. Return ONLY valid JSON, no extra text.
"""

        return prompt

    def should_use_ultrathink(
        self,
        fuzzy_attribute_score: float,
        fuzzy_project_score: float,
        threshold: float = 0.7
    ) -> bool:
        """
        Decide if we should use UltraThink or trust fuzzy matching

        Args:
            fuzzy_attribute_score: Confidence of fuzzy attribute match
            fuzzy_project_score: Confidence of fuzzy project match
            threshold: Minimum confidence to skip UltraThink

        Returns:
            True if UltraThink should be used, False if fuzzy is good enough
        """
        # Use UltraThink if either score is below threshold
        if fuzzy_attribute_score < threshold or fuzzy_project_score < threshold:
            return True

        # Also use UltraThink if scores are moderately low (ambiguous)
        avg_score = (fuzzy_attribute_score + fuzzy_project_score) / 2
        if avg_score < 0.8:
            return True

        return False


# Global instance
_ultrathink_matcher = None

def get_ultrathink_matcher() -> UltraThinkMatcher:
    """Get or create global UltraThink matcher instance"""
    global _ultrathink_matcher
    if _ultrathink_matcher is None:
        _ultrathink_matcher = UltraThinkMatcher()
    return _ultrathink_matcher
