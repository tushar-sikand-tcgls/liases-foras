"""
UltraThink Agent - LLM-Driven Query Resolution

Philosophy:
- Let LLM make ALL decisions (routing, matching, formatting)
- Minimal code-based control flow
- LLM steers the conversation and decides next steps
- Code only executes LLM's instructions

The LLM is the BRAIN. Code is just the EXECUTOR.
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import google.generativeai as genai


@dataclass
class UltraThinkDecision:
    """LLM's decision on how to proceed"""
    action: str  # "fetch_and_answer", "need_clarification", "error"
    attribute: Optional[str]
    project: Optional[str]
    response_template: str
    kg_fields_needed: List[str]
    confidence: float
    reasoning: str
    raw_response: Dict


class UltraThinkAgent:
    """
    LLM-driven agent for intelligent query resolution

    The LLM decides:
    1. What is being asked?
    2. What data do I need from KG?
    3. How should I format the answer?
    4. Should I ask for clarification?
    5. What's the next step?

    Code only:
    - Fetches from KG when LLM says "fetch X"
    - Fills templates when LLM says "fill template with Y"
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Gemini"""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',  # Use latest model like other services
            generation_config={"response_mime_type": "application/json"}
        )

    def think(
        self,
        query: str,
        available_attributes: List[str],
        available_projects: List[str],
        kg_sample_data: Optional[Dict] = None
    ) -> UltraThinkDecision:
        """
        Let LLM think about the query and decide what to do

        Args:
            query: User's question
            available_attributes: List of known attributes
            available_projects: List of known projects
            kg_sample_data: Optional sample to help LLM understand data structure

        Returns:
            LLM's decision on what to do next
        """

        prompt = self._build_thinking_prompt(
            query,
            available_attributes,
            available_projects,
            kg_sample_data
        )

        # Let LLM think and decide
        response = self.model.generate_content(prompt)

        # Parse LLM's decision
        try:
            decision_json = json.loads(response.text)

            return UltraThinkDecision(
                action=decision_json.get("action", "error"),
                attribute=decision_json.get("attribute"),
                project=decision_json.get("project"),
                response_template=decision_json.get("response_template", "{VALUE}"),
                kg_fields_needed=decision_json.get("kg_fields_needed", []),
                confidence=decision_json.get("confidence", 0.0),
                reasoning=decision_json.get("reasoning", ""),
                raw_response=decision_json
            )

        except json.JSONDecodeError as e:
            return UltraThinkDecision(
                action="error",
                attribute=None,
                project=None,
                response_template="Error: Could not parse LLM response",
                kg_fields_needed=[],
                confidence=0.0,
                reasoning=f"JSON parse error: {e}",
                raw_response={"error": str(e), "text": response.text}
            )

    def _build_thinking_prompt(
        self,
        query: str,
        available_attributes: List[str],
        available_projects: List[str],
        kg_sample_data: Optional[Dict] = None
    ) -> str:
        """Build prompt that lets LLM think and decide"""

        # Sample a subset to keep prompt manageable
        attrs_sample = available_attributes[:50]
        projs_sample = available_projects[:20]

        prompt = f"""You are an intelligent agent for a real estate knowledge graph Q&A system.

**YOUR ROLE:** Understand queries, match them to available data, and decide how to respond.

**USER QUESTION:**
"{query}"

**AVAILABLE ATTRIBUTES (what can be queried):**
{json.dumps(attrs_sample, indent=2)}
{f'... ({len(available_attributes)} total)' if len(available_attributes) > 50 else ''}

**AVAILABLE PROJECTS:**
{json.dumps(projs_sample, indent=2)}
{f'... ({len(available_projects)} total)' if len(available_projects) > 20 else ''}
"""

        if kg_sample_data:
            prompt += f"""
**SAMPLE PROJECT DATA (to understand structure):**
{json.dumps(kg_sample_data, indent=2)[:1000]}...
"""

        prompt += """
**YOUR TASK - THINK STEP BY STEP:**

1. **Understand the question:** What is the user really asking?

2. **Match entities (be VERY lenient):**
   - Spelling variations: "Shrinivas" ≈ "Shriniwas"
   - Sound-alike: "Sara" ≈ "Sarah"
   - Newlines as spaces: "Sara\\nCity" = "Sara City"
   - Units optional: "Annual Sales Value" = "Annual Sales Value (Rs.Cr.)"
   - Abbreviations: "PSF" = "Price Per Sqft"
   - Word order flexible: "Kate Residency" ≈ "Residency Kate"

3. **Decide action:**
   - `fetch_and_answer`: You know what to fetch and how to format
   - `need_clarification`: Query is ambiguous, need user to clarify
   - `error`: Can't match any entities

4. **Design response:**
   - Create a template with placeholders: `{VALUE}`, `{project}`, `{location}`, etc.
   - Decide what fields to fetch from KG
   - Think about the best format (formal, informative, concise)

**RESPONSE FORMAT (JSON only):**
```json
{
  "action": "fetch_and_answer | need_clarification | error",

  "attribute": "best matching attribute or null",
  "project": "best matching project or null",

  "response_template": "The {attribute} of {project} in {location} is {VALUE}",

  "kg_fields_needed": [
    "attribute_value",
    "project.location",
    "project.developer",
    "project.launch_date"
  ],

  "confidence": 0.95,

  "reasoning": "Your step-by-step thinking: How did you match? Why this template? What are you uncertain about?"
}
```

**EXAMPLES:**

**Example 1: Clear match with spelling variation**
Query: "What is the Annual Sales Value of Pradnyesh Shrinivas?"
Your thinking:
- Attribute: "Annual Sales Value" → matches "Annual Sales Value (Rs.Cr.)" (unit specification)
- Project: "Pradnyesh Shrinivas" → sounds like "Pradnyesh Shriniwas" (w vs v sound)  - Action: fetch_and_answer
- Template: Include project context for richness

Response:
```json
{
  "action": "fetch_and_answer",
  "attribute": "Annual Sales Value (Rs.Cr.)",
  "project": "Pradnyesh\\nShriniwas",
  "response_template": "The {attribute} of {project} in {location} is {VALUE}.",
  "kg_fields_needed": ["attribute_value", "project.location"],
  "confidence": 0.88,
  "reasoning": "Matched attribute exactly with unit spec. Project name matched phonetically (Shrinivas≈Shriniwas) with high confidence. Template includes context for informative answer."
}
```

**Example 2: Ambiguous query**
Query: "Tell me about new projects"
Your thinking:
- No specific attribute mentioned
- No specific project mentioned
- Too vague to give a single answer

Response:
```json
{
  "action": "need_clarification",
  "attribute": null,
  "project": null,
  "response_template": "I found {count} projects. Would you like to know about: {project_list}? Or ask about a specific attribute like Project Size, Total Supply, or Sold %?",
  "kg_fields_needed": ["all_projects.name"],
  "confidence": 0.3,
  "reasoning": "Query is too vague. No specific attribute or project. Need user to narrow down."
}
```

**Example 3: Not found**
Query: "What is the underwater basket weaving score?"
Your thinking:
- No matching attribute in available list
- Probably not a real estate metric

Response:
```json
{
  "action": "error",
  "attribute": null,
  "project": null,
  "response_template": "I don't have data on '{user_query}'. Available attributes include: Project Size, Total Supply, Annual Sales, etc. Please ask about one of these.",
  "kg_fields_needed": [],
  "confidence": 0.0,
  "reasoning": "No matching attribute found. Not a standard real estate metric."
}
```

---

Now think about the user's question above and respond with your decision in JSON format.
Be LENIENT with matching - prefer a good guess over requiring perfect matches.
"""

        return prompt


# Global instance
_ultrathink_agent = None

def get_ultrathink_agent() -> UltraThinkAgent:
    """Get or create global UltraThink agent"""
    global _ultrathink_agent
    if _ultrathink_agent is None:
        _ultrathink_agent = UltraThinkAgent()
    return _ultrathink_agent


# Convenience function for quick testing
def ask_ultrathink(
    query: str,
    available_attributes: List[str],
    available_projects: List[str]
) -> UltraThinkDecision:
    """
    Quick helper to ask UltraThink agent

    Usage:
        decision = ask_ultrathink(
            "What is the Project Size of Sara City?",
            ["Project Size", "Total Supply", ...],
            ["Sara City", "The Urbana", ...]
        )

        if decision.action == "fetch_and_answer":
            # Fetch from KG
            value = kg.get(decision.project, decision.attribute)
            # Fill template
            response = decision.response_template.replace("{VALUE}", str(value))
    """
    agent = get_ultrathink_agent()
    return agent.think(query, available_attributes, available_projects)
