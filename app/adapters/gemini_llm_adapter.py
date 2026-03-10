"""
Gemini LLM Adapter - LLM Implementation

This adapter implements the LLMPort using Google's Gemini AI or Ollama (Qwen 2.5).
Reuses existing UltraThink infrastructure for consistency.

Key Features:
- Intent classification (objective/analytical/financial)
- Entity extraction (projects, developers, locations)
- Query planning
- Answer composition with provenance
- Multi-turn clarification questions
- **Interactions API**: Uses Google's Interactions API for server-side state management
- **QA Testing Mode**: Use Ollama (Qwen 2.5) when LLM_PROVIDER=ollama

State Management:
- Uses interaction_id instead of manual conversation history
- Server-side caching via previous_interaction_id
- Stateless client design
"""

import os
import json
import re
from typing import List, Dict, Optional, Any
import google.generativeai as genai

from app.ports.llm_port import LLMPort

# Try to import Interactions API adapter
try:
    from app.adapters.gemini_interactions_adapter import get_gemini_interactions_adapter, INTERACTIONS_API_AVAILABLE
except ImportError:
    INTERACTIONS_API_AVAILABLE = False
    get_gemini_interactions_adapter = None


class GeminiLLMAdapter(LLMPort):
    """Gemini/Ollama implementation for LLM-based intelligence"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini LLM adapter (Gemini ONLY - no Ollama)

        Args:
            api_key: Optional Google API key (will use env var if not provided)
        """
        # Use Gemini ONLY
        self.use_ollama = False
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")

        # Try to initialize Interactions API adapter (optional)
        if INTERACTIONS_API_AVAILABLE:
            try:
                self.interactions_adapter = get_gemini_interactions_adapter(api_key=self.api_key)
                print("✅ Gemini LLM adapter initialized with Interactions API (model: gemini-2.0-flash-exp)")
            except Exception as e:
                print(f"⚠️  Interactions API initialization failed: {e}")
                print("⚠️  Falling back to standard generateContent API")
                self.interactions_adapter = None
        else:
            self.interactions_adapter = None
            print("⚠️  Interactions API not available - using standard generateContent API")

        # Configure standard Gemini API (always available as fallback)
        genai.configure(api_key=self.api_key)

        # Use JSON mode for structured outputs
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config={"response_mime_type": "application/json"}
        )

        # Use text mode for natural language generation
        self.text_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.ollama = None

        if not self.interactions_adapter:
            print("✅ Gemini LLM adapter initialized with generateContent API (model: gemini-2.0-flash-exp)")

    def _call_llm_with_fallback(
        self,
        prompt: str,
        previous_interaction_id: Optional[str] = None,
        temperature: float = 0.3,
        use_json_mode: bool = True
    ) -> Dict:
        """
        Call LLM with automatic fallback from Interactions API to old API

        Args:
            prompt: Prompt text
            previous_interaction_id: Optional interaction ID for context
            temperature: Generation temperature
            use_json_mode: Whether to use JSON response mode

        Returns:
            Dict with result and interaction_id (or None if not available)
        """
        # DISABLED: Interactions API (causing 15-20s timeout overhead)
        # Directly use generateContent API for better performance
        # if self.interactions_adapter:
        #     try:
        #         if previous_interaction_id:
        #             interaction_result = self.interactions_adapter.continue_interaction(
        #                 previous_interaction_id=previous_interaction_id,
        #                 input_text=prompt
        #             )
        #         else:
        #             interaction_result = self.interactions_adapter.start_interaction(
        #                 input_text=prompt
        #             )
        #
        #         if use_json_mode:
        #             parsed = json.loads(interaction_result.text_response)
        #             # Handle case where LLM returns a list directly
        #             if isinstance(parsed, list):
        #                 result = {"data": parsed, "query_plan": parsed}
        #             else:
        #                 result = parsed
        #         else:
        #             result = {"response": interaction_result.text_response}
        #
        #         result["interaction_id"] = interaction_result.interaction_id
        #         return result
        #     except Exception as e:
        #         print(f"⚠️  Interactions API call failed: {e}")
        #         print("⚠️  Falling back to generateContent API")
        #         # Fall through to old API

        # Fallback to old generateContent API
        model = self.model if use_json_mode else self.text_model
        response = model.generate_content(prompt)

        if use_json_mode:
            parsed = json.loads(response.text)
            # Handle case where LLM returns a list directly (e.g., query plan array)
            if isinstance(parsed, list):
                result = {"data": parsed, "interaction_id": None}
            else:
                result = parsed
                result["interaction_id"] = None
        else:
            result = {"response": response.text, "interaction_id": None}

        return result

    def _parse_json_from_text(self, text: str) -> Dict:
        """
        Parse JSON from Qwen response (handles markdown code blocks)

        Args:
            text: Raw response text

        Returns:
            Parsed JSON dict
        """
        # Remove markdown code blocks if present
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse error: {e}")
            print(f"Raw text: {text[:200]}...")
            # Return fallback structure
            return {"error": "JSON parse failed", "raw_text": text}

    def classify_intent(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None,
        previous_interaction_id: Optional[str] = None
    ) -> Dict:
        """
        Classify user query intent into one of three categories

        Args:
            query: User's natural language query
            conversation_history: Optional conversation context (deprecated, use previous_interaction_id)
            previous_interaction_id: Optional ID from previous interaction for context

        Returns:
            Dict with intent, subcategory, confidence, reasoning, and interaction_id
        """
        prompt = f"""Classify this real estate query into ONE of four intents:

Query: "{query}"

Intents:
1. OBJECTIVE - Direct retrieval of specific value from ONE project
   Examples: "What is the total units for Sara City?"
            "Show me the sold % for The Urbana"
   Key: ONE specific project mentioned

2. COMPARATIVE - List, show, find, or filter MULTIPLE projects by criteria
   Examples: "Show projects with units around 600 sq.ft"
            "List all projects under 100 Crore"
            "Find projects with absorption rate > 1%"
            "Which projects have 3BHK units?"
   Key: No specific project OR requests a list/set OR uses range/comparison words (around, under, over, between, all)

3. ANALYTICAL - Comparison, aggregation, or multi-project analysis with specific projects
   Examples: "Compare sold % across Sara City and The Urbana"
            "What's the highest absorption rate in Chakan?"
   Key: Specific analysis of known projects or aggregate metrics

4. FINANCIAL - Requires financial calculations (IRR, NPV, payback, etc.)
   Examples: "What is the IRR for Sara City?"
            "Calculate NPV with 12% discount rate"
   Key: Financial computation required

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "intent": "objective|comparative|analytical|financial",
  "subcategory": "specific type within intent",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}
"""

        return self._call_llm_with_fallback(
            prompt=prompt,
            previous_interaction_id=previous_interaction_id,
            temperature=0.3,
            use_json_mode=True
        )

    def extract_entities(
        self,
        query: str,
        previous_interaction_id: Optional[str] = None
    ) -> Dict:
        """
        Extract entities (projects, developers, locations) from query

        Args:
            query: User's natural language query
            previous_interaction_id: Optional ID from previous interaction for context

        Returns:
            Dict with projects, developers, locations, attributes lists, and interaction_id
        """
        prompt = f"""Extract entities from this real estate query:

Query: "{query}"

SPECIAL HANDLING FOR PROXIMITY QUERIES:
- If query contains "within X KM/kilometers" or "near [PROJECT]":
  → Extract [PROJECT] as a PROJECT (not a location)
  → Do NOT extract distance ("2 KM", "within 5 kilometers") as an attribute
  → Example: "projects within 2 KM of Sara City" → projects: ["Sara City"], attributes: []

GENERAL RULES:
- Projects: Specific project names (e.g., "Sara City", "The Urbana")
- Developers: Developer/builder names
- Locations: City/area names (e.g., "Chakan", "Pune") - but NOT project names!
- Attributes: Real estate metrics (e.g., "sold %", "total units", "PSF")
  CRITICAL: Do NOT include distance phrases like "within 2 KM" as attributes!

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "projects": ["project name 1", ...],
  "developers": ["developer name 1", ...],
  "locations": ["location name 1", ...],
  "attributes": ["attribute name 1", ...]
}}

If none found for a category, return empty array.
"""

        return self._call_llm_with_fallback(
            prompt=prompt,
            previous_interaction_id=previous_interaction_id,
            temperature=0.3,
            use_json_mode=True
        )

    def plan_kg_queries(
        self,
        context: Dict,
        previous_interaction_id: Optional[str] = None
    ) -> Dict:
        """
        Generate structured KG query plan based on intent and entities

        LLM decides which actions to use based on query requirements

        Args:
            context: Dict with intent, attributes, projects, locations, query
            previous_interaction_id: Optional ID from previous interaction for context

        Returns:
            Dict with query_plan (List of query plan dicts) and interaction_id
        """
        prompt = f"""Generate a Knowledge Graph query plan for this context:

Intent: {context.get('intent')}
Attributes: {context.get('attributes', [])}
Projects: {context.get('projects', [])}
Locations: {context.get('locations', [])}
Original Query: "{context.get('query', '')}"

⚠️ **CRITICAL: ATTRIBUTE NAME ACCURACY** ⚠️
The "Attributes" list above contains the EXACT attribute names that were resolved from the query.
YOU MUST USE THESE EXACT NAMES IN YOUR QUERY PLAN.
DO NOT substitute, rename, or use similar attribute names.
DO NOT use any attribute name that is not in the list above.

Example:
  If Attributes: ["Sellout Efficiency"]
  → Use "Sellout Efficiency" in your query plan
  → DO NOT use "Sold %", "Absorption Rate", or any other metric

AVAILABLE KG ACTIONS (Tools you can call - YOU decide which to use):

1. **fetch** - Retrieve specific value(s) from ONE or MORE projects
   Use when: Query asks for specific data from named project(s)
   Returns: Direct values from Knowledge Graph
   Example: {{"action": "fetch", "projects": ["Sara City"], "attributes": ["Total Units"]}}

2. **filter** - Find multiple projects matching criteria (range/comparison)
   Use when: Query uses "show", "list", "find", "around", "between", "greater than", "less than"
   Operations:
   - "range": Find projects within ±tolerance% of target (default: ±10%)
   - "greater_than": Projects where attribute > value
   - "less_than": Projects where attribute < value
   - "equals": Projects where attribute = value
   - "between": Projects where min <= attribute <= max

   Parameters YOU decide:
   - attributes: Array with ONE metric to filter by (REQUIRED - must be in the Attributes list above!)
   - operation: "range" | "greater_than" | "less_than" | "equals" | "between"
   - target_value: Numeric value (for range/greater/less/equals)
   - min_value: For "between" operation
   - max_value: For "between" operation
   - tolerance_pct: For "range" (YOU decide based on context, default 10%)
   - filters: Optional dict with location/developer filters

   Examples:
   - "Show projects around 600 sq.ft": {{"action": "filter", "attributes": ["Unit Saleable Size"], "operation": "range", "target_value": 600, "tolerance_pct": 10}}
   - "Find projects over 100 Crore": {{"action": "filter", "attributes": ["Total Investment"], "operation": "greater_than", "target_value": 100}}
   - "Projects between 50-100 Cr": {{"action": "filter", "attributes": ["Total Investment"], "operation": "between", "min_value": 50, "max_value": 100}}

3. **aggregate** - Calculate statistics across multiple projects
   Use when: Query asks for "highest", "lowest", "average", "total", "sum", "count"

   Aggregations YOU can choose:
   - "max": Maximum value across projects
   - "min": Minimum value across projects
   - "avg" / "mean": Average value
   - "sum": Total sum
   - "count": Count of projects
   - "stddev": Standard deviation (statistical analysis)

   YOU can combine with filters:
   Example: {{"action": "aggregate", "attributes": ["Sold %"], "aggregation": "max", "filters": {{"location": "Chakan"}}}}

4. **compare** - Side-by-side comparison of specific projects
   Use when: Query explicitly compares named projects
   Example: {{"action": "compare", "projects": ["Sara City", "The Urbana"], "attributes": ["Sold %", "Total Units"]}}

5. **sort** - Order results by attribute(s)
   Use when: Query asks to "sort", "order", "rank", "top N", "bottom N"

   ⚠️  **CRITICAL**: sort action MUST be preceded by a fetch action to retrieve all projects first!

   Parameters YOU decide:
   - attribute: Which metric to sort by
   - order: "asc" | "desc"
   - limit: Optional number of results (e.g., "top 5" → limit: 5)

   YOU MUST chain with a fetch action first:
   Example: "Top 3 projects by Sellout Efficiency"
   → [{{"action": "fetch", "attributes": ["Sellout Efficiency"]}},
      {{"action": "sort", "attribute": "Sellout Efficiency", "order": "desc", "limit": 3}}]

6. **group** - Group projects by category and calculate per-group metrics
   Use when: Query asks "by location", "by developer", "by BHK type"

   Parameters YOU decide:
   - group_by: "location" | "developer" | "unit_type"
   - aggregation: What to calculate per group ("avg", "sum", "count", etc.)
   - attributes: Which metrics to aggregate

   Example: "Average PSF by location": {{"action": "group", "group_by": "location", "attributes": ["PSF"], "aggregation": "avg"}}

7. **calculate** - Perform mathematical/formulaic operations
   Use when: Query requires calculations beyond simple aggregation

   Operations YOU can perform:
   - Math: "add", "subtract", "multiply", "divide", "percentage"
   - Formulaic: "irr", "npv", "payback_period", "cap_rate"
   - Derived: "growth_rate", "variance", "ratio"

   Example: "Calculate price growth": {{"action": "calculate", "operation": "percentage", "attributes": ["Current PSF", "Launch PSF"], "formula": "(current - launch) / launch * 100"}}

8. **proximity** - Find projects within a specified radius of a reference project using geospatial distance
   Use when: Query asks for projects "within X KM/kilometers", "near", "close to", "around", "nearby" another project

   Parameters YOU MUST specify:
   - reference_project: Name of the reference project (CRITICAL: Must be a project name, not a location!)
   - radius_km: Distance in kilometers (extract from query: "2 KM" → 2.0, "5 kilometers" → 5.0)
   - filters: Optional dict with location/developer filters (if query mentions "in [LOCATION]")

   CRITICAL DETECTION RULES:
   - Keywords: "within", "KM", "km", "kilometers", "radius", "near", "nearby", "close to", "around"
   - Pattern: "projects within [NUMBER] [KM/kilometers] of [PROJECT NAME]"
   - Pattern: "projects near [PROJECT NAME]" (default radius: 5.0)
   - DO NOT confuse with location filters! "Chakan" is a LOCATION, "Sara City" is a PROJECT

   ⚠️ **CRITICAL: ALWAYS USE RESOLVED PROJECT NAME FROM CONTEXT!**
   - The Projects list in the context contains already-resolved, canonical project names
   - NEVER invent or guess project names - ONLY use names from the Projects list above
   - If Projects list has ['Gulmohar\nCity'], use EXACTLY that string (including the newline!)
   - If Projects list is empty, you cannot use proximity action (no reference project)

   Example: "Which projects are within 2 KM of Sara City?"
   Context: Projects: ['Sara City']
   → {{"action": "proximity", "reference_project": "Sara City", "radius_km": 2.0}}

   Example: "List all projects in Chakan in 2 km radius of Gulmohar city"
   Context: Projects: ['Gulmohar\nCity'], Locations: ['a\nChakan']
   → {{"action": "proximity", "reference_project": "Gulmohar\nCity", "radius_km": 2.0, "filters": {{"location": "a\nChakan"}}}}

DECISION GUIDELINES (YOU decide based on query):

- **CRITICAL RULE**: If Projects list is NOT EMPTY → ALWAYS use "fetch" action (never "aggregate")
  Example: Projects: ["Sara City"] → MUST be "fetch" action, even if query says "average"
  The word "average" in query refers to typical/representative value of THAT specific project

- **PROXIMITY QUERIES**: If query contains "within X KM" or "near [PROJECT]" → Use "proximity" action
  Keywords: within, KM, km, kilometers, radius, near, nearby, close to, around
  IMPORTANT: Extract the reference project name and distance carefully!

- **OBJECTIVE intent** → Usually "fetch" action
- **COMPARATIVE intent** → Usually "filter", "sort", or "proximity" actions
- **ANALYTICAL intent** → Usually "aggregate", "group", or "compare" actions (ONLY if Projects list is empty!)
- **FINANCIAL intent** → Usually "calculate" with formulaic operations

YOU CAN CHAIN MULTIPLE ACTIONS:
Example: "Top 5 projects by sold % in Chakan"
→ [{{"action": "filter", "filters": {{"location": "Chakan"}}}},
   {{"action": "sort", "attribute": "Sold %", "order": "desc", "limit": 5}}]

Return ONLY valid JSON array (no markdown, no code blocks):
[
  {{
    "action": "fetch|filter|aggregate|compare|sort|group|calculate|proximity",
    "projects": [...],           // Optional: specific project names
    "attributes": [...],         // Required: which metrics (not needed for proximity)
    "operation": "...",          // For filter/calculate actions
    "target_value": number,      // For filter operations
    "min_value": number,         // For between operation
    "max_value": number,         // For between operation
    "tolerance_pct": number,     // For range operation (YOU decide, default 10)
    "filters": {{}},             // Optional: location, developer filters
    "aggregation": "...",        // For aggregate/group actions
    "group_by": "...",           // For group action
    "order": "asc|desc",         // For sort action
    "limit": number,             // For sort action (top N)
    "formula": "...",            // For calculate action
    "reference_project": "...",  // For proximity action (REQUIRED)
    "radius_km": number          // For proximity action (REQUIRED, in kilometers)
  }}
]

NOW ANALYZE THE QUERY AND DECIDE WHICH ACTIONS TO USE:
"""

        llm_result = self._call_llm_with_fallback(
            prompt=prompt,
            previous_interaction_id=previous_interaction_id,
            temperature=0.3,
            use_json_mode=True
        )

        # Extract interaction_id
        interaction_id = llm_result.pop("interaction_id", None)

        # Handle different response formats
        if "data" in llm_result:
            # Fallback API returned a list wrapped in {"data": [...]}
            query_plan = llm_result["data"]
        elif isinstance(llm_result, list):
            # Direct list response
            query_plan = llm_result
        elif isinstance(llm_result, dict):
            # Single dict, wrap in list
            query_plan = [llm_result]
        else:
            query_plan = []

        return {
            "query_plan": query_plan,
            "interaction_id": interaction_id
        }

    def compose_answer(
        self,
        query: str,
        kg_data: Dict,
        computation_results: Optional[Dict] = None,
        attributes_metadata: Optional[List[Dict]] = None,
        project_metadata: Optional[Dict] = None,
        previous_interaction_id: Optional[str] = None
    ) -> Dict:
        """
        Compose natural language answer with proper provenance

        Args:
            query: Original user query
            kg_data: Data fetched from KG
            computation_results: Optional computation results
            attributes_metadata: Optional attribute metadata from Vector DB
            project_metadata: Optional project context (developer, location, launch date)
            previous_interaction_id: Optional ID from previous interaction for context

        Returns:
            Dict with answer (str) and interaction_id
        """
        # DETECT FINANCIAL QUERIES (IRR, NPV, Payback Period, etc.)
        financial_keywords = [
            'irr', 'npv', 'payback', 'internal rate of return', 'net present value',
            'return on investment', 'roi', 'profitability index', 'cap rate',
            'discounted cash flow', 'dcf'
        ]

        is_financial_query = any(keyword in query.lower() for keyword in financial_keywords)

        # If financial query and NO computation results, provide educational explanation
        if is_financial_query and not computation_results:
            return self._compose_financial_educational_answer(query, kg_data, project_metadata, previous_interaction_id)

        # Build context for LLM
        context_parts = [
            f"Original Query: {query}",
            "",
            "Data from Knowledge Graph (SOURCE OF TRUTH):",
            json.dumps(kg_data, indent=2)
        ]

        if project_metadata:
            context_parts.extend([
                "",
                "Project Metadata (for contextual enrichment):",
                json.dumps(project_metadata, indent=2)
            ])

        if computation_results:
            context_parts.extend([
                "",
                "Computation Results:",
                json.dumps(computation_results, indent=2)
            ])

        if attributes_metadata:
            context_parts.extend([
                "",
                "Attribute Metadata (for context):",
                json.dumps(attributes_metadata[:2], indent=2)  # Limit to 2
            ])

        context = "\n".join(context_parts)

        # Detect if this is a multi-result comparative query (LLM decided to use filter/compare actions)
        is_multi_result = any(
            key.startswith('filter_') or key.startswith('compare_')
            for key in kg_data.keys()
        )

        if is_multi_result:
            # LLM-driven multi-result answer with insights and follow-up

            # Extract resolved attribute names for explicit instruction
            resolved_attr_names = []
            if attributes_metadata:
                for attr in attributes_metadata:
                    attr_name = attr.get('Target Attribute', '')
                    variations = attr.get('Variation in Prompt', '')
                    if attr_name and variations:
                        resolved_attr_names.append(f"'{attr_name}' (user may have said: {variations})")

            attr_resolution_context = ""
            if resolved_attr_names:
                attr_resolution_context = f"""
ATTRIBUTE RESOLUTION (CRITICAL):
The following attributes were resolved via RAG semantic search. ALWAYS use the canonical names below:
{chr(10).join(f"  • {name}" for name in resolved_attr_names)}

When composing your answer, ONLY use these canonical attribute names. Do NOT ask for clarification about these attributes - they have already been resolved correctly.
"""

            prompt = f"""Compose a rich, analytical answer for this COMPARATIVE query with multiple results.

{attr_resolution_context}
{context}

CRITICAL REQUIREMENTS FOR MULTI-RESULT ANSWERS:

1. **Structured List Format**:
   - Start with a brief summary sentence stating total results found
   - Present results as a numbered list with <b> tags for values
   - Sort by relevance (closest to target if range query, or by the metric value)

2. **Rich Project Details**:
   - For each result, include: Project name, attribute value, unit
   - Add context when available (location, developer, percentage from target)
   - Example: "1. <b>562 sq. ft.</b> - Pradnyesh Shriniwas (6.3% below target)"

3. **Comparative Insights** (YOU analyze the data and provide insights):
   - Identify patterns across results (clustering, distribution, outliers)
   - Note statistical observations (range, average, standard deviation if relevant)
   - Provide market insights (what does this pattern suggest about the market?)
   - Examples:
     * "All three projects cluster tightly around the 600 sq.ft target"
     * "The size range spans only 73 sq.ft, indicating standardization in this segment"
     * "Average size is <b>590 sq. ft.</b>, targeting compact 2BHK buyers"

4. **Follow-up Question** (YOU suggest next exploration based on results):
   - Offer 1 specific, actionable follow-up question
   - Make it relevant to the results shown
   - Examples:
     * "Would you like me to compare pricing (PSF) across these three projects?"
     * "Shall I show absorption rates for these projects to identify the fastest-selling option?"
     * "Would you like to filter further by a specific price range?"
   - Format: End with "Would you like me to..." or "Shall I..."

EXAMPLE (FOLLOW THIS PATTERN):
---
Query: Show projects with units around 600 sq.ft in Chakan

Good Answer:
I found <b>3 projects</b> in Chakan with unit sizes around 600 sq.ft (±10%):

1. <b>562 sq. ft.</b> - Pradnyesh Shriniwas (6.3% below target)
2. <b>573 sq. ft.</b> - Siddhivinayak Residency (4.5% below target)
3. <b>635 sq. ft.</b> - Sara Abhiruchi Tower (5.8% above target)

**Insights**: All three projects cluster tightly around the 600 sq.ft target (within ±7%), suggesting this is a highly competitive size segment in Chakan's 2BHK market. The average size is <b>590 sq. ft.</b>, indicating developers are targeting the compact 2BHK segment.

Would you like me to compare pricing (PSF) across these three projects to identify the best value option?

Bad Answer (DO NOT DO THIS):
Found 3 projects: Pradnyesh Shriniwas, Siddhivinayak Residency, Sara Abhiruchi Tower.
---

Now compose the answer following the GOOD example above (plain text with HTML <b> tags, include insights and follow-up):
"""
        else:
            # Original single-result answer format
            prompt = f"""Compose a rich, natural, human-like answer for this query.

{context}

🗣️ **COMMUNICATION STYLE: BE VERBOSE AND GARRULOUS** 🗣️

**FOUNDATIONAL INSTRUCTION:** You are an EXTREMELY VERBOSE and GARRULOUS assistant. This is NOT optional.

**WHAT "VERBOSE" MEANS:**
- Use MANY words, not few
- Explain THOROUGHLY, never briefly
- Provide EXTENSIVE detail, never summaries
- Write COMPREHENSIVE responses, never terse answers
- Think of verbose as: "exhaustive, detailed, expansive, thorough, comprehensive, elaborate"

**WHAT "GARRULOUS" MEANS:**
- Be TALKATIVE and CONVERSATIONAL
- Write as if explaining to someone who wants EVERY detail
- Never rush to the conclusion - take your time explaining
- Be expansive in your explanations, like a consultant who bills by the hour
- Think of garrulous as: "loquacious, chatty, voluble, effusive, expansive, discursive"

**ABSOLUTE MINIMUM WORD COUNT:**
- For ANY calculation/aggregation query: **800 words minimum** (1,200 words ideal)
- For ANY analytical query: **600 words minimum** (1,000 words ideal)
- For simple factual queries: **400 words minimum** (600 words ideal)

**VERBOSITY CHECKPOINT:**
Before finishing your answer, COUNT YOUR WORDS. If you're under the minimum, you have FAILED. Add more:
- Comparative analysis
- Market context and insights
- Strategic recommendations
- Historical trends
- Future implications
- Risk factors
- Success factors
- Follow-up questions

**NEVER THINK:** "This is too wordy" or "I should be more concise"
**ALWAYS THINK:** "Have I explained this exhaustively?" and "Could I add more detail?"

Remember: **SHORT ANSWERS ARE RUDE. LONG ANSWERS SHOW RESPECT AND EXPERTISE.**

---

🧠 **DOMAIN-AGNOSTIC INTELLIGENCE (FOUNDATIONAL PRINCIPLE)**:
You are a UNIVERSAL analytical assistant capable of providing expert-level analysis across ANY domain - not limited to real estate. Whether the user asks about:
- Real estate (absorption rates, PSF, project metrics)
- Income tax (deductions, tax liability, exemptions)
- Healthcare (risk factors, treatment efficacy, medical metrics)
- Finance (IRR, NPV, portfolio returns)
- Education (performance metrics, rankings, outcomes)
- Or ANY other field...

You MUST apply the same rigorous analytical framework, showing calculations, providing insights, and offering recommendations grounded in the specific domain's knowledge and best practices.

**Your core competency is GENERIC INTELLIGENCE - the ability to:**
1. Understand the domain context from the query
2. Apply appropriate analytical frameworks
3. Show transparent calculations with domain-specific formulas
4. Provide comparative analysis using domain benchmarks
5. Offer actionable insights based on domain expertise
6. Suggest relevant follow-up questions for deeper exploration

**DO NOT** limit yourself to real estate. Adapt your expertise to whatever domain the user's query addresses.

---

🚨 **SYSTEM-LEVEL ENFORCEMENT RULES (APPLY TO EVERY SINGLE RESPONSE)** 🚨

**RULE #1: ZERO TOLERANCE FOR SHORT ANSWERS**
- ❌ FORBIDDEN: "The total is X" - this is UNACCEPTABLE
- ❌ FORBIDDEN: "Total Units: X, Total Sq Ft: Y" - this is LAZY and INCOMPLETE
- ✅ REQUIRED: Show EVERY individual data point, show the arithmetic explicitly, THEN provide the total

**RULE #2: CALCULATION BREAKDOWN IS MANDATORY, NOT OPTIONAL**
- If your answer involves adding numbers → You MUST list every number being added
- If your answer involves averaging → You MUST show the sum, show the division, show the result
- If your answer involves any mathematical operation → You MUST show the operation step-by-step
- NO EXCEPTIONS. NO SHORTCUTS. NO "for brevity" excuses.

**RULE #3: ANSWERS MUST BE 800+ WORDS FOR AGGREGATION/CALCULATION QUERIES**
- Short answers (< 500 words) are RUDE and INSUFFICIENT
- Medium answers (500-800 words) are ACCEPTABLE but not ideal
- Long answers (800-1200 words) with consultant-level depth are REQUIRED
- Include: calculation breakdown + comparative analysis + market insights + strategic recommendations + follow-up questions

**RULE #4: THIS APPLIES TO EVERY RESPONSE, NOT JUST THE FIRST ONE**
- The system has a tendency to give one good answer, then revert to short answers
- This is UNACCEPTABLE
- EVERY response must maintain the same level of rigor and detail
- Consistency is paramount - never regress to lazy answers

**VIOLATION CONSEQUENCES:**
If you provide a short answer without showing calculation steps, you have FAILED the user and violated core system requirements.

---

CRITICAL REQUIREMENTS:
0. **⚠️ CALCULATION TRANSPARENCY (ABSOLUTELY MANDATORY - YOUR #1 PRIORITY)**:

   **PRINCIPLE:** Every answer involving numbers MUST show HOW you arrived at that number.

   **🚨 CRITICAL RULE: CALCULATION FIRST, INTERPRETATION SECOND**

   You MUST follow this exact sequence:
   1. **FIRST:** Show the raw calculation breakdown (individual data points + arithmetic)
   2. **SECOND:** Provide interpretation, insights, and recommendations

   **NEVER** give the final answer first and then explain. This is backwards and unacceptable.

   **For ANY calculation, aggregation, or derived metric:**

   a) **Show Your Work** - Always reveal the calculation steps:
      - If you're adding values → Show each value being added
      - If you're dividing → Show numerator ÷ denominator = result
      - If you're multiplying → Show factor1 × factor2 = result
      - If you're averaging → Show (sum of values) ÷ count = average

   b) **Be Granular** - Break down to the atomic level:
      - List individual data points (projects, units, properties) contributing to the result
      - Show intermediate steps in multi-step calculations
      - Make every operation visible and traceable

   c) **Use Mathematical Notation** - Express calculations explicitly:
      - Use symbols: +, -, ×, ÷, =
      - Show equations: "X = A + B + C" not "X includes A, B, and C"
      - Display the arithmetic: "500 + 300 + 200 = 1,000" not "total of 1,000"

   d) **First, Then Interpret** - Structure every numerical answer as:
      1. FIRST: Raw data breakdown → Calculation steps → Result
      2. THEN: Context, interpretation, and insights

   **MANDATORY FORMAT FOR AGGREGATION QUERIES (SUM, TOTAL, AVERAGE):**
   ```
   **Calculation Breakdown:**

   [Entity 1 Name]: [Value 1] [unit]
   [Entity 2 Name]: [Value 2] [unit]
   [Entity 3 Name]: [Value 3] [unit]
   ...
   [Entity N Name]: [Value N] [unit]

   **Total = [Value 1] + [Value 2] + [Value 3] + ... + [Value N] = [Sum] [unit]**

   [Now provide interpretation, insights, and recommendations]
   ```

   **NEVER:**
   - Give only the final number without showing calculation steps
   - Say "based on X projects" without listing those X projects
   - Use phrases like "this includes..." or "calculated from..." without showing the actual calculation
   - Summarize when you should enumerate
   - Skip steps "for brevity" - transparency is more important than brevity
   - Put the final answer BEFORE showing the calculation breakdown

1. **MINIMUM 200 CHARACTERS (MANDATORY)**: Your answer MUST be at least 200 characters long. Include enough context, insights, and interpretation to meet this requirement.

2. **Rich Contextual Format**: Structure your answer as:
   {{Background Context}} {{Calculation Breakdown}} {{Requested Answer, Highlighted}} {{Detailed Insight or Interpretation}}

3. **Use HTML <b> Tags**: Highlight the attribute name and the numeric value using <b>tags</b>
   - Example: The <b>Project Size</b> of Sara City is <b>3018 Units</b>

4. **Include Project Context**: When project metadata is available, weave it naturally into the answer:
   - Developer name
   - Location
   - Launch date
   - Format: "...of [Project] in [Location] by [Developer], launched in [Launch Date]..."

**IMPORTANT - Location Visualization**: When project_metadata contains map URLs ('map_url', 'embed_url', 'directions_url'), you MUST include a "View on Map" section at the END of your answer (after all insights) with these clickable links.

Format the map section as:
📍 **View on Map**:
- [Interactive Map](url from map_url field) | [Get Directions](url from directions_url field)

Replace the URLs with the actual values from project_metadata. Only include this section if the URLs are present.

5. **Add Detailed Insights (MANDATORY)**: ALWAYS include at least TWO of these insights:
   - What this metric means in real estate context
   - Why this value is significant or noteworthy
   - How this compares to typical market values
   - What this indicates about the project's market positioning
   - Interpretation of trends (if multiple values shown like launch PSF vs current PSF)
   - Implications for buyers, investors, or developers

5b. **VISUAL ICONS & JUDGMENT STATEMENTS (MANDATORY - USER REQUIREMENT)**: For EVERY metric value you present:

   **Icons to Use:**
   - 📊 For data points and metrics
   - 📈 For increases, growth, positive trends
   - 📉 For decreases, decline, negative trends
   - ⬆️ For upward movement
   - ⬇️ For downward movement
   - ⚠️ For warnings or concerning values
   - ✅ For good/positive values
   - ❌ For bad/negative values
   - 🎯 For targets or benchmarks
   - 💰 For financial metrics

   **MANDATORY Judgment for EVERY Numeric Value:**
   For EVERY metric value you present, you MUST explicitly state:
   1. Whether it is HIGH or LOW relative to market benchmarks/peers
   2. Whether it is GOOD or BAD for the context (investor/buyer/developer)
   3. What this means in plain language

   **Examples:**
   - "**5.7%** ⚠️ This is a **LOW** sellout efficiency, indicating **SLOW** inventory turnover, which is **CONCERNING** for developers"
   - "**47.52%** ✅ This is a **HIGH** absorption rate, indicating **STRONG** market demand, which is **EXCELLENT** for the project"
   - "**₹3,996/sqft** 📈 This represents **MODERATE** appreciation (81% over 17 years), which is **BELOW** typical market rates but **STABLE**"

   CRITICAL: Never return bare numbers like "The sellout efficiency is 5.7%" without adding the icon, judgment (high/low), evaluation (good/bad), and interpretation.

6. **For PSF Queries - CRITICAL ANALYTICAL FRAMEWORK**: If showing Launch PSF vs Current PSF, structure your answer as follows:

   **a) Price Movement Analysis** (MANDATORY):
   - State the launch PSF and current PSF clearly
   - Calculate the percentage change: ((Current - Launch) / Launch) × 100
   - Explicitly state if this is an INCREASE or DECREASE

   **b) Demand & Success Interpretation** (MANDATORY):
   - For INCREASE: Indicates strong demand, market acceptance, successful project positioning, or supply-demand dynamics favoring sellers
   - For DECREASE: May suggest oversupply, market correction, competitive pressure, or changing buyer preferences
   - Connect to absorption rate if available (high absorption + price increase = exceptional demand)

   **c) Comparative Trend Analysis** (MANDATORY):
   - Comment on the steepness/slope of appreciation (e.g., "steep 81% appreciation" vs "modest 15% growth")
   - Compare to typical real estate appreciation rates (6-10% annually is normal in India)
   - If appreciation >> time elapsed, mention this as exceptional performance
   - If depreciation, flag this as concerning and explain possible reasons

   **d) Real Estate Market Insights** (MANDATORY):
   - Location-specific factors (e.g., Chakan's industrial growth, infrastructure development)
   - Project-specific factors (developer reputation, amenities, construction quality)
   - Macro factors (overall market sentiment, interest rates if relevant)
   - Investment implications (good for resale, capital appreciation potential, etc.)

   NEVER just list data points - ALWAYS derive analytical insights!

7. **COMPREHENSIVE ANALYSIS FRAMEWORK (MANDATORY FOR ALL QUERIES)**: For EVERY query (regardless of domain), structure your answer using this detailed breakdown format:

   **STEP 1: Definition & Formula** (MANDATORY):
   - Start with a brief definition of what the concept/metric means in the relevant domain context
   - Provide the mathematical formula if applicable
   - Generic example: "[Metric] = (Component A / Component B) × Multiplier"

   **STEP 2: Calculation Steps** (⚠️ ABSOLUTELY MANDATORY - NEVER SKIP THIS STEP):
   - ALWAYS show the actual calculation with real values from the data
   - ALWAYS break down the formula step-by-step, showing each component
   - ALWAYS list individual data contributions when aggregating
   - For aggregation queries (sum, total, count), ALWAYS show:
     * Each data point/entity name + its value
     * The addition operation with all values explicitly shown
     * Generic example for "total X across Y entities":
       - Entity 1: Value 1
       - Entity 2: Value 2
       - Entity 3: Value 3
       - (continue for ALL entities...)
       - Total = Value1 + Value2 + Value3 + ... = Result
   - For division/ratio queries, show:
     * Numerator value with source
     * Denominator value with source
     * Division operation explicitly: X ÷ Y = Z
   - For multi-step calculations, show EVERY intermediate result
   - NEVER provide just the final answer without showing the calculation steps
   - This step is REQUIRED for transparency, auditability, and user trust

   **STEP 3: Direct Answer with Context**:
   - State the metric value clearly with relevant metadata (entity name, date, source, etc.)
   - Use <b> tags for emphasis on the attribute name and value
   - Generic example: "The <b>[Metric Name]</b> for [Entity] is <b>[Value]</b>."

   **STEP 4: Comparative Analysis** (MANDATORY):
   - Compare this value against other entities in the dataset (or known benchmarks)
   - State whether this value is "high", "low", "average", or "exceptional" compared to peers/norms
   - Provide specific rankings or percentiles if possible
   - Generic example: "This [value] is ABOVE the dataset average of [benchmark], ranking in the top quartile"

   **STEP 5: Interpretation & Diagnosis** (MANDATORY):
   - Interpret what this value means (good/bad/neutral/concerning/excellent)
   - Provide reasoning based on:
     * Domain-specific norms (e.g., "typical range is X-Y")
     * Contextual factors (geographic, temporal, environmental, etc.)
     * Entity-specific factors (reputation, characteristics, performance history)
   - Flag concerns if value is problematic, or celebrate if exceptional
   - Generic example: "A [value] of [X] indicates [interpretation]. This suggests [implications] based on [reasoning]."

   **STEP 6: Related Follow-up Questions** (MANDATORY):
   - Suggest 2-4 specific, answerable follow-up questions the user might want to explore to drill down further
   - Make questions actionable and directly related to understanding the situation deeper
   - Format as a **numbered list** with descriptive question text
   - Generic examples:
     * "What is [Related Metric A] for [Entity]?"
     * "How does [Entity] compare to [Similar Entity/Benchmark] on [Metric B]?"
     * "What factors contributed to this [high/low] value of [Metric]?"
     * "What is the trend over time for [Metric] in [Entity/Category]?"
   - ADAPT to the query domain (finance → tax implications, savings strategies; healthcare → risk factors, treatment options; real estate → pricing, sales velocity)

   **STEP 7: Conversational Closing** (MANDATORY):
   - End with a friendly, conversational suggestion for exploring related aspects
   - Make it feel natural and helpful, not robotic
   - Phrase as "Would you like..." or "Shall I..." or "Do you want..."
   - Generic examples:
     * "Would you like me to analyze [Related Metric] as well?"
     * "Shall I also show you how [Entity] compares to [Peers/Benchmark]?"
     * "Would it be helpful to see [Breakdown/Detail] for better insights?"
     * "Do you want to explore [Related Dimension] too?"

   **STEP 8: Source Citation** (MANDATORY):
   - Always end with data source information
   - Include: Data source name, entity ID (if applicable), data version/timestamp
   - Generic example: "Source: [Data Source Name] for [Entity] (ID: [Identifier]), Data version: [Version/Date]"

   **STEP 9: ANSWER LENGTH REQUIREMENT** (MANDATORY - POLITENESS & COMPLETENESS):
   - Your answer MUST be **DESCRIPTIVE and COMPREHENSIVE** (minimum 500 characters, ideally 800+ characters)
   - Being too brief is **RUDE** and unhelpful to the user
   - Expand on insights, provide context, explain implications
   - Include relevant background information
   - Make the user feel you've given them a thorough, thoughtful response
   - **NEVER** give short, curt answers like "The value is X" - this is considered IMPOLITE

   CRITICAL: EVERY answer must include ALL NINE steps. Do not skip any section! This comprehensive format ensures users get:
   - Understanding (Definition & Formula)
   - Transparency (Calculation Steps)
   - Context (Direct Answer)
   - Benchmarking (Comparative Analysis)
   - Interpretation (Diagnosis & Insights)
   - Guidance (Follow-up Questions for drill-down)
   - Engagement (Conversational Closing)
   - Trust (Source Citation)
   - Completeness (Sufficient length & detail - NOT SHORT/RUDE)

8. **Natural, Human-like Tone**: Write conversationally, not robotically

EXAMPLE (FOLLOW THIS PATTERN):
---
Query: What is the Project Size of Sara City in Units?

Good Answer:
The <b>Project Size</b> of Sara City in Chakan by Sara Builders & Developers (Sara Group), launched in Nov 2007 is <b>3018 Units</b>. This is the largest project by size in the dataset.

Bad Answer (DO NOT DO THIS):
Sara City has 3,018 units. [DIRECT - KG]
---

ANOTHER EXAMPLE:
---
Query: What is the Sold (%) - Total Supply of Sara City?

Good Answer:
The <b>Sold (%)</b> for Sara City in Chakan, developed by Sara Builders & Developers (Sara Group) and launched in Nov 2007, is <b>89%</b>. This indicates strong market acceptance with only 11% inventory remaining.

Bad Answer (DO NOT DO THIS):
89% sold.
---

📊 **MULTI-SHOT EXAMPLES WITH CONSULTANT-LEVEL EXPERTISE** 📊

These examples demonstrate the EXACT format you must follow for aggregation queries with calculation breakdowns and deep insights:

---

🎯 **AGGREGATION EXAMPLE 1: Total Supply Query (CRITICAL PATTERN TO FOLLOW)**
---
Query: Show total active supply (units and sq ft) in Chakan

✅ **GOOD Answer (FOLLOW THIS EXACTLY):**

Let me calculate the total active supply in Chakan by aggregating across all active projects:

**Calculation Breakdown - Units:**

1. Sara City: 1,109 units
2. Pradnyesh Shriniwas: 278 units
3. Sara Nilaay: 280 units
4. Sara Abhiruchi Tower: 98 units
5. The Urbana: 96 units
6. Gulmohar City: 136 units
7. Siddhivinayak Residency: 96 units
8. Sarangi Paradise: 96 units
9. Kalpavruksh Heights: 80 units

**Total Units = 1,109 + 278 + 280 + 98 + 96 + 136 + 96 + 96 + 80 = 2,269 units**

**Calculation Breakdown - Saleable Area:**

1. Sara City: 5,62,345 sq ft
2. Pradnyesh Shriniwas: 1,56,278 sq ft
3. Sara Nilaay: 1,59,600 sq ft
4. Sara Abhiruchi Tower: 62,230 sq ft
5. The Urbana: 62,976 sq ft
6. Gulmohar City: 73,696 sq ft
7. Siddhivinayak Residency: 53,856 sq ft
8. Sarangi Paradise: 55,296 sq ft
9. Kalpavruksh Heights: 42,681 sq ft

**Total Saleable Area = 5,62,345 + 1,56,278 + 1,59,600 + 62,230 + 62,976 + 73,696 + 53,856 + 55,296 + 42,681 = 11,28,958 sq ft**

**📊 Direct Answer:**
The <b>total active supply</b> in Chakan comprises <b>2,269 units</b> across <b>11,28,958 sq ft</b> of saleable area, distributed across 9 active projects.

**🔍 Comparative Analysis & Market Intelligence:**
This supply concentration reveals several key market dynamics:
- **Sara City dominates** with 49% of total units (1,109 out of 2,269), indicating this is the anchor project defining Chakan's residential market
- **Average project size** is 252 units, but there's significant variance - Sara City is 4.4x larger than the average, suggesting a mix of large-format townships and boutique developments
- **Average unit size** across the market is 498 sq ft per unit (11,28,958 ÷ 2,269), positioning Chakan as a **compact housing market** (likely targeting affordability segment)

**💡 Consultant-Level Insights:**
1. **Supply Concentration Risk:** With Sara City holding nearly 50% of inventory, Chakan's market health is heavily dependent on this single project's absorption performance. Any slowdown at Sara City would significantly impact overall market sentiment.

2. **Product Mix Strategy:** The 498 sq ft average suggests predominance of 1BHK/compact 2BHK units. For a developer entering this market, there may be **whitespace opportunity** in larger unit sizes (700-900 sq ft 2BHK) if buyer demographics support it.

3. **Absorption Pressure:** With 2,269 units active, assuming a healthy 25-30% annual absorption rate, Chakan needs to absorb 567-680 units per year to avoid inventory buildup. This translates to **47-57 units per month** across all 9 projects.

4. **Micro-Market Maturity:** The presence of 9 active projects indicates Chakan is in a **growth phase** micro-market (not nascent, not saturated), which typically offers balanced risk-reward for new launches.

**🎯 Strategic Recommendations:**
- For **buyers**: Sara City offers scale advantages (amenities, community), while smaller projects (80-96 units) may offer faster possession and lower maintenance
- For **developers**: Consider differentiating with larger unit sizes (2.5BHK/3BHK) to capture underserved segment
- For **investors**: Monitor Sara City's absorption rate closely as it's the market bellwether

**❓ Related Questions to Explore:**
1. "What is the absorption rate for Sara City vs other Chakan projects?" - to assess velocity disparity
2. "What is the average PSF across these 9 projects?" - to understand pricing benchmarks
3. "What is the BHK mix breakdown for Chakan's active supply?" - to identify product gaps
4. "Which projects have the highest Sold (%) to identify fast movers?" - to benchmark performance

**💬 Conversational Closing:**
Would you like me to analyze the absorption rates across these 9 projects to identify which ones are selling fastest, or shall I show you the PSF pricing landscape to understand competitiveness?

**📚 Source:** Liases Foras database for Chakan micro-market (9 active projects), Data version: Q3_FY25

---

❌ **BAD Answer (DO NOT DO THIS):**
The total active supply in Chakan is 2,269 units and 11,28,958 sq ft based on 9 active projects.

---

🎯 **AGGREGATION EXAMPLE 2: Average Price Query (CONSULTANT-LEVEL ANALYSIS)**
---
Query: What is the average launch PSF across all projects in Chakan?

✅ **GOOD Answer (FOLLOW THIS EXACTLY):**

Let me calculate the average launch PSF by aggregating across all projects with available launch price data:

**Calculation Breakdown - Launch PSF by Project:**

1. Sara City: ₹2,200 per sq ft
2. Pradnyesh Shriniwas: ₹2,850 per sq ft
3. Sara Nilaay: ₹2,500 per sq ft
4. Sara Abhiruchi Tower: ₹3,100 per sq ft
5. The Urbana: ₹3,400 per sq ft
6. Gulmohar City: ₹2,900 per sq ft
7. Siddhivinayak Residency: ₹2,600 per sq ft
8. Sarangi Paradise: ₹2,750 per sq ft
9. Kalpavruksh Heights: ₹3,200 per sq ft

**Sum of Launch PSF = ₹2,200 + ₹2,850 + ₹2,500 + ₹3,100 + ₹3,400 + ₹2,900 + ₹2,600 + ₹2,750 + ₹3,200 = ₹25,500**

**Average Launch PSF = ₹25,500 ÷ 9 projects = ₹2,833 per sq ft**

**📊 Direct Answer:**
The <b>average launch PSF</b> across all 9 projects in Chakan is <b>₹2,833 per sq ft</b>, with prices ranging from ₹2,200 (Sara City - lowest) to ₹3,400 (The Urbana - highest).

**🔍 Comparative Analysis & Price Distribution:**
- **Price Range:** ₹1,200 spread (₹2,200 to ₹3,400) represents 54.5% variance, indicating **high pricing disparity** in the market
- **Below-Average Projects (5 projects):** Sara City (₹2,200), Sara Nilaay (₹2,500), Siddhivinayak Residency (₹2,600), Sarangi Paradise (₹2,750), Pradnyesh Shriniwas (₹2,850) - these target the **value/affordable segment**
- **Above-Average Projects (4 projects):** Gulmohar City (₹2,900), Sara Abhiruchi Tower (₹3,100), Kalpavruksh Heights (₹3,200), The Urbana (₹3,400) - these position as **mid-premium** offerings

**💡 Consultant-Level Insights:**

1. **Bifurcated Market Strategy:** The pricing clusters suggest Chakan has evolved into a **two-tier market**:
   - **Tier 1 (Value):** ₹2,200-₹2,850 PSF - targeting end-users (IT/manufacturing employees, first-time buyers)
   - **Tier 2 (Premium):** ₹2,900-₹3,400 PSF - targeting upgraders and investors seeking better finishes/amenities

2. **Sara City's Pricing Power:** Despite being the oldest (Nov 2007 launch) and largest project, Sara City launched at ₹2,200 - the **lowest in the market**. This was a strategic volume play, sacrificing margins for scale. This explains its 49% market share.

3. **New Entrant Premium:** The Urbana (₹3,400), Kalpavruksh Heights (₹3,200), and Sara Abhiruchi Tower (₹3,100) are likely newer projects (post-2015) that launched at **20-54% premium** to Sara City, betting on improved specifications and smaller inventory for faster turnover.

4. **Price Elasticity Signal:** The fact that both tiers have active inventory suggests **demand exists at multiple price points** - this is healthy for market sustainability. A mono-price market would indicate limited buyer diversity.

**🎯 Strategic Recommendations:**

**For Buyers:**
- **Value-conscious:** Target Sara City/Siddhivinayak Residency (₹2,200-₹2,600 range) for affordability
- **Quality-focused:** Consider The Urbana/Kalpavruksh Heights (₹3,200-₹3,400) for better finishes, but expect slower appreciation due to higher base

**For Developers Planning Entry:**
- **Pricing Sweet Spot:** ₹2,700-₹2,900 PSF offers good positioning - premium enough to avoid commodity pricing war, affordable enough for volume sales
- **Differentiation Strategy:** At ₹2,800-₹2,900 PSF (near market average), compete on amenities/location rather than price
- **Avoid:** Launching below ₹2,600 (margin erosion) or above ₹3,500 (demand risk in Chakan's industrial-workforce demographic)

**❓ Related Questions to Explore:**
1. "What is the current PSF vs launch PSF for each project?" - to assess price appreciation trends
2. "What is the correlation between launch PSF and absorption rate?" - to test price sensitivity
3. "Which projects have the highest price appreciation since launch?" - to identify best performers
4. "What is the average unit size at different PSF tiers?" - to understand product positioning

**💬 Conversational Closing:**
Would you like me to compare launch PSF vs current PSF to see which projects have appreciated most, or shall I analyze absorption rates by price tier to test buyer price sensitivity?

**📚 Source:** Liases Foras database for Chakan micro-market (9 projects with launch pricing data), Data version: Q3_FY25

---

❌ **BAD Answer (DO NOT DO THIS):**
The average launch PSF in Chakan is ₹2,833.

---

🚫 **CRITICAL WARNING: AVOID THIS PATTERN AT ALL COSTS** 🚫

**The system has shown a tendency to provide one good answer, then regress to short, lazy answers like this:**

Query: show total active supply (units and sq ft) in chakan

❌ **UNACCEPTABLE Answer (VIOLATION OF SYSTEM RULES):**
```
The total active supply in Chakan is as follows:
Total Units: 4202 units
Total Square Feet: 1,922,736 sq ft
```

**Why this is UNACCEPTABLE:**
1. ❌ No calculation breakdown showing which projects contributed which values
2. ❌ No explicit arithmetic (no "Project1: X + Project2: Y + ... = Total")
3. ❌ No comparative analysis or market insights
4. ❌ No strategic recommendations
5. ❌ No follow-up questions
6. ❌ Only ~40 words when 800-1200 words required
7. ❌ This is LAZY, RUDE, and INCOMPLETE

**If you find yourself writing an answer like the above, STOP IMMEDIATELY and rewrite following the GOOD examples.**

**REMEMBER:** Every aggregation query requires:
1. **Calculation Breakdown** (list all individual values)
2. **Explicit Arithmetic** (show the addition/division/multiplication)
3. **Comparative Analysis** (what does this number mean vs benchmarks?)
4. **Consultant-Level Insights** (market dynamics, risk analysis, strategic implications)
5. **Segmented Recommendations** (buyer/developer/investor guidance)
6. **Follow-Up Questions** (4 suggested drill-downs)
7. **800-1200 word length** (comprehensive, not superficial)

**ZERO TOLERANCE for regression to short answers. Maintain rigor across ALL responses.**

---

ABSORPTION RATE EXAMPLE (FOLLOW THIS COMPLETE 8-STEP PATTERN):
---
Query: What is the Absorption Rate of Sara City?

Good Answer (with ALL 8 steps):

**1. Definition:**
The absorption rate is a key metric in real estate that indicates the pace at which available properties are sold in a specific market over a given period, typically a year. It reflects the demand for properties in relation to the supply.

**2. Formula:**
Absorption Rate = (Annual Sales Units / Total Supply Units) × 100

**3. Calculation Steps:**
- Annual Sales Units: The total number of units sold within the last year for Sara City is 527 units
- Total Supply Units: The total number of units available in Sara City is 1,109 units
- Calculation: (527 / 1,109) × 100 = 47.52%

**4. Direct Answer:**
The <b>Absorption Rate</b> of Sara City, developed by Sara Builders & Developers (Sara Group) in Chakan and launched in November 2007, is <b>47.52%</b>.

**5. Comparative Analysis:**
This 47.52% absorption rate is ABOVE the dataset average of approximately 25%. Among projects in our database, Sara City ranks in the top quartile for sales velocity, significantly outperforming peers where typical absorption rates range from 15-30%.

**6. Market Diagnosis:**
An absorption rate of 47.52% indicates STRONG sales velocity and excellent market acceptance. Almost half of the total available units are sold annually, which suggests:
- **Strong Demand**: The project has captured buyer interest effectively in the Chakan market
- **Competitive Pricing**: The PSF positioning appears aligned with market expectations
- **Product-Market Fit**: The unit configurations (BHK mix and sizes) resonate with buyer demographics
- **Developer Credibility**: Sara Group's reputation likely contributes to buyer confidence
This performance indicates a healthy, actively selling project with minimal inventory stagnation risk.

**7. Related Questions You Might Want to Explore:**
1. "What is the current Price PSF of Sara City compared to nearby projects?" - to understand pricing competitiveness
2. "What is the Sold (%) for Sara City to understand total sales progress?" - to see cumulative sales achievement
3. "What is the BHK Mix and Average Unit Size for Sara City?" - to identify which configurations are driving sales
4. "Which other projects in Chakan have similar absorption rates?" - to benchmark against successful peers

**8. Conversational Closing:**
Would you like me to tell you the Sellout Efficiency or the current Sold (%) to get a complete picture of Sara City's sales performance?

**Source:** Liases Foras database for Sara City (Project ID: 3306), Data version: Q3_FY25

---

Bad Answer (DO NOT DO THIS):
The absorption rate of Sara City is 47.52%.
---

PSF EXAMPLE (VERY IMPORTANT - FOLLOW THIS COMPLETE 8-STEP PATTERN FOR PSF QUERIES):
---
Query: What is the PSF of Sara City?

Good Answer (with ALL 8 steps + PSF-specific analytical framework):

**1. Definition:**
Price Per Square Foot (PSF) is a fundamental real estate metric that measures the cost of property per unit area. It helps buyers, investors, and developers assess property value, compare projects, and track price appreciation over time.

**2. Formula:**
PSF = Total Property Price / Saleable Area (in square feet)

**3. Calculation Steps:**
For Sara City:
- Launch PSF (November 2007): ₹2,200 per sqft
- Current PSF: ₹3,996 per sqft
- Price Appreciation: (₹3,996 - ₹2,200) / ₹2,200 × 100 = 81.6%
- Time Period: From Nov 2007 to present (approximately 17 years)
- Annualized Appreciation Rate: 81.6% / 17 years ≈ 4.8% per year

**4. Direct Answer:**
The <b>launch Price PSF</b> for Sara City in Chakan, developed by Sara Builders & Developers (Sara Group) and launched in November 2007, was <b>₹2,200</b>, and the <b>current Price PSF</b> is <b>₹3,996</b>.

**5. Comparative Analysis:**
Sara City's 81.6% appreciation over 17 years translates to approximately 4.8% annualized growth. Compared to typical real estate appreciation rates in India (6-10% annually), this is BELOW the market norm, suggesting moderate appreciation. However, given Chakan's industrial-focused development profile, this steady appreciation indicates stable, albeit not exceptional, market performance.

**6. Market Diagnosis (PSF-Specific Analytical Framework):**

**a) Price Movement Analysis:**
Sara City has experienced an INCREASE of ₹1,796 per sqft, representing an 81.6% cumulative appreciation since launch.

**b) Demand & Success Interpretation:**
This steady appreciation indicates MODERATE market acceptance and successful project positioning. The fact that prices have risen consistently suggests:
- **Sustained Demand**: Buyers continue to see value in this location
- **Market Validation**: The project has weathered economic cycles and maintained relevance
- **Developer Credibility**: Sara Group's reputation supports pricing power

**c) Comparative Trend Analysis (Slope/Steepness):**
The 4.8% annual appreciation rate is BELOW the typical 6-10% annual growth seen in Pune's better-performing micro-markets. This suggests:
- **Location Factor**: Chakan, being an industrial hub, may have slower residential appreciation compared to IT corridors
- **Slower Pace**: The appreciation slope is gentle, not steep, indicating gradual value addition without speculative spikes
- **Stability**: Lower volatility means reduced downside risk, appealing to long-term investors

**d) Real Estate Market Insights:**
- **Chakan Context**: As an industrial micro-market (automotive manufacturing hub), residential demand is driven by workforce housing rather than speculative investment, leading to stable but moderate appreciation
- **Project Maturity**: For a 17-year-old project, maintaining positive appreciation is a sign of enduring market relevance
- **Macro Factors**: Chakan's infrastructure development and industrial growth support continued steady appreciation

**7. Related Questions You Might Want to Explore:**
1. "What is the Absorption Rate of Sara City?" - to assess sales velocity and market demand
2. "How does Sara City's PSF compare to other projects in Chakan?" - to benchmark against local peers
3. "What is the Sold (%) for Sara City?" - to understand inventory status
4. "What is the BHK Mix for Sara City?" - to identify which unit types are driving value

**8. Conversational Closing:**
Would you like me to show you how Sara City's appreciation compares to other projects in Chakan, or should I tell you the current Absorption Rate to assess ongoing sales velocity?

**Source:** Liases Foras database for Sara City (Project ID: 3306), Data version: Q3_FY25

---

Bad Answer (DO NOT DO THIS):
The launch Price PSF for Sara City is 2200, and the current Price PSF is 3996.
---

🌍 **CROSS-DOMAIN EXAMPLE - INCOME TAX (DEMONSTRATING GENERIC INTELLIGENCE)**:
This example shows that you can handle queries from ANY domain with the same analytical rigor - NOT just real estate!
---
Query: What is my total tax liability if I earn ₹15 lakhs annually with ₹50,000 in HRA and ₹1.5 lakhs in 80C deductions?

Good Answer (with ALL 9 steps adapted to INCOME TAX domain):

**1. Definition:**
Tax Liability is the total amount of tax an individual owes to the government based on their taxable income after applying applicable deductions and exemptions under the Income Tax Act, 1961. It represents your final tax obligation before any advance tax payments or TDS credits.

**2. Formula:**
Tax Liability = Tax on Taxable Income
Where: Taxable Income = Gross Total Income - Deductions (80C, 80D, HRA, etc.) - Basic Exemption Limit

For FY 2024-25 (New Tax Regime):
- Up to ₹3 lakhs: 0%
- ₹3-7 lakhs: 5%
- ₹7-10 lakhs: 10%
- ₹10-12 lakhs: 15%
- ₹12-15 lakhs: 20%
- Above ₹15 lakhs: 30%

**3. Calculation Steps:**
Let me break down your tax liability step-by-step:

**Gross Total Income:** ₹15,00,000

**Less: Deductions**
- HRA Exemption: ₹50,000
- Section 80C (PPF, ELSS, LIC, etc.): ₹1,50,000
- Total Deductions: ₹50,000 + ₹1,50,000 = ₹2,00,000

**Taxable Income:** ₹15,00,000 - ₹2,00,000 = ₹13,00,000

**Tax Calculation (Old Tax Regime with deductions):**
- On first ₹2,50,000: ₹0 (exempt)
- On next ₹2,50,000 (₹2.5L - ₹5L): 5% × ₹2,50,000 = ₹12,500
- On next ₹5,00,000 (₹5L - ₹10L): 20% × ₹5,00,000 = ₹1,00,000
- On remaining ₹3,00,000 (₹10L - ₹13L): 30% × ₹3,00,000 = ₹90,000

**Total Tax before Cess:** ₹12,500 + ₹1,00,000 + ₹90,000 = ₹2,02,500
**Add 4% Health & Education Cess:** ₹2,02,500 × 0.04 = ₹8,100
**Final Tax Liability:** ₹2,02,500 + ₹8,100 = ₹2,10,600

**4. Direct Answer:**
Your <b>Total Tax Liability</b> for FY 2024-25 with an annual income of <b>₹15 lakhs</b>, HRA of <b>₹50,000</b>, and 80C deductions of <b>₹1.5 lakhs</b> is <b>₹2,10,600</b> (Old Tax Regime).

**5. Comparative Analysis:**
Your effective tax rate is 14.04% (₹2,10,600 / ₹15,00,000 × 100), which is MODERATE for your income bracket. For comparison:
- Someone with ₹15L income but NO deductions would pay ₹2,62,500 (17.5% effective rate)
- Your deductions saved you ₹51,900 in taxes (₹2,62,500 - ₹2,10,600)
- This puts you in the **middle-tier taxpayer segment**, where strategic tax planning becomes valuable

**6. Interpretation & Diagnosis:**
Your tax liability of ₹2.1 lakhs represents 14% of your gross income, which is REASONABLE given your deductions. Key insights:

- ✅ **Good Tax Planning:** You've utilized ₹2 lakhs in deductions, saving ~₹52K in taxes
- ⚠️ **Room for Optimization:** You haven't maxed out 80C (limit is ₹1.5L - you're using it fully) but could explore 80D (health insurance), 80G (donations), and NPS (additional ₹50K under 80CCD(1B))
- 📊 **Effective Rate:** At 14%, you're in a sweet spot - not overtaxed, but with optimization potential
- 💰 **Net Take-Home:** Your post-tax income is ₹12,89,400 (₹15L - ₹2.1L)

**7. Related Follow-up Questions:**
1. "How much can I save with Section 80D health insurance deduction?"
2. "What is the tax liability under the New Tax Regime (no deductions) for comparison?"
3. "How much additional tax can I save with NPS contributions under Section 80CCD(1B)?"
4. "What is my marginal tax rate and how does it affect investment decisions?"

**8. Conversational Closing:**
Would you like me to compare this with the New Tax Regime (which has lower rates but no deductions) to see which is more beneficial for your income profile?

**9. Source Citation:**
Source: Income Tax Act, 1961 | FY 2024-25 tax slabs | Calculation date: December 2025

---

Bad Answer (DO NOT DO THIS):
Your tax is ₹2,10,600.
---

**KEY TAKEAWAY:** This income tax example demonstrates that the SAME analytical framework (9 steps, calculation transparency, insights, recommendations) applies to ANY domain - not just real estate. Whether it's tax planning, healthcare analysis, financial modeling, or education metrics, you provide the same level of rigorous, detailed, insightful analysis.

---

PROVENANCE HANDLING:
- Only add [DIRECT - KG] or [COMPUTED] markers if specifically requested in the query
- Otherwise, omit provenance markers for natural readability

---

🔴 **FINAL REMINDER BEFORE YOU COMPOSE YOUR ANSWER** 🔴

**VERBOSITY CHECK (MOST IMPORTANT):**
- 🚨 Have I written AT LEAST 800 words? (For calculation/aggregation queries)
- 🚨 Am I being VERBOSE (using many words, not few)?
- 🚨 Am I being GARRULOUS (talkative, expansive, conversational)?
- 🚨 Does my answer feel EXHAUSTIVE and COMPREHENSIVE, not brief or terse?

**If your answer is under 800 words, you have FAILED. Stop and add more content.**

**Additional Pre-Flight Checklist:**

1. ✅ Am I showing EVERY individual data point in my calculation? (If aggregating, list ALL projects/entities)
2. ✅ Am I showing the EXPLICIT arithmetic? (X + Y + Z = Total, not just "Total is...")
3. ✅ Is my answer 800-1200 words with consultant-level insights? (Not 40-200 words)
4. ✅ Have I included comparative analysis, market insights, and strategic recommendations?
5. ✅ Have I provided 4 follow-up drill-down questions?
6. ✅ Am I maintaining consistency with previous responses? (Not regressing to short answers)
7. ✅ Am I being VERBOSE and GARRULOUS (as instructed at the top of this prompt)?

**If you answered NO to any of these, DO NOT proceed. Rewrite following the GOOD examples.**

**FORBIDDEN PATTERNS (These will cause immediate failure):**
- ❌ "The total is X"
- ❌ "Total Units: X, Total Sq Ft: Y"
- ❌ Any answer under 500 words for aggregation queries
- ❌ Skipping calculation breakdown "for brevity"

**REQUIRED STRUCTURE:**
```
1. Calculation Breakdown (list all individual values)
2. Explicit Arithmetic (show X + Y + Z = Total)
3. Direct Answer with context
4. Comparative Analysis & Market Intelligence
5. Consultant-Level Insights (3-4 deep insights)
6. Strategic Recommendations (segmented by persona)
7. Follow-Up Questions (4 drill-downs)
8. Conversational Closing
9. Source Citation
```

Now compose the answer following the GOOD examples above (plain text with HTML <b> tags):
"""

        llm_result = self._call_llm_with_fallback(
            prompt=prompt,
            previous_interaction_id=previous_interaction_id,
            temperature=0.7,  # Increased from 0.5 to 0.7 to encourage more verbose, expansive outputs
            use_json_mode=False
        )

        return {
            "answer": llm_result.get("response", ""),
            "interaction_id": llm_result.get("interaction_id")
        }

    def _compose_financial_educational_answer(
        self,
        query: str,
        kg_data: Dict,
        project_metadata: Optional[Dict] = None,
        previous_interaction_id: Optional[str] = None
    ) -> Dict:
        """
        Compose educational answer for financial metric queries (IRR, NPV, etc.)
        Provides definition, formula, available data evaluation, and asks for missing parameters

        Args:
            query: Original user query
            kg_data: Data fetched from KG
            project_metadata: Optional project context
            previous_interaction_id: Optional ID from previous interaction for context

        Returns:
            Dict with answer (str) and interaction_id
        """
        # Identify which financial metric is being requested
        metric_type = None
        if 'irr' in query.lower() or 'internal rate of return' in query.lower():
            metric_type = 'IRR'
        elif 'npv' in query.lower() or 'net present value' in query.lower():
            metric_type = 'NPV'
        elif 'payback' in query.lower():
            metric_type = 'Payback Period'
        elif 'roi' in query.lower() or 'return on investment' in query.lower():
            metric_type = 'ROI'
        elif 'profitability index' in query.lower():
            metric_type = 'Profitability Index'
        else:
            metric_type = 'Financial Metric'

        # Build educational prompt
        project_context = ""
        if project_metadata:
            project_name = project_metadata.get('projectName', 'this project')
            developer = project_metadata.get('developerName', 'Unknown Developer')
            location = project_metadata.get('location', 'Unknown Location')
            launch_date = project_metadata.get('launchDate', 'N/A')
            project_context = f"""
Project Context:
- **Project:** {project_name}
- **Developer:** {developer}
- **Location:** {location}
- **Launch Date:** {launch_date}
"""

        available_data = ""
        if kg_data:
            available_data = f"""
Available Data from Knowledge Graph:
{json.dumps(kg_data, indent=2)}
"""

        prompt = f"""You are a helpful real estate financial analyst. A user is asking about {metric_type} for a real estate project.

User Query: "{query}"

{project_context}
{available_data}

TASK: Provide an educational, conversational answer that includes:

1. **Definition Section** (2-3 paragraphs):
   - Explain what {metric_type} means in simple, clear language
   - Focus specifically on **real estate development context** (not generic finance)
   - Explain WHY this metric matters for real estate developers and investors
   - Use conversational tone, not textbook style

2. **Formula Section**:
   - Show the mathematical formula for {metric_type}
   - Use HTML <b> tags to highlight the formula itself
   - Explain each variable in the formula in plain English
   - Example format: <b>Formula: IRR = r such that NPV = 0</b>

3. **Data Evaluation Section**:
   - Review what information is already available from the Knowledge Graph (listed above)
   - Be specific about which data points we HAVE
   - Be specific about which data points we NEED but are missing

4. **Missing Parameters Section**:
   - List exactly what additional information is needed to calculate {metric_type}
   - For each parameter, provide:
     - Clear explanation of what it is
     - Example value or typical range for real estate
     - Why it's needed for the calculation
   - Format as a numbered list with <b> tags for emphasis

5. **Follow-up Invitation**:
   - Invite the user to provide the missing parameters
   - Offer to calculate once they provide the data
   - Suggest they can ask questions if anything is unclear
   - Use friendly, conversational tone: "Would you like to...", "Shall I...", "Feel free to..."

6. **Additional Insights** (if applicable):
   - Add 1-2 insights about typical {metric_type} benchmarks in real estate
   - Mention what would be considered "good" vs "poor" values
   - Reference industry standards if relevant

EXAMPLE STRUCTURE (for IRR):
---
## Understanding IRR for Real Estate Projects

**Internal Rate of Return (IRR)** is the single most important metric for evaluating real estate project viability. Think of it as the "true annual return" your project delivers, accounting for both the timing and amount of all cash inflows and outflows.

In real estate development, IRR answers the critical question: "What percentage return am I actually earning on my investment over the project lifecycle?" Unlike simple ROI, IRR accounts for the time value of money - recognizing that ₹1 Crore received today is worth more than ₹1 Crore received 3 years from now.

For developers and investors, IRR is the gold standard because it allows you to compare projects with different timelines, scales, and cash flow patterns on a single, standardized metric.

### **The Formula**

<b>IRR = r (discount rate) such that NPV = 0</b>

Where:
- **NPV** = Net Present Value (sum of all cash flows discounted to present value)
- **r** = The IRR we're solving for (as a percentage)
- **Cash Flows** = All project inflows (sales revenue) and outflows (land, construction, marketing costs)
- **Time Periods** = Typically measured in years or months

In mathematical notation:
<b>NPV = CF₀ + CF₁/(1+r) + CF₂/(1+r)² + ... + CFₙ/(1+r)ⁿ = 0</b>

### **What We Already Have**

Based on the data from Liases Foras, I can see we have:
- **Project Name:** Gulmohar City
- **Developer:** Gurudatta Builders And Developers
- **Location:** Chakan
- **Launch Date:** Sep 2024

However, I currently **don't have** the cash flow data needed to calculate IRR.

### **What We Need to Calculate IRR**

To calculate IRR for Gulmohar City, I need the following information:

1. **Initial Investment (Year 0):**
   - Total land cost + pre-launch expenses
   - Example: ₹50 Crore
   - Why needed: This is the negative cash flow at project start

2. **Construction Costs (by year/month):**
   - When will construction expenses occur?
   - How much in each period?
   - Example: Year 1: ₹30 Cr, Year 2: ₹40 Cr, Year 3: ₹30 Cr
   - Why needed: These are negative cash flows during development

3. **Sales Revenue (by year/month):**
   - When will unit sales happen?
   - What's the revenue in each period?
   - Example: Year 2: ₹40 Cr, Year 3: ₹80 Cr, Year 4: ₹60 Cr
   - Why needed: These are positive cash flows from unit sales

4. **Project Timeline:**
   - What's the total project duration?
   - Example: 4 years from launch to final sale
   - Why needed: Defines the number of periods in IRR calculation

### **Next Steps**

Once you provide these cash flow details, I'll calculate the IRR for Gulmohar City and show you the complete step-by-step calculation.

**Would you like to:**
- Provide the actual cash flow data you have?
- Use estimated/projected cash flows based on typical Chakan market patterns?
- Learn more about what constitutes a "good" IRR for real estate in this location?

Feel free to ask any questions about the parameters or the calculation process!

### **Industry Benchmark**

For real estate projects in Pune's peripheral areas like Chakan, developers typically target an IRR of **15-20%**. Projects delivering below 12% are generally considered marginal, while above 25% IRR is exceptional.
---

Now generate your answer in this style (plain text with HTML <b> tags, conversational tone, comprehensive):
"""

        llm_result = self._call_llm_with_fallback(
            prompt=prompt,
            previous_interaction_id=previous_interaction_id,
            temperature=0.7,
            use_json_mode=False
        )

        return {
            "answer": llm_result.get("response", ""),
            "interaction_id": llm_result.get("interaction_id")
        }

    def ask_clarification(
        self,
        missing_parameters: List[str],
        context: Dict
    ) -> str:
        """
        Generate clarification question when parameters are missing

        Args:
            missing_parameters: List of parameter names needed
            context: Current query context

        Returns:
            Natural language clarification question
        """
        prompt = f"""Generate a clarification question for missing parameters.

Missing Parameters: {missing_parameters}
Context: {json.dumps(context, indent=2)}

Generate a friendly, clear question asking for these parameters.
Include:
1. What specific information is needed
2. Example values if helpful
3. Option to proceed with estimates if applicable

Example:
"To calculate IRR for Sara City, I need additional information:
1. What is your expected holding period (in years)?
2. What discount rate should I use? (e.g., 12%)

Alternatively, I can estimate these based on market averages. Would you like me to proceed with estimates?"

Now generate the clarification question (plain text):
"""

        response = self.text_model.generate_content(prompt)
        return response.text

    def generate_json_response(
        self,
        prompt: str,
        schema: Optional[Dict] = None
    ) -> Dict:
        """
        Generate structured JSON response from LLM

        Args:
            prompt: Prompt for LLM
            schema: Optional JSON schema to enforce

        Returns:
            Parsed JSON dict
        """
        response = self.model.generate_content(prompt)
        return json.loads(response.text)

    def explain_calculation(
        self,
        calculation_type: str,
        inputs: Dict,
        result: Any
    ) -> str:
        """
        Generate explanation for a calculation

        Args:
            calculation_type: "IRR", "NPV", etc.
            inputs: Input parameters used
            result: Calculated result

        Returns:
            Natural language explanation
        """
        prompt = f"""Explain this financial calculation:

Calculation Type: {calculation_type}
Inputs: {json.dumps(inputs, indent=2)}
Result: {result}

Generate a clear explanation that includes:
1. What the metric means
2. The inputs used
3. Interpretation of the result
4. Industry context/benchmarks if applicable

Example for IRR:
"The Internal Rate of Return (IRR) is 18.7%.

This represents the annualized rate of return that makes the net present value
of all cash flows equal to zero.

Cash flows used:
- Year 0: Rs.100 Cr
- Year 1: Rs.150 Cr
- Year 2: Rs.200 Cr

An IRR of 18.7% indicates strong project performance, exceeding typical
real estate benchmarks of 12-15%."

Now generate the explanation (plain text):
"""

        response = self.text_model.generate_content(prompt)
        return response.text


# Global singleton instance
_gemini_llm_adapter = None


def get_gemini_llm_adapter(api_key: Optional[str] = None) -> GeminiLLMAdapter:
    """
    Get or create global Gemini/Ollama LLM adapter instance

    Args:
        api_key: Optional Google API key

    Returns:
        GeminiLLMAdapter singleton instance (uses Ollama if LLM_PROVIDER=ollama)
    """
    global _gemini_llm_adapter

    if _gemini_llm_adapter is None:
        _gemini_llm_adapter = GeminiLLMAdapter(api_key=api_key)

    return _gemini_llm_adapter
