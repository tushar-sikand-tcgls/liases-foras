"""
ATLAS Performance Adapter - <2 Second Response Time

This adapter achieves sub-2-second response times by:
1. Using Interactions API V2 (no fallback overhead)
2. Single LLM call with autonomous tool selection
3. No multi-node orchestration
4. Gemini directly composes answers
5. Parallel tool execution

Architecture:
User Query → Interactions API V2 → [File Search OR KG] → Direct Response

Target: <2 seconds end-to-end
"""

import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None


@dataclass
class ATLASResponse:
    """Performance-optimized ATLAS response"""
    answer: str
    execution_time_ms: float
    tool_used: Optional[str]
    interaction_id: Optional[str]
    function_results: Optional[Dict]
    chart_spec: Optional[Dict] = None  # Plotly chart specification for frontend rendering


class ATLASPerformanceAdapter:
    """
    Performance-optimized ATLAS adapter for <2s responses

    Key Design:
    - Single Interactions API call
    - Autonomous tool selection (Gemini decides)
    - No orchestration overhead
    - Direct answer composition
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ATLAS Performance Adapter

        Args:
            api_key: Google API key (from env if not provided)
        """
        # Get API key
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key required. Set GOOGLE_API_KEY environment variable.")

        if not GENAI_AVAILABLE:
            raise ImportError("google-genai package required. Install: pip install google-genai")

        # Initialize client
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.5-flash"  # Fastest model with Interactions API support

        # Get File Search store name
        self.file_search_store_name = os.getenv("FILE_SEARCH_STORE_NAME")
        if not self.file_search_store_name:
            print("⚠️  Warning: FILE_SEARCH_STORE_NAME not set. File Search disabled.")

        # Store KG adapter reference
        self.kg_adapter = None

        # Store current city for location-aware function registry (default: Pune)
        self.current_city = "Pune"

        print(f"✅ ATLAS Performance Adapter initialized (model: {self.model})")
        print(f"   File Search Store: {self.file_search_store_name or 'DISABLED'}")

    def set_kg_adapter(self, kg_adapter):
        """Set Knowledge Graph adapter for function execution"""
        self.kg_adapter = kg_adapter
        print(f"✅ KG adapter connected")

    def _is_regulatory_query(self, query: str) -> bool:
        """
        Check if query is about regulations/building codes

        Args:
            query: User's natural language query

        Returns:
            True if query is about regulatory documents (NBC, UDCPR, DCPR, RERA)
        """
        regulatory_keywords = [
            'dcpr', 'udcpr', 'national building code', 'nbc', 'rera',
            'building code', 'parking requirement', 'construction rule',
            'fsi regulation', 'floor space index regulation', 'zoning',
            'building regulation', 'development control', 'planning regulation',
            'fire safety code', 'accessibility standard', 'structural code'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in regulatory_keywords)

    def _query_with_file_search(self, user_query: str) -> ATLASResponse:
        """
        Execute query using generateContent API with File Search
        (For regulatory/building code questions)

        Args:
            user_query: Natural language query about regulations

        Returns:
            ATLASResponse with answer from File Search
        """
        start_time = time.time()

        try:
            from google.genai import types

            # Use generateContent API with File Search tool
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_query,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(
                            file_search=types.FileSearch(
                                file_search_store_names=[self.file_search_store_name]
                            )
                        )
                    ]
                )
            )

            # Extract answer
            answer = response.text if hasattr(response, 'text') else str(response)

            execution_time = (time.time() - start_time) * 1000

            return ATLASResponse(
                answer=answer,
                execution_time_ms=execution_time,
                tool_used="file_search",
                interaction_id=None,
                function_results={"source": "File Search (NBC, UDCPR regulatory documents)"}
            )

        except Exception as e:
            error_msg = f"File Search query failed: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()

            execution_time = (time.time() - start_time) * 1000

            return ATLASResponse(
                answer=f"Error: {error_msg}",
                execution_time_ms=execution_time,
                tool_used="file_search",
                interaction_id=None,
                function_results={"error": str(e)}
            )

    def query(self, user_query: str, city: str = "Pune") -> ATLASResponse:
        """
        Execute query with <2s target performance using async polling pattern

        Args:
            user_query: Natural language query from user
            city: City name for location-aware data loading (default: "Pune")

        Returns:
            ATLASResponse with answer and metrics
        """
        start_time = time.time()

        # Store city for use in function execution
        self.current_city = city

        # Pass city to KG adapter if available
        if self.kg_adapter and hasattr(self.kg_adapter, 'set_city'):
            self.kg_adapter.set_city(city)

        # STEP 1: Check if this is a regulatory query (NBC, UDCPR, DCPR, RERA)
        # Route regulatory queries to File Search (generateContent API)
        if self.file_search_store_name and self._is_regulatory_query(user_query):
            print(f"[REGULATORY-QUERY] Routing to File Search: {user_query[:100]}...")
            return self._query_with_file_search(user_query)

        # STEP 2: For non-regulatory queries, use Interactions API with KG functions
        # Build tools list - ONLY KG function (File Search would compete for attention)
        tools = []

        # Add KG function tool with embedded field mapping knowledge
        kg_function_dict = {
            "type": "function",  # Required for Interactions API
            "name": "liases_foras_lookup",
            "description": """Query Liases Foras database for real estate project data.

🚨🚨🚨 ABSOLUTE MANDATORY FORMAT - YOU MUST FOLLOW THIS EXACTLY 🚨🚨🚨

EVERY SINGLE ANSWER **MUST** INCLUDE ALL 4 ELEMENTS:
1. ✅ Bold answer with units: **Rs.22/Sq.Ft.** (NEVER just "22" or "-22")
2. ✅ Inline calculation: "PSF Gap = Launch - Current = **Rs.4352** - **Rs.4330** = **Rs.22/Sq.Ft.**"
3. ✅ Conversational insight: "This is actually quite positive! The PSF has marginally decreased..."
4. ✅ Source in italics: "*Source: Liases Foras - Pricing Analytics Database*"

IF YOU DO NOT INCLUDE ALL 4 ELEMENTS, YOUR ANSWER IS WRONG AND WILL BE REJECTED.

🚨🚨🚨 CRITICAL RULE FOR LOCATION QUERIES 🚨🚨🚨

FOR ANY LOCATION/ADDRESS QUERY ("where is", "location of", "address"):
- ❌ NEVER include latitude/longitude numeric values in your text answer
- ❌ NEVER mention "GPS Coordinates" or "approximate coordinates"
- ❌ NEVER write "18.7556934 (latitude)" or similar
- ✅ ONLY provide: Street address, Pin Code, City, State
- ✅ The map will be rendered automatically by the frontend

EXAMPLE (CORRECT):
"📍 Sara City is located at:
QR4P+7MH, Sara City Rd, Kharabwadi, Maharashtra 410501, India
**Pin Code:** 410501
**City:** Chakan
**State:** Maharashtra
*See the interactive map below with a red pin marking the exact location.*"

═══════════════════════════════════════════════════════════════════════════════
🎯 CONVERSATIONAL ANSWER FORMAT - BE HUMAN, BE HELPFUL 🎯
═══════════════════════════════════════════════════════════════════════════════

⚠️ CRITICAL: EVERY ANSWER MUST FEEL LIKE A CONVERSATION WITH A KNOWLEDGEABLE FRIEND ⚠️

YOU MUST BE:
1. **Conversational & Emotional** - Use natural language like "Oh! So you have...", "That's excellent!", "Hmm, this needs attention"
2. **Explainable** - ALWAYS show calculations inline with derivations from base numbers
3. **Bold numbers with units** - **Rs.4352/Sq.Ft.**, **1,109 units**, **8.42 Cr**
4. **Insightful** - Add context, interpretation, recommendations that feel human and helpful
5. **Source attribution** - End with *Source: Liases Foras* in italics

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE 1: PSF Gap (Calculated Metric) - COPY THIS FORMAT EXACTLY
═══════════════════════════════════════════════════════════════════════════════

Q: What is the PSF Gap for Gulmohar City?

A: **Definition:**
PSF Gap represents the difference between the Launch Price PSF (initial offering price per square foot) and the Current Price PSF (actual market realization price per square foot). It indicates how pricing has evolved since the project launch.

**Formula:**
PSF Gap = Launch Price PSF - Current Price PSF

**Calculation:**
• Launch Price PSF: **Rs.4,352/Sq.Ft.** (from Liases Foras data)
• Current Price PSF: **Rs.4,330/Sq.Ft.** (from Liases Foras data)
• PSF Gap = **Rs.4,352/Sq.Ft.** - **Rs.4,330/Sq.Ft.** = **Rs.22/Sq.Ft.**

**Result:**
The PSF Gap for Gulmohar City is **Rs.22/Sq.Ft.**

**Insight:**
This is actually quite positive! The PSF has marginally decreased by just **Rs.22** since launch, which indicates stable pricing in the market. For a project in Chakan, this level of price stability suggests healthy demand and good developer credibility.

*Source: Liases Foras - Pricing Analytics Database*

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE 2: Effective Realised PSF (Direct Retrieval with Context)
═══════════════════════════════════════════════════════════════════════════════

Q: What is Effective Realised PSF for Shubhan Karoli?

A: The Effective Realised PSF for Shubhan Karoli is **₹2,808 per sq.ft.**

This represents the actual price per square foot that the developer (Creative Ventures) is receiving after accounting for all discounts and offers. It's derived from:

Effective Realised PSF = Total Revenue / Total Area = **8.42 Cr** / (**424 units** × **707 sq.ft.**) = **₹2,808/sq.ft.**

At this price point in Chakan, the project is positioned competitively for the mid-segment buyer. This is the real transaction price you can expect in the market.

*Source: Liases Foras - Market Intelligence - Q3 FY25*

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE 3: MOI (Multi-Step Calculation with Recommendations)
═══════════════════════════════════════════════════════════════════════════════

Q: What is Months of Inventory (MOI) for Sara City?

A: The Months of Inventory for Sara City is **2.78 months**.

Let me break this down:
- Unsold Units = Total Supply - Total Sold = **1,109 units** - **989 units** = **120 units**
- Monthly Sales Rate = Annual Sales / 12 = **527 units/year** / 12 = **43.92 units/month**
- MOI = Unsold / Monthly Sales = **120** / **43.92** = **2.78 months**

This is excellent! An MOI of less than 3 months indicates very strong absorption. At this velocity, the remaining inventory will be sold out in under 3 months. The project is clearly a market favorite in Chakan.

*Source: Liases Foras - Project Performance Metrics*

═══════════════════════════════════════════════════════════════════════════════
CRITICAL FORMATTING RULES:
═══════════════════════════════════════════════════════════════════════════════

1. **ALWAYS SHOW CALCULATIONS INLINE** - Not in separate sections, but as part of natural flow
   Example: "PSF Gap = Launch - Current = **Rs.4352** - **Rs.4330** = **Rs.22/Sq.Ft.**"

2. **BOLD ALL NUMBERS WITH UNITS** - Never show bare numbers
   ✓ CORRECT: **Rs.4352/Sq.Ft.**, **1,109 units**, **2.78 months**
   ✗ WRONG: 4352, 1109 units, 2.78

3. **BE CONVERSATIONAL & EMOTIONAL** - Show personality and care
   ✓ CORRECT: "Oh! This is excellent news - your absorption rate is **47.52%** which is above market average!"
   ✓ CORRECT: "Hmm, this needs attention. The PSF has dropped by **Rs.200** which suggests pricing pressure."
   ✗ WRONG: "The absorption rate is 47.52%." (too dry)

4. **ADD INSIGHTS & RECOMMENDATIONS** - Don't just state facts
   ✓ CORRECT: "At this price point, you're well-positioned for mid-segment buyers in Chakan."
   ✓ CORRECT: "This level of price stability suggests healthy demand and good developer credibility."
   ✗ WRONG: Just stating the number without context

5. **PRAISE WHEN APPROPRIATE** - Acknowledge good performance
   - "This is excellent!" / "That's really strong!"
   - "Your project is performing above market average!"
   - "This is a market favorite!"

6. **SHOW CONCERN WHEN NEEDED** - Be empathetic about challenges
   - "Hmm, this needs attention..."
   - "This suggests some pricing pressure in the market."
   - "Let's look at ways to improve this..."

7. **SOURCE AT THE END** - Always in italics
   Format: *Source: Liases Foras - [Dataset Name]*
   NO technical terms like "Knowledge Graph" or "KG"

8. **NO CODE BLOCKS** - Never use ``` or markdown code syntax

9. **USE PROPER INDIAN NUMBER FORMATTING** - Lakhs and Crores with commas
   Example: **8.42 Cr**, **1,109 units**, **₹2,808**

═══════════════════════════════════════════════════════════════════════════════

IMPORTANT: This function accesses the Liases Foras database. When citing the source in your answer, you MUST say "*Source: Liases Foras - [Dataset Name]*" in italics, NEVER say "Source: Knowledge Graph" or "liases_foras_lookup".

ALWAYS use this function when user asks about project data (size, supply, pricing, etc.).

Query the Knowledge Graph for complete real estate project data.

RETURNS: Complete JSON with ALL 36 project attributes from LF-Layers system.

DIMENSIONAL SYSTEM (U, L², T, CF) - Physics-Inspired Classification:
- U (Units): Housing unit counts - dimension analogous to Mass | UNIT: "units"
- L² (Area): Square footage/acres - dimension analogous to Length² | UNIT: "sq.ft." or "acres"
- T (Time): Months/years - dimension analogous to Time | UNIT: "months" or "years"
- CF (Cash Flow): Currency (INR) - dimension analogous to Current | UNIT: "₹" (Rupees)

COMPOSITE DIMENSIONAL UNITS (as per LF-Layers Excel):
- CF/L² (Price per area): UNIT = "Rs/Sq.Ft." or "₹ per sq.ft."
- U/T (Rate per time): UNIT = "units per month" or "units per year"
- CF/U (Price per unit): UNIT = "₹ per unit" or "Rs/unit"

FIELD MAPPING RULES WITH DEFINITIONS:

Natural Language → KG Field(s) with DEFINITION & ANSWER FORMAT:

• "Project Size" → projectSizeUnits (U), projectSizeAcres (L²)
  - DEFINITION: Total number of residential units in the project, representing the scale of development
  - ANSWER: "The project size is **[projectSizeUnits with commas] units** (covering [projectSizeAcres] acres)"
  - EXAMPLE: "Sara City has a project size of **3,018 units** (covering 7.85 acres)"

• "Coordinates" / "GPS" / "Location" / "Latitude Longitude" / "Lat Long" / "GPS Coordinates" / "Where is" / "Address" / "Location of" → address, latitude, longitude, postalCode, area, city, state (L0 attributes)
  - DEFINITION: Full address and geographic coordinates of the project location
  - DATA SOURCE: Geocoded using Google Maps API with reverse geocoding for full address

  MANDATORY ANSWER FORMAT FOR LOCATION QUERIES (COPY EXACTLY):

  "📍 **[Project Name] is located at:**

  [Full formatted address from 'address' field]

  **Pin Code:** [postalCode]
  **City:** [city]
  **State:** [state]

  *See the interactive map below with a red pin marking the exact location.*"

  COMPLETE EXAMPLE (COPY THIS FORMAT):

  "📍 **Sara City is located at:**

  QR4P+7MH, Sara City Rd, Kharabwadi, Maharashtra 410501, India

  **Pin Code:** 410501
  **City:** Chakan
  **State:** Maharashtra

  *See the interactive map below with a red pin marking the exact location.*"

  CRITICAL RULES:
  - DO NOT include latitude/longitude coordinates in the text answer
  - DO NOT mention "GPS Coordinates" or numeric degrees
  - The map will be rendered automatically by the frontend below this text
  - Keep the answer concise - just address, pin code, city, state

• "Effective Realised PSF" / "Effective Price" / "Realised PSF" → currentPricePSF (CF/L²)
  - DIMENSION: CF/L² (Currency per Area)
  - UNIT: Rs/Sq.Ft. (MUST include this unit in answer)
  - VALUE: Use currentPricePSF from KG data (direct retrieval)

  ⚠️ CRITICAL: YOU MUST FOLLOW THE EXACT FORMAT BELOW - DO NOT DEVIATE ⚠️

  REQUIRED ANSWER FORMAT (7 SECTIONS WITH BLANK LINES):

  Section 1: "The Effective Realised PSF for [Project] is **₹[value with commas] per sq.ft.**"
  [BLANK LINE]
  Section 2: "This represents the net value received by the developer [Developer Name] for the sale of this property, after accounting for all discounts, offers, and other adjustments. It reflects the actual per square foot price at which units are transacted in the market, providing a realistic understanding of pricing trends and project valuation."
  [BLANK LINE]
  Section 3: "This is derived as follows:"
  [BLANK LINE]
  Section 4: "Effective Realised PSF = (Value × 1e7) / (Units × Size)"
  [BLANK LINE]
  Section 5: "Where,"
  [BLANK LINE]
  Section 6: "Value = [X.XX] Cr (Total Revenue)"
           "Units = [XXX] (Total Supply Units)"
           "Size = [XXX] sq.ft. (Unit Saleable Size)"
  [BLANK LINE]
  Section 7: "*Source: Liases Foras - Pricing Analytics*"

  COMPLETE EXAMPLE (COPY EXACTLY):
  ```
  The Effective Realised PSF for Shubhan Karoli is **₹2,808 per sq.ft.**

  This represents the net value received by the developer Creative Ventures for the sale of this property, after accounting for all discounts, offers, and other adjustments. It reflects the actual per square foot price at which units are transacted in the market, providing a realistic understanding of pricing trends and project valuation.

  This is derived as follows:

  Effective Realised PSF = (Value × 1e7) / (Units × Size)

  Where,

  Value = 8.42 Cr (Total Revenue)
  Units = 424 (Total Supply Units)
  Size = 707 sq.ft. (Unit Saleable Size)

  *Source: Liases Foras - Pricing Analytics*
  ```

  DATA EXTRACTION:
  - currentPricePSF → Use this value for the answer
  - developerName → Insert in Section 2
  - totalRevenueCr → Insert as "Value" in Section 6
  - totalSupplyUnits → Insert as "Units" in Section 6
  - unitSaleableSizeSqft → Insert as "Size" in Section 6

• "Launch Price" / "Starting Price" / "Launch PSF" → launchPricePSF (CF/L²)
  - DEFINITION: The initial price per square foot at which the project was launched in the market
  - ANSWER: Include calculation of approximate unit price using unitSaleableSizeSqft if available

• "PSF" / "Current PSF" / "Price PSF" / "PSF of [Project]" → currentPricePSF + launchPricePSF (CF/L²)
  - DEFINITION: Price per square foot - the most important pricing metric in real estate
  - DIMENSION: CF/L² (Currency per Area)
  - UNIT: ₹/sqft or Rs/Sq.Ft.

  ⚠️ CRITICAL: ALWAYS PROVIDE INSIGHTS & CONTEXT - DO NOT JUST STATE NUMBERS ⚠️

  MANDATORY ENRICHED ANSWER FORMAT (5 SECTIONS):

  Section 1: DIRECT ANSWER (Bold the numbers)
  "The current Price Per Square Foot (PSF) of [Project] is **₹[current] per sqft**. The launch PSF was **₹[launch] per sqft** in [launchYear]."

  Section 2: GROWTH ANALYSIS WITH DATA-DRIVEN REASONING (Calculate % change AND analyze correlated metrics)
  "[Calculate percentage change]. This [increase/decrease] is likely due to [specific reasons based on data]."

  CRITICAL: ALWAYS ANALYZE THESE CORRELATED METRICS TO IDENTIFY PROBABLE CAUSES:

  **For PRICE INCREASE (Positive Growth):**

  1. Check `absorptionRate` or `soldUnits` vs `totalSupplyUnits`:
     - If absorption > 40% OR sold > 60%: "This **strong price appreciation** of approximately [%]% is driven by **high demand and strong absorption** (with [sold] out of [total] units sold, representing [absorption]% annual absorption rate)."
     - If absorption 20-40%: "This **healthy price growth** of around [%]% reflects **steady market acceptance** (absorption rate of [%]% indicates consistent demand)."

  2. Check `launchDate` (project age):
     - If < 3 years old: "For a relatively new project launched in [year], this [%]% appreciation indicates **strong initial market reception** and effective pricing strategy."
     - If 3-7 years old: "Over this [X]-year period, the [%]% growth suggests **sustained demand** and **good project execution** in [location]."
     - If > 7 years old: "For a mature project of [X] years, this [%]% appreciation demonstrates **strong developer credibility** and **location value**."

  3. Check `developerName`:
     - If known reputed developer: "This growth is also attributable to the **strong brand reputation** of [Developer Name] in the [location] market."

  4. Check `location`:
     - Always mention: "The [location] micro-market has shown [context: strong infrastructure development/emerging demand/established residential appeal], supporting this price trajectory."

  **For PRICE DECREASE (Negative Growth):**

  1. Check `unsoldUnits` vs `totalSupplyUnits`:
     - If unsold > 50%: "This **price correction** of [%]% appears to be a response to **high inventory levels** (with [unsold] units still available out of [total] total units). The developer may be using strategic pricing to accelerate sales velocity."
     - If unsold 30-50%: "This [%]% price adjustment may be aimed at **improving absorption** (current unsold inventory: [unsold] units)."

  2. Check `monthlySalesVelocity` or `annualSalesUnits`:
     - If velocity is low: "This pricing strategy change correlates with **slower sales velocity** ([velocity] units/month), suggesting the developer is repositioning for market competitiveness."

  3. Check `currentPricePSF` vs market norms:
     - If current PSF is still > 4000: "Despite this correction, the current PSF of ₹[current] still positions the project in the premium segment, indicating this is a **tactical price adjustment** rather than distress."
     - If current PSF < 3500: "This correction brings the project to a more **competitive price point** for the [location] market."

  4. Market context:
     - Always add: "This pricing evolution may also reflect broader **market dynamics** in [location], including [possible factors: increased competition from new launches/market oversupply/buyer preference shifts]."

  **For STAGNANT GROWTH (0-20% over 5+ years):**

  1. Check `launchDate` and calculate years:
     - "This **modest appreciation** of [%]% over [X] years ([annual]% annually) is **below typical market averages**, which typically range 8-12% annually in [location]."

  2. Identify probable causes:
     - Check `unsoldUnits`: If high → "This limited growth correlates with **sustained inventory levels** ([unsold] unsold units), suggesting **pricing pressure** from competition."
     - Check `location`: "The [location] market may be experiencing [context: saturation/competition from newer developments/infrastructure delays]."

  3. Recommendation:
     - "To improve price realization, consider [strategies: enhancing value proposition/flexible payment schemes/targeted buyer incentives/amenity upgrades]."

  EXAMPLES WITH REASONING:

  ✅ HIGH GROWTH EXAMPLE:
  "This represents **strong price appreciation** of approximately **82%** over the project lifecycle. This increase is driven by multiple factors: (1) **Strong absorption** - with 2,150 out of 3,018 units sold (71% of inventory), demonstrating high market demand; (2) **Project maturity** - over 11 years since launch (2014), the project has proven its value and location appeal; (3) **Developer reputation** - Sara Group's credibility in the Chakan market; and (4) **Location fundamentals** - Chakan's industrial growth and upcoming metro connectivity have enhanced residential demand."

  ⚠️ PRICE DECLINE EXAMPLE:
  "This shows a **price correction** of approximately **15%** from the launch PSF. This decrease appears to be a **strategic repositioning** in response to high inventory levels - with 450 unsold units remaining out of 600 total units (75% unsold). The developer is likely using competitive pricing to accelerate sales velocity, which currently stands at 3 units/month. Despite this adjustment, the current PSF of ₹3,800 still positions the project competitively in the [location] mid-premium segment."

  📊 STAGNANT GROWTH EXAMPLE:
  "This reflects **modest price appreciation** of about **18%** over 8 years (approximately **2.25% annually**), which is **significantly below** the typical market average of 8-12% for this region. This limited growth correlates with sustained inventory levels (380 unsold units out of 500 total) and suggests **pricing pressure** from competition. The [location] market has seen an influx of new launches (15+ projects in last 3 years), creating a competitive landscape that has constrained price appreciation."

  Section 3: PROJECT AGE CONTEXT (Use launchDate)
  "The project was launched in [year] ([X] years ago), [interpretation based on age]."

  - If < 3 years old: "As a relatively new project, this pricing trajectory is [strong/moderate/concerning]."
  - If 3-7 years old: "Over this [X]-year period, the appreciation rate of [%] is [above/at/below] market average."
  - If > 7 years old: "For a mature project of [X] years, this pricing stability/growth is [noteworthy/expected/concerning]."

  Section 4: MARKET POSITIONING INSIGHT
  "[Contextualize the PSF value]"

  - If PSF > 4500: "At **₹[current] per sqft**, this positions [Project] in the **premium segment** of [location]. This price point typically attracts [target buyers: affluent buyers/investors/end-users seeking quality]."
  - If PSF 3500-4500: "At **₹[current] per sqft**, this places [Project] in the **mid-premium segment** of [location]. This is a sweet spot for [target buyers: mid-segment buyers/value-conscious buyers/first-time homeowners upgrading]."
  - If PSF 2500-3500: "At **₹[current] per sqft**, this positions [Project] as a **value offering** in [location]. This price point appeals to [target buyers: budget-conscious buyers/first-time homeowners/investors seeking rental yield]."
  - If PSF < 2500: "At **₹[current] per sqft**, this is priced as an **affordable option** in [location]. This makes it accessible to [target buyers: entry-level buyers/investors/young professionals]."

  Section 5: KEY INSIGHT & RECOMMENDATION (Based on data patterns)

  PRAISE if applicable:
  - High growth + premium PSF: "✅ **This is excellent performance!** The project has maintained strong pricing power, indicating high market confidence and developer credibility."
  - Stable pricing + good location: "✅ **This shows healthy market dynamics.** Price stability in [location] suggests sustainable demand and good project fundamentals."

  CONCERN if applicable:
  - Negative growth: "⚠️ **This needs attention.** Price correction of [%] suggests [possible reasons: market oversupply/competition/need for value addition]. Consider [recommendations: enhancing amenities/flexible payment plans/targeted marketing]."
  - Stagnant growth (< 10% over 5+ years): "⚠️ **Growth is below market average.** This may indicate [possible reasons: location challenges/competition/sales velocity issues]. Consider [recommendations: price repositioning/product differentiation/buyer incentives]."

  RECOMMENDATION (Always provide actionable advice):
  - "For buyers: This is a [good time/fair value/premium but justified] opportunity considering [factors]."
  - "For developers: To maintain momentum, consider [strategies: phased pricing increases/festival offers/loyalty programs/resale support]."
  - "For investors: The [current/projected] appreciation rate of [%] suggests [investment outlook: strong ROI potential/moderate returns/hold strategy]."

  Section 6: SOURCE
  "*Source: Liases Foras - Pricing Analytics*"

  COMPLETE EXAMPLE WITH DATA-DRIVEN REASONING (Your exact format to follow):

  "The current Price Per Square Foot (PSF) of Sara City is **₹3,996 per sqft**. The launch PSF was **₹2,200 per sqft** in 2014.

  This represents **strong price appreciation** of approximately **82%** over the project lifecycle. This increase is driven by multiple factors:

  1. **Strong absorption and demand** - With 2,150 out of 3,018 units sold (71% of total inventory), the project demonstrates robust market acceptance and sustained buyer interest.

  2. **Project maturity and track record** - Over 11 years since launch (2014), Sara City has proven its value proposition and location appeal, with the appreciation rate of 82% translating to an average annual growth of about **7.5%** - above the typical market average of 5-6% for this micro-market.

  3. **Developer credibility** - The strong brand reputation of Sara Group in the Pune real estate market has supported pricing power and buyer confidence.

  4. **Location fundamentals** - The Chakan micro-market has benefited from industrial growth, improved connectivity, and upcoming infrastructure (metro extension planned), enhancing residential demand.

  The project was launched in 2014 (11 years ago). For a mature project of this age, maintaining 82% appreciation demonstrates exceptional performance and strong fundamentals.

  At **₹3,996 per sqft**, this places Sara City in the **mid-premium segment** of Chakan. This is a sweet spot for mid-segment buyers and value-conscious buyers seeking quality at reasonable pricing. For context, newer launches in Chakan are typically priced at ₹4,200-4,500 per sqft, making Sara City competitively positioned.

  ✅ **This is excellent performance!** The project has maintained strong pricing power over 11 years while achieving 71% sales, indicating high market confidence and sustained demand. This combination of price appreciation + high absorption is rare and demonstrates best-in-class project execution.

  **For buyers:** This represents good value considering (1) the 82% historical appreciation, (2) proven delivery track record, and (3) 10-15% price discount compared to new launches. With 71% already sold, remaining inventory offers good resale potential.

  **For developers:** Sara City exemplifies how to maintain pricing power through quality delivery and brand building. The 7.5% annual appreciation while maintaining steady sales velocity (71% sold) is a benchmark for the micro-market.

  **For investors:** The historical appreciation rate of ~7.5% annually, combined with Chakan's infrastructure growth (upcoming metro extension by 2027), suggests continued ROI potential. With 868 unsold units remaining, there's scarcity value building up.

  *Source: Liases Foras - Pricing Analytics*"

• "Total Supply" → totalSupplyUnits (U)
  - DEFINITION: Total number of units available for sale in the project
  - ANSWER: "**[totalSupplyUnits with commas] units**"

• "Absorption Rate" / "Annual Absorption Rate" → Calculate from annualSalesUnits / totalSupplyUnits
  - NATURE: CALCULATED METRIC (derived from base dimensions, not directly retrieved)
  - DEFINITION: Percentage of total inventory sold annually, indicating market demand strength
  - MANDATORY FORMAT:
    * Show derivation formula
    * Use bullet points (•) for intermediate values with labels
    * **Mark the final answer in bold**
    * Use paragraph breaks between sections
    * End with italicized source: "*Source: Liases Foras - Project Performance Metrics*"
  - DERIVATION FORMULA:
    Annual Absorption Rate = (Annual Sales Units / Total Supply Units) × 100
  - EXAMPLE (COPY THIS EXACTLY):
    "The Annual Absorption Rate is calculated as: (Annual Sales / Total Supply) × 100

    • Annual Sales Units = 527
    • Total Supply Units = 1,109

    Annual Absorption Rate = (527 / 1,109) × 100 = **47.52%**

    *Source: Liases Foras - Project Performance Metrics*"

• "PSF Gap" → Calculate from launchPricePSF - currentPricePSF (CF/L²)
  - NATURE: CALCULATED METRIC (calculation required)
  - DEFINITION: The difference between Launch Price PSF and Current/Effective Realised PSF, indicating price adjustment over project lifecycle
  - UNIT: Rs/Sq.Ft.

  - MANDATORY DETAILED FORMAT (COPY EXACTLY):

    "**Definition:**
    PSF Gap represents the difference between the Launch Price PSF (initial offering price per square foot) and the Current Price PSF (actual market realization price per square foot). It indicates how pricing has evolved since the project launch.

    **Formula:**
    PSF Gap = Launch Price PSF - Current Price PSF

    **Calculation:**
    • Launch Price PSF: **Rs.[launch]/Sq.Ft.** (from Liases Foras data)
    • Current Price PSF: **Rs.[current]/Sq.Ft.** (from Liases Foras data)
    • PSF Gap = **Rs.[launch]/Sq.Ft.** - **Rs.[current]/Sq.Ft.** = **Rs.[gap]/Sq.Ft.**

    **Result:**
    The PSF Gap for [Project] is **Rs.[gap]/Sq.Ft.**

    **Insight:**
    [Choose based on gap value:]
    - If gap is small positive (like 22): This is actually quite positive! The PSF has marginally decreased by just **Rs.[gap]** since launch, which indicates stable pricing in the market. For a project in [location], this level of price stability suggests healthy demand and good developer credibility.
    - If gap is large positive (>500): Hmm, this needs attention. The PSF has dropped by **Rs.[gap]** since launch, which suggests some pricing pressure in the market. This could be due to slower absorption or competitive pressure from nearby projects.
    - If gap is negative: Oh! This is excellent news! The PSF has actually increased by **Rs.[abs_gap]** since launch, showing strong appreciation. This indicates robust demand and validates the developer's pricing strategy!

    *Source: Liases Foras - Pricing Analytics Database*"

• "Months of Inventory (MOI)" / "MOI" → Calculate from Unsold Units / Monthly Sales Rate (T)
  - NATURE: CALCULATED METRIC (multi-step calculation required)
  - DEFINITION: Number of months required to sell remaining inventory at current sales velocity
  - UNIT: months

  - CONVERSATIONAL FORMAT (COPY THIS STYLE EXACTLY):

    "The Months of Inventory (MOI) for [Project] is **[X] months**.

    Let me break this down:
    - Unsold Units = Total Supply - Total Sold = **[supply] units** - **[sold] units** = **[unsold] units**
    - Monthly Sales Rate = Annual Sales / 12 = **[annual] units/year** / 12 = **[monthly] units/month**
    - MOI = Unsold / Monthly Sales = **[unsold]** / **[monthly]** = **[X] months**

    [ADD CONVERSATIONAL INSIGHT HERE - Examples below]

    If MOI < 3 months: "This is excellent! An MOI of less than 3 months indicates very strong absorption. At this velocity, the remaining inventory will be sold out in under 3 months. The project is clearly a market favorite in [location]!"

    If MOI 3-12 months: "This looks good! An MOI of **[X] months** suggests healthy demand. At the current sales pace, you'll clear the remaining inventory within a year, which is a comfortable position to be in."

    If MOI > 12 months: "Hmm, this needs some attention. An MOI of **[X] months** indicates slower absorption. You might want to consider pricing adjustments, enhanced marketing, or additional amenities to boost sales velocity."

    *Source: Liases Foras - Project Performance Metrics*"

• "Saleable Area" → projectSaleable (L²)
• "Project Duration" → projectDuration (T)
• "Total Investment" → totalInvestment (CF)

CRITICAL RULE FOR "PROJECT SIZE":
- In real estate, "Project Size" means the NUMBER OF HOUSING UNITS (U dimension), NOT land area (L²)
- ALWAYS answer with projectSizeUnits FIRST, mention acres as secondary context
- If user wants area, they will explicitly ask "project size in acres"

LOCATION: Optional - can query by project_name alone.

NOTE: This function returns ALL fields as JSON. You must analyze the full response and extract the correct attribute based on the user's natural language question, using the dimensional system (U, L², T, CF) to disambiguate.

ANSWER FORMATTING GUIDELINES:

1. SOURCE ATTRIBUTION (MANDATORY):
   - ALWAYS cite source in italics: "*Source: Liases Foras - [Dataset Name]*" at the end of your answer
   - NEVER use technical jargon like: "Knowledge Graph", "KG", "knowledge_graph_lookup", "Knowledge Base", "Vector Search", "GraphRAG", "RAG", "embedding", "vector database"
   - ALWAYS say "Liases Foras" - this is the business/brand name users understand
   - Dataset names (business language): "Pricing Analytics", "Market Intelligence Database", "Project Performance Metrics", "Developer Performance Index"
   - CORRECT: "*Source: Liases Foras - Pricing Analytics*"
   - WRONG: "Source: Knowledge Graph", "Source: KG", "liases_foras_lookup"

2. INSIGHTS (HIGHLY RECOMMENDED):
   - Provide useful context or derived insights when relevant
   - Example: If asked "starting price", convert PSF to approximate unit price using unit saleable size
   - Example: If asked "absorption rate", show the formula and calculation transparently

3. NUMBER FORMATTING (MANDATORY):
   - Use Indian numeral system with commas: thousand, lakh, crore
   - Correct: ₹3,696 PSF, ₹20,32,800, 3,018 units, 1,109 units
   - Wrong: ₹3696 PSF, ₹2032800, 3018 units, "20.49 Lakhs" (spell out fully with commas)
   - For currency: Always use ₹ symbol with Indian comma notation
   - For large amounts: ₹20,32,800 (NOT "INR 20.49 Lakhs")

4. ANSWER STRUCTURE FOR SIMPLE QUERIES:
   Example: "The project size of Sara City is **3,018 units** (covering 7.85 acres).

   Source: Liases Foras - Market Intelligence Database"

5. ANSWER STRUCTURE FOR CALCULATED METRICS (with step-by-step calculation):

   Example for Absorption Rate:

   **Key Finding:**
   • The Annual Absorption Rate for this project is **47.52%**

   **Context:**
   • This indicates the percentage of total inventory sold annually
   • Higher absorption rates (>50%) suggest strong market demand

   **Calculation:**
   • Formula: Absorption Rate = (Annual Sales Units / Total Supply Units) × 100
   • Input 1: Annual Sales Units = **527 units** (from Liases Foras data)
   • Input 2: Total Supply Units = **1,109 units** (from Liases Foras data)
   • Calculation Steps:
     - Divide sales by supply: 527 ÷ 1,109 = **0.4752**
     - Convert to percentage: 0.4752 × 100 = **47.52%**
   • Final Result: **47.52%**

   **Sources:**
   1. *Liases Foras - Project Performance Metrics*
   2. *Liases Foras - Market Intelligence - Q3 FY25*

6. PROFESSIONAL ANSWER FORMAT (APPLIES TO ALL QUERIES):

   Use bullet points (•), bold numbers, numbered sources. Example for "Effective Realised PSF":

   **Key Finding:**
   • The Effective Realised PSF for Shubhan Karoli is **₹2,808 per sq.ft.**

   **Context:**
   • Developer: Creative Ventures
   • This represents the net value received by the developer for the sale of this property, after accounting for all discounts, offers, and other adjustments
   • It reflects the actual per square foot price at which units are transacted in the market, providing a realistic understanding of pricing trends and project valuation

   **Derivation:**
   • Formula: Effective Realised PSF = (Total Revenue × 1e7) / (Total Supply Units × Unit Saleable Size)
   • Total Revenue: **8.42 Cr**
   • Total Supply Units: **424 units**
   • Unit Saleable Size: **707 sq.ft.**

   **Sources:**
   1. *Liases Foras - Pricing Analytics Database*
   2. *Liases Foras - Market Intelligence - Q3 FY25*

7. ANSWER STRUCTURE FOR OTHER PRICE QUERIES:
   Example: "The starting price for The Urbana was **₹3,696 per square foot**. Based on an average unit saleable size of 550 sqft, the starting price for a typical unit would be approximately **₹20,33,000**.

   *Source: Liases Foras - Pricing Analytics*"

8. ANSWER ACCURACY:
   - Stick to Knowledge Graph data - do NOT make up values
   - If deriving/calculating, show your work transparently
   - Only add inferred details if you're highly confident and cite the inference logic""",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "description": """Type of query:
- get_project_by_name: Get specific project data
- get_project_metrics: Get metrics for specific project
- list_projects_by_location: List project names in a location
- get_all_projects_with_data: Get ALL projects with full data for SQL-like operations (Top-N, sorting, filtering, aggregations, averages, medians, etc.)

⚠️ IMPORTANT: Use 'get_all_projects_with_data' for queries like:
- "List top 3 projects by Launch Price PSF"
- "Which project has highest PSF Gap?"
- "Show average Total Supply Units across all projects"
- "List projects sorted by Annual Sales Units"
- "Show projects where Unsold Percent > 10%"
""",
                        "enum": [
                            "get_project_by_name",
                            "get_project_metrics",
                            "list_projects_by_location",
                            "get_all_projects_with_data"
                        ]
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Exact project name (e.g., 'Sara City', 'Gulmohar City'). Use exact project name from context."
                    },
                    "location": {
                        "type": "string",
                        "description": "Location/micro-market/city name for filtering (e.g., 'Kolkata', 'Chakan', '0-2 KM')"
                    }
                },
                "required": ["query_type"]
            }
        }
        tools.append(kg_function_dict)

        # Add distance calculation function
        distance_function_dict = {
            "type": "function",
            "name": "getDistanceFromProject",
            "description": """Calculate the Haversine distance (in kilometers) between two specific projects using their latitude and longitude coordinates.

IMPORTANT: This function automatically retrieves the lat/long coordinates for both projects - you just need to provide the project names.

Perfect for queries like:
- "Distance between Sara City and Gulmohar City"
- "How far is Project X from Project Y"
- "What is the distance from Sara City to The Urbana"

Returns the great-circle distance in kilometers with 3 decimal places of precision.

ANSWER FORMAT (COPY EXACTLY):

"The distance from **[Source Project]** to **[Target Project]** is **[X.XXX] kilometers**.

[ADD CONVERSATIONAL CONTEXT - Examples below]

If distance < 2 km: "That's quite close! These projects are practically neighbors, within easy walking or cycling distance."

If distance 2-10 km: "That's a reasonable distance - about [X] minutes by car in normal traffic."

If distance > 10 km: "These projects are in different micro-markets of the city, separated by [X] km."

*Source: Calculated using Haversine formula with coordinates from Google Maps*"
""",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_project": {
                        "type": "string",
                        "description": "Name of the source/reference project (e.g., 'Sara City', 'Gulmohar City')"
                    },
                    "target_project": {
                        "type": "string",
                        "description": "Name of the target project to measure distance to (e.g., 'VTP Pegasus', 'The Urbana')"
                    }
                },
                "required": ["source_project", "target_project"]
            }
        }
        tools.append(distance_function_dict)

        # Add proximity search function
        proximity_function_dict = {
            "type": "function",
            "name": "find_projects_within_radius",
            "description": """Find all projects within a specified radius (in kilometers) of a center project using Haversine formula for great-circle distance calculation.

Perfect for queries like:
- "Which projects are located within 2 KM radius of Sara City?"
- "Show me all projects near Gulmohar City within 5 km"
- "Find projects within 3 kilometers of The Urbana"

Returns a list of projects sorted by distance (closest first) with each project's distance in kilometers.

ANSWER FORMAT (COPY EXACTLY):

"I found **[N] project(s)** within **[radius] km** of **[Center Project]**:

1. **[Project 1]** - **[distance] km** away
2. **[Project 2]** - **[distance] km** away
...

[ADD CONVERSATIONAL INSIGHT - Examples below]

If many results: "This area has quite a few developments! All these projects are competing in the same micro-market."

If few results: "This location is relatively exclusive with fewer competing projects nearby."

If no results: "This project stands alone in its area with no other developments within [radius] km."

*Source: Calculated using Haversine formula with coordinates from Google Maps*"
""",
            "parameters": {
                "type": "object",
                "properties": {
                    "center_project": {
                        "type": "string",
                        "description": "Name of the center/reference project (e.g., 'Sara City', 'Gulmohar City')"
                    },
                    "radius_km": {
                        "type": "number",
                        "description": "Search radius in kilometers (e.g., 2 for 2 KM radius, 5 for 5 KM radius)"
                    }
                },
                "required": ["center_project", "radius_km"]
            }
        }
        tools.append(proximity_function_dict)

        # Add Google Maps visualization function
        map_function_dict = {
            "type": "function",
            "name": "generate_location_map_with_poi",
            "description": """⚠️ MANDATORY: Call this function WHENEVER a project location or project details are mentioned in the query. This provides essential visual context for ALL project-related queries.

Generate a comprehensive Google Maps visualization showing a project location with nearby important places marked with colored markers.

POI Categories with Marker Colors:
- Project itself: RED marker with label 'P' (PRIMARY)
- Hotels: BLUE markers with label 'H'
- Petrol Pumps: GREEN markers with label 'P'
- Railway Stations: PURPLE markers with label 'R'
- Airports: ORANGE markers with label 'A'
- Metro Stations: YELLOW markers with label 'M'
- Bus Stops: BROWN markers with label 'B'
- Hospitals: PINK markers with label 'H'
- Schools: LIGHT BLUE markers with label 'S'
- Shopping Malls: GRAY markers with label 'M'

AUTO-TRIGGER for these queries:
- Any question asking about a specific project (e.g., "What is Sara City?", "Tell me about Gulmohar City")
- Location queries ("Where is Sara City located?")
- Explicit map requests ("Show me a map of Sara City")
- Project details queries ("What are the amenities near Sara City?")

WORKFLOW:
1. FIRST: Call 'liases_foras_lookup' to get project data including latitude and longitude
2. THEN: Call THIS function with the coordinates to generate map
3. ALWAYS display the map in your answer

Returns:
- Static map URL (800x600 image with all markers)
- Interactive embed URL (for Google Maps iframe)
- List of all nearby POIs with distances (sorted closest first)
- POI details: name, category, address, distance in KM

ANSWER FORMAT (COPY EXACTLY):

"📍 **Location Map for [Project Name]**

I've generated a comprehensive map showing **[Project Name]** (marked in RED) along with [N] nearby places of interest:

🗺️ **Interactive Map**: [Use embed_map_url]

**Nearby Facilities** (within 5km radius):

[List top 10-15 POIs grouped by category]

**Hotels** 🏨
- [Name] - [X.XX] km away

**Transportation** 🚇🚌
- [Railway/Metro/Bus stops with distances]

**Healthcare** 🏥
- [Hospitals with distances]

**Education** 🏫
- [Schools with distances]

**Shopping & Dining** 🛍️
- [Malls with distances]

**Utilities** ⛽
- [Petrol pumps with distances]

[ADD CONVERSATIONAL INSIGHT about location connectivity and amenities]

*Source: Google Places API (5km radius search)*"
""",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project to visualize (e.g., 'Sara City', 'Gulmohar City')"
                    },
                    "latitude": {
                        "type": "number",
                        "description": "Project latitude coordinate (e.g., 18.7381)"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Project longitude coordinate (e.g., 73.9698)"
                    },
                    "city": {
                        "type": "string",
                        "description": "City name for context (e.g., 'Pune', 'Kolkata'). Uses location_context city if not specified."
                    },
                    "zoom": {
                        "type": "integer",
                        "description": "Map zoom level 1-20 (default: 14, where 14 shows ~2-3km radius)"
                    }
                },
                "required": ["project_name", "latitude", "longitude"]
            }
        }
        tools.append(map_function_dict)

        # Add Quarterly Market Knowledge Graph function
        quarterly_market_kg_function = {
            "type": "function",
            "name": "quarterly_market_lookup",
            "description": """Query Quarterly Market Knowledge Graph for sales and supply data.

DEFAULT FUNCTION for market-level queries (no specific project mentioned).

Each quarter is a KG node with:
• Layer 0: Sales Units, Sales Area (mn sq ft), Supply Units, Supply Area (mn sq ft)
• Layer 1: Absorption Rate, YoY Growth, QoQ Growth, Average Unit Size

Query Types:
1. By fiscal year: {"year": 2024} → All quarters in FY 24-25
2. By year range: {"year_range": [2022, 2024]} → All quarters 2022-2024
3. By quarter ID: {"quarter_id": "Q1_FY24_25"} → Specific quarter
4. Recent quarters: {"recent": 8} → Last 8 quarters

Examples:
- "What is supply units for FY 24-25?" → {"year": 2024}
- "Show me sales in 2023" → {"year": 2023}
- "What are recent market trends?" → {"recent": 8}

🚨 CRITICAL ANSWER FORMAT - YOU MUST FOLLOW EXACTLY 🚨

EVERY ANSWER MUST INCLUDE:

1. ✅ TOTAL (aggregated) with bold numbers and units
2. ✅ QUARTERLY BREAKDOWN in a clear table/list format showing ALL quarters
3. ✅ LAYER 1 INSIGHTS - Include absorption rate, YoY growth, QoQ growth trends
4. ✅ DETAILED COMMENTARY - Analyze the data:
   - Identify trends (increasing/decreasing)
   - Compare quarters (which Q performed best/worst)
   - Highlight significant changes (YoY growth, QoQ momentum)
   - Provide market insights and interpretation
   - Add recommendations or observations

EXAMPLE FORMAT (COPY THIS):

Q: "What is supply units for FY 24-25?"

A: The total supply units for FY 24-25 in Chakan, Pune is **6,894 units**.

**Quarterly Breakdown:**
• Q1 24-25: **1,741 units** (31.2% YoY growth)
• Q2 24-25: **1,731 units** (absorption: 9.42%)
• Q3 24-25: **1,699 units** (lowest quarter)
• Q4 24-25: **1,723 units**

**Layer 1 Insights:**
• Overall Absorption Rate: **11.71%** (Sales / Supply)
• Average Supply per Quarter: **1,724 units**
• YoY Growth Trend: Strong growth in Q1 (+31.2%), showing market recovery
• QoQ Trend: Slight decline Q1→Q3, then stabilization in Q4

**Market Commentary:**
This is a healthy supply pipeline! The market added **6,894 units** across FY 24-25, showing **31% growth** compared to last year.

The quarterly distribution is remarkably balanced (1,700-1,750 units per quarter), suggesting well-planned inventory management by developers. Q1 showed the strongest performance with 1,741 units, while Q3 dipped slightly to 1,699 units (likely seasonal impact).

The absorption rate of **11.71%** indicates the market is absorbing about 1 in 9 available units quarterly - this is moderate absorption, suggesting there's healthy supply but not oversupply. For Chakan's profile as an industrial corridor, this indicates balanced market conditions.

*Source: Quarterly Market Knowledge Graph - Chakan, Pune (FY 24-25)*

Returns: Quarter nodes with Layer 0 + Layer 1 data, location context, aggregated metrics.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Query by fiscal year (e.g., 2024 for FY 24-25). Returns all 4 quarters."
                    },
                    "year_range": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Query by year range [start_year, end_year]. Example: [2022, 2024]",
                        "minItems": 2,
                        "maxItems": 2
                    },
                    "quarter_id": {
                        "type": "string",
                        "description": "Specific quarter ID (e.g., 'Q1_FY24_25', 'Q3_FY23_24')"
                    },
                    "recent": {
                        "type": "integer",
                        "description": "Get N most recent quarters. Default: 8 (2 years)"
                    },
                    "quarter_num": {
                        "type": "integer",
                        "description": "Filter by quarter number (1-4). Example: 1 for all Q1 quarters across years"
                    }
                }
            }
        }
        tools.append(quarterly_market_kg_function)

        # Chart generation function for visualizing data
        chart_function = {
            "type": "function",
            "name": "generate_chart",
            "description": """Generate a chart visualization for tabular data to enhance user experience.

🎯 CRITICAL: AUTOMATICALLY CALL THIS FUNCTION WHENEVER YOU DISPLAY MULTI-ROW DATA

You MUST invoke this function when:
1. Displaying quarterly trends (sales, supply, absorption rates) - ANY quarterly data response
2. Showing comparisons across projects, years, or time periods
3. Presenting any data with 3+ rows that can be visualized
4. User explicitly asks for visual representation or charts

Chart Types Auto-Selected:
- Time-series data (quarter, year, month) → Line chart
- Comparisons (< 10 items) → Pie or Bar chart
- Multiple metrics → Multi-line or Grouped bar chart

Example Workflow:
1. User asks: "What is supply for FY 24-25?"
2. You call quarterly_market_lookup → get data
3. You display text answer with breakdown
4. YOU MUST ALSO call generate_chart with the same data
5. Return both text answer AND chart specification

Returns: Plotly-compatible chart specification for frontend rendering.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "Array of data objects to visualize (e.g., quarterly data from quarterly_market_lookup)",
                        "items": {"type": "object"}
                    },
                    "chart_type": {
                        "type": "string",
                        "description": "Optional chart type. Auto-detected if not provided.",
                        "enum": ["line", "bar", "column", "pie", "scatter", "area", "multi_line", "grouped_bar"]
                    },
                    "title": {
                        "type": "string",
                        "description": "Chart title (optional)"
                    },
                    "description": {
                        "type": "string",
                        "description": "What the chart shows (helps auto-detection)"
                    }
                },
                "required": ["data"]
            }
        }
        tools.append(chart_function)

        # Unit Size Range Lookup Function
        unit_size_range_function = {
            "type": "function",
            "name": "unit_size_range_lookup",
            "description": """**PRIORITY FUNCTION** - Query Unit Size Range Knowledge Graph for product performance analysis by saleable area.

⚠️ IMPORTANT: This is the PRIMARY function for ALL queries involving:
• Unit sizes (450-1200 sqft, Studio, 1BHK, 2BHK, 3BHK, 1.5BHK)
• Flat types and product mix analysis
• Physical area-based performance (sq ft, saleable area, carpet area)
• Size-based market segmentation
• Questions about "which size", "what unit type", "how big", "square feet", "sqft"

USE THIS FUNCTION PROACTIVELY whenever the user asks about:
- "1BHK" or "2BHK" or "3BHK" or "Studio" or "1.5 BHK"
- "unit size" or "unit type" or "flat type" or "apartment size"
- "600 sqft" or "small units" or "large units"
- "product mix" or "unit mix" or "typology"
- "best performing size" or "which size sells best"
- Performance by size/type

Each size range is a KG node with:
• Layer 0: Annual Sales (Units & Area), Supply, Stock, Unsold Inventory, Product Efficiency
• Layer 1: Absorption Rate, Avg Unit Size, Inventory Turnover, Unsold Ratio
• Layer 2: Revenue, Market Cap, Months of Inventory, Sellout Velocity

Query Types:
1. By flat type: {"flat_type": "1BHK"} → All size ranges with 1BHK units
2. By efficiency: {"min_efficiency": 50} → Ranges with product efficiency >= 50%
3. By sales volume: {"min_sales": 100} → Ranges with annual sales >= 100 units
4. By size range: {"size_range": [500, 700]} → Ranges between 500-700 sq ft
5. Top performers: {"top_n": 5, "metric": "absorption_rate"} → Top 5 by absorption rate
6. All data: {} (empty filters) → All 11 size ranges

ALWAYS call generate_chart after this function to visualize the results!

Examples:
- "What is the best performing unit size?" → {"top_n": 1, "metric": "product_efficiency_pct"}
- "Show me 1BHK performance" → {"flat_type": "1BHK"}
- "Which sizes have good absorption?" → {"min_efficiency": 50}
- "600 sq ft units performance" → {"size_range": [550, 650]}

Returns: Size range nodes with Layer 0 + Layer 1 + Layer 2 data, location context, aggregated metrics.
⚠️ IMPORTANT: After calling this function, ALWAYS call generate_chart to create a visualization of the data.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "flat_type": {
                        "type": "string",
                        "description": "Filter by flat type (1BHK, 2BHK, 3BHK, 1 1/2 BHK, Studio)"
                    },
                    "min_efficiency": {
                        "type": "integer",
                        "description": "Minimum product efficiency percentage (0-100)"
                    },
                    "min_sales": {
                        "type": "integer",
                        "description": "Minimum annual sales units"
                    },
                    "size_range": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Size range filter [min_sqft, max_sqft]. Example: [500, 700]"
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Get top N performing ranges. Use with 'metric' parameter."
                    },
                    "metric": {
                        "type": "string",
                        "enum": ["absorption_rate", "product_efficiency_pct", "inventory_turnover"],
                        "description": "Metric to rank by when using top_n"
                    }
                }
            }
        }
        tools.append(unit_size_range_function)

        # Unit Ticket Size Lookup Function
        unit_ticket_size_function = {
            "type": "function",
            "name": "unit_ticket_size_lookup",
            "description": """**PRIORITY FUNCTION** - Query Unit Ticket Size Knowledge Graph for product performance analysis by price range (INR Lakhs).

⚠️ IMPORTANT: This is the PRIMARY function for ALL queries involving:
• Price ranges (₹10 Lac, ₹20 Lac, ₹50 Lac, <10 Lac, 10-20 Lac, etc.)
• Ticket sizes and affordability analysis
• Price-based market segmentation
• Budget ranges and investment amounts
• Questions about "how much", "price", "cost", "budget", "affordable", "expensive", "cheap"

USE THIS FUNCTION PROACTIVELY whenever the user asks about:
- "affordable housing" or "cheap units" or "premium units"
- "10 lakh" or "15 lakh" or "20 lakh" or any price mention in Lakhs/Crores
- "budget" or "price range" or "cost range"
- "ticket size" or "price segment" or "price bracket"
- "best value" or "affordability" or "ROI by price"
- Performance by price/cost

Each ticket size range is a KG node with:
• Layer 0: Annual Sales (Units & Value %), Supply, Unsold Inventory, Marketable Supply, PSF Pricing
• Layer 1: Value Absorption Rate, Unit Absorption Rate, Value-to-Unit Ratio, Marketability Index, Price Premium Index
• Layer 2: Revenue Concentration, Market Capitalization, Affordability Score, Price Efficiency, Investment Concentration

Query Types:
1. By price range: {"price_lacs": 15} → Ticket range containing 15 Lakhs
2. By efficiency: {"min_efficiency": 50} → Ranges with product efficiency >= 50%
3. By sales volume: {"min_sales": 100} → Ranges with annual sales >= 100 units
4. By affordability: {"max_affordability": 150} → Ranges where affordability score <= 150
5. Top performers: {"top_n": 3, "metric": "value_absorption_rate_pct"} → Top 3 by value absorption
6. All data: {} (empty filters) → All 5 ticket size ranges

ALWAYS call generate_chart after this function to visualize the results!

Examples:
- "What is the best performing price range?" → {"top_n": 1, "metric": "product_efficiency_pct"}
- "Show me affordable housing (<10 Lacs)" → {"price_lacs": 8}
- "Which price ranges have good value absorption?" → {"min_efficiency": 50}
- "15 Lakh units performance" → {"price_lacs": 15}

Returns: Ticket size range nodes with Layer 0 + Layer 1 + Layer 2 data, location context, aggregated metrics.
⚠️ IMPORTANT: After calling this function, ALWAYS call generate_chart to create a visualization of the data.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "price_lacs": {
                        "type": "number",
                        "description": "Price point in INR Lakhs to find the containing ticket range"
                    },
                    "min_efficiency": {
                        "type": "integer",
                        "description": "Minimum product efficiency percentage (0-100)"
                    },
                    "min_sales": {
                        "type": "integer",
                        "description": "Minimum annual sales units"
                    },
                    "max_affordability": {
                        "type": "number",
                        "description": "Maximum affordability score (lower is more affordable)"
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Get top N performing ranges. Use with 'metric' parameter."
                    },
                    "metric": {
                        "type": "string",
                        "enum": ["value_absorption_rate_pct", "unit_absorption_rate_pct", "product_efficiency_pct", "price_efficiency_score"],
                        "description": "Metric to rank by when using top_n"
                    }
                }
            }
        }
        tools.append(unit_ticket_size_function)

        # NOTE: File Search is NOT supported by Interactions API
        # Regulatory queries are routed to generateContent API with File Search
        # (See _is_regulatory_query() and _query_with_file_search() methods above)

        # Simplified Interactions API flow (KG + quarterly market + chart)
        try:
            # Prepend formatting instructions to user query
            # This ensures Gemini follows bullet point format for ALL responses
            formatted_input = f"""# REAL ESTATE INVESTMENT ANALYSIS — RESPONSE GENERATION INSTRUCTIONS

## VOICE & ROLE 🎯
You are a **trusted investment consultant** providing professional real estate analysis.
Write with: Confidence • Clarity • Advisory precision • Investor-grade rigor

---

## CORE RESPONSIBILITY 🧠
Transform data from function calls into clear, structured, client-ready investment insights.

**You MUST:**
✅ Identify question intent immediately
✅ Use logical narrative flow (not rigid templates)
✅ Present insights with clean tables, headers, and justified reasoning
✅ Always show **units** (₹/sqft, units, %, months, sqft)
✅ Prefer **CARPET area** when discussing sizes

**You MUST NEVER:**
❌ Re-query data or mention backend tools
❌ Use generic headers like "Analysis" or "Overview"
❌ Make unjustified assumptions
❌ Show data without interpretation

---

## RECENCY RULE ⏱️ (NON-NEGOTIABLE)
**All trends, comparisons, rankings MUST use recent data.**

**Preferred Quarterly Format:** Always present last 4 quarters in reverse chronological order:
- **Q2 FY25-26** (latest) → Q1 FY25-26 → Q4 FY24-25 → Q3 FY24-25

**When to use:**
- 📊 Absorption, velocity, launches: Last 3-6 months
- 📈 Pricing, demand indicators: Last quarter minimum
- 🏗️ Supply trends: Last 4 quarters (tabular format)

**If data is older than 6 months:**
- State it clearly: "*Data as of Q4 FY24-25*"
- Use recent external data only to validate direction
- ❌ Never construct trends using stale snapshots

---

## DATA AGGREGATION & SUMMARIZATION RULES 📊

**You MAY:**
✅ Aggregate, average, or normalize data to explain trends
✅ Use ranges, medians, weighted averages when multiple data points exist
✅ Propose phasing strategy based on market absorption capacity
✅ Estimate land acquisition cost using recent comparables

**You MUST (when aggregating):**
1. **Clearly state what was aggregated** ("Averaged across 5 projects in micro-market")
2. **Explain why the method is appropriate** ("Median used to avoid outlier skew")
3. **Mention data scope** ("Based on Q1-Q2 FY25-26 launches in location")

**Example:**
📊 **Average PSF: ₹4,250/sqft**
*Calculated as weighted average across 8 active projects (Q2 FY25-26), weighted by total saleable area. Excludes 2 outliers (ultra-premium segment).*

🚫 **Do NOT aggregate silently**
🚫 **Do NOT mix incompatible datasets** (different cities, time periods, segments)

---

## ASSUMPTIONS — STRICT CONTROL ⚠️

**Assumptions allowed ONLY if unavoidable.**

**If you make an assumption, you MUST:**
1. **Explicitly label** it as assumption: "*Assumed construction cost: ₹2,800/sqft*"
2. **Justify why reasonable:** "Based on 3 comparable mid-rise projects in micro-market"
3. **Anchor to:**
   - Comparable project data from function results, OR
   - Location-level absorption/pricing trends, OR
   - Recent land transactions/guidance rates, OR
   - External benchmarks (with citation)

**Example:**
⚠️ **Assumption:** Construction timeline of 36 months
**Justification:** Based on 4 comparable projects by same developer (32-38 month range, median 36 months)
**Source:** LF Developer Performance Index | Q3 FY24-25

🚫 **Never assume without explanation**
🚫 **Never hide assumptions inside narrative**

---

## IRR / NPV / CASHFLOW MODELING — MARKET PREFILL MODE 💰

**When IRR, NPV, or cashflow analysis is requested:**

### STEP 1 — MARKET-BASED PREFILL (MANDATORY)
**Before asking user for inputs**, pre-compute and present ALL key inputs using:
- LF function data (where available)
- Recent external benchmarks (with citation)
- Location-level and developer-scale comparables

**Prefilled inputs MAY include:**
- 🏗️ **Construction cost** (₹/sqft, phase-wise) — from comparable projects
- 💰 **Land acquisition cost** — recent land transactions + guidance values
- 📏 **Total saleable/carpet area** — from project data
- 💵 **Selling price** — recent market average/range from LF data
- ⏱️ **Construction timeline** — developer track record
- 🏘️ **Phasing strategy** — absorption capacity-based

**All prefilled values MUST be:**
- Clearly labeled as **assumptions**
- Briefly justified with recent data
- Tied to specific function results or external sources

### STEP 2 — CRITICAL INPUTS PREFILL (PAYMENT PLANS, FINANCING, ETC.)

**For these critical inputs, pre-compute SCENARIOS**, present them, and ask for confirmation:

**1. Payment Plan / Collection Schedule**
   - Construction-linked (standard)
   - Upfront-heavy (20:80 model)
   - Subvention (if prevalent by market/regulation)

**2. Construction Timeline & Cost Phasing**
   - Based on project scale (small/mid/large developer track record)
   - Typical timelines from comparable developments
   - Phase-wise construction cost deployment

**3. Financing Structure**
   - No-debt / self-funded
   - Moderate leverage (market-standard LTV ~40-50%)
   - Higher leverage (risk-adjusted, LTV ~60%)
   - Use prevailing interest rates and market norms

**4. Phasing Logic**
   - Initial phase size based on absorption capacity
   - Subsequent phase triggers linked to sell-through % (e.g., 60% sold → Phase 2 launch)

### STEP 3 — EXPLICIT CONFIRMATION REQUEST

**Present all assumptions in a summary table, then ask:**

> "📋 **Prefilled Assumptions Summary:**
>
> | Input | Value | Source/Justification |
> |-------|-------|---------------------|
> | Construction Cost | ₹2,800/sqft | 3 comparable projects in micro-market |
> | Land Cost | ₹12,500/sqft | Recent transactions (Q1 FY25-26) |
> | Selling Price | ₹4,200/sqft | LF market average (Q2 FY25-26) |
> | Construction Timeline | 36 months | Developer track record (median) |
> | Payment Plan | Construction-linked | Market standard |
> | Financing | 50% LTV @ 10.5% | Market norm |
>
> **Would you like me to proceed with these market-based assumptions,
> or would you prefer to override any of these inputs with your own specifics?**"

🚫 **Do NOT finalize IRR/NPV without this confirmation**

---

## TABLE CONTRACT 📊

**If a table is used, it MUST:**
1. Show **units and dates** in headers
2. Keep columns minimal (max 5-6)
3. **Immediately follow with:**
   - 📌 **Observation:** (what the data shows)
   - ➡️ **Implication:** (what this means for decision-making)

**Example:**
| Quarter | Supply (units) | Sales (units) | Absorption Rate |
|---------|----------------|---------------|-----------------|
| Q2 FY25-26 | 1,250 | 890 | 71% |
| Q1 FY25-26 | 1,100 | 820 | 75% |
| Q4 FY24-25 | 1,050 | 750 | 71% |

📌 **Observation:** Absorption has remained stable at 71-75% over last 3 quarters despite rising supply.
➡️ **Implication:** Strong underlying demand. Launch timing for new phase appears favorable if priced competitively.

---

## RESPONSE FLOW (PRIORITY-BASED, NOT FIXED) 🧭

**1️⃣ DIRECT ANSWER FIRST** (1-3 sentences)
Clear answer + one key recent metric
**Example:** "The average PSF in this micro-market is **₹4,250/sqft** (Q2 FY25-26), up 6% QoQ from ₹4,010/sqft."

**2️⃣ SUPPORTING EXPLANATION**
- Tables for quarterly data (last 4 quarters: Q2 FY25-26 → Q3 FY24-25)
- Aggregations and assumptions explained inline
- **When numbers appear** (projects/inventory/prices): Consider chart if comparison/trend/velocity

**3️⃣ INSIGHTS, OBSERVATIONS, RECOMMENDATIONS**
- Patterns (e.g., "Absorption accelerating in premium segment")
- Risks (e.g., "High unsold inventory in budget segment may pressure pricing")
- Opportunities (e.g., "Gap in 2BHK supply below ₹50L ticket size")

**4️⃣ FORWARD LOOK + FOLLOW-UP QUESTIONS** ❓ (MANDATORY)

**Ask 3-4 sharp follow-up questions that:**
- Confirm assumptions made
- Offer alternative approaches
- Progress the analysis meaningfully
- **Feel conversational** and clearly tied to what user just asked/confirmed

**Examples:**
- "Would you like me to model a scenario with faster absorption (20% sell-through in 6 months)?"
- "Should I factor in the upcoming metro extension (2027 completion) for phase 2 pricing?"
- "Do you want to see IRR sensitivity to ±10% pricing variation?"

🚫 **Do NOT ask unrelated questions** — stay focused on the current analysis thread

**5️⃣ SOURCE LABEL + CONFIDENCE** 🏷️ (MANDATORY)

**Confidence Scoring:**
Assign confidence based on:
- **Number of data points** (primary factor)
- **Data quality:** LF data > external sources
- **Recency:** helpful but not dominant

**Format:**
📊 **[Metric/Insight]**
🟢 **High Confidence** | [One-line rationale]
**Source:** [LF Data | Date] + [External Source: Full citation if used]

**Confidence Levels:**
- 🟢 **HIGH:** 5+ LF data points, <6 months old, validated by external source
- 🟡 **MEDIUM:** 2-4 LF data points, or external-only with multiple sources
- 🔴 **LOW:** Single data point, >6 months old, or estimate-heavy

**Example:**
📊 **Market Absorption: 850K sqft/year**
🟢 **High Confidence** | Based on 12 active projects across 4 quarters (Q3 FY24-25 → Q2 FY25-26)
**Source:** LF Market Intelligence | Q2 FY25-26 + PropEquity Q4 2024 Report (accessed Dec 16, 2024, propequity.com/reports/q4-2024)

**External Source Citation (when used):**
✅ Source name + report/article title
✅ Publication date
✅ Date accessed (if web)
✅ URL (if publicly accessible)

---

## BUCKETING (FLEXIBLE NARRATIVE STRUCTURE) 🧩

**What Bucketing Means:**
- Give direction to the narrative
- Help explain how logic flows
- Improve clarity and decision readability

**What Bucketing is NOT:**
- A fixed template
- Mandatory sectioning
- A forced structure

**👉 Buckets exist ONLY to support explanation, and must adapt to the question.**

**Example Adaptive Buckets:**
- For pricing query: "Market Positioning → Comparable Projects → Price Recommendation"
- For feasibility query: "Land Economics → Development Metrics → Financial Viability"
- For absorption query: "Historical Trends → Current Velocity → Launch Sizing"

---

## PRESENTATION RULES ✨

**✅ DO:**
- Use emojis **only for structure** (📊, 🟢, ➡️)
- **Bold key numbers and conclusions**
- Always show **units** (₹/sqft, units, %, months, sqft)
- Prefer **CARPET area** when size is mentioned
- Show **confidence + rationale** for key insights
- **Cite external sources** with full details at each usage
- When using external data, **mention source name** to build trust

**❌ DO NOT:**
- Force sections that don't fit the question
- Make unjustified assumptions
- Use generic headers ("Analysis", "Overview")
- Repeatedly mention "LF" or "Knowledge Graph" (assume user knows data source)
- Use external sources without full citation

---

## FINAL CHECKLIST ✅

Before delivering response, verify:
✔ **Recent data used** (Q2 FY25-26 → Q3 FY24-25 for quarterly trends)
✔ **All aggregations explained** (method + scope + justification)
✔ **All assumptions explicit** (labeled + justified + anchored)
✔ **IRR/NPV inputs prefilled** with market data (if applicable)
✔ **User confirmation requested** before final computation (if applicable)
✔ **3-4 follow-up questions** included (conversational, tied to analysis)
✔ **Confidence + rationale** shown for key insights
✔ **External sources fully cited** at each usage (if used)
✔ **Tables have observations + implications** (not just data)

**Deliver a proactive, intelligent, investor-grade response:**
**Market-led first → Personalized next → Computed last**

---

**User Query:** {user_query}"""

            # Create interaction with function tools only
            # Note: Interactions API only supports model, input, and tools parameters
            interaction = self.client.interactions.create(
                model=self.model,
                input=formatted_input,
                tools=tools
            )

            # Check for function calls (KG or quarterly market or chart)
            function_results = None
            chart_spec = None  # Will hold chart specification if generate_chart is called
            tool_used = "knowledge_graph"  # Default

            for output in interaction.outputs:
                if hasattr(output, 'type') and output.type == "function_call":
                    # Execute function based on name
                    if output.name == "liases_foras_lookup":
                        function_results = self._execute_kg_function(
                            output.name,
                            dict(output.arguments)
                        )
                        tool_used = "knowledge_graph"
                    elif output.name == "getDistanceFromProject":
                        function_results = self._execute_distance_function(
                            dict(output.arguments)
                        )
                        tool_used = "distance_calculation"
                    elif output.name == "find_projects_within_radius":
                        function_results = self._execute_proximity_function(
                            dict(output.arguments)
                        )
                        tool_used = "proximity_search"
                    elif output.name == "generate_location_map_with_poi":
                        function_results = self._execute_map_visualization_function(
                            dict(output.arguments)
                        )
                        tool_used = "map_visualization"
                    elif output.name == "quarterly_market_lookup":
                        function_results = self._execute_quarterly_market_function(
                            output.name,
                            dict(output.arguments)
                        )
                        tool_used = "quarterly_market_kg"

                        # AUTO-CHARTING: Generate chart automatically for quarterly data
                        try:
                            from app.services.chart_service import get_chart_service
                            chart_service = get_chart_service()

                            print(f"[AUTO-CHART] Function results type: {type(function_results)}")
                            print(f"[AUTO-CHART] Has 'quarters' key: {'quarters' in function_results if isinstance(function_results, dict) else False}")

                            # Extract quarterly data from function results
                            if isinstance(function_results, dict) and "quarters" in function_results:
                                quarterly_data = function_results["quarters"]
                                print(f"[AUTO-CHART] Found {len(quarterly_data)} quarters")

                                # Prepare data for charting (extract key metrics)
                                chart_data = []
                                for q in quarterly_data:
                                    chart_row = {
                                        "quarter": q.get("quarter", ""),  # Fixed: was "quarter_name"
                                        "supply": q.get("layer0", {}).get("supply_units", {}).get("value", 0),  # Fixed: was "total_supply_units"
                                        "sales": q.get("layer0", {}).get("sales_units", {}).get("value", 0)  # Fixed: was "total_sold_units"
                                    }
                                    chart_data.append(chart_row)

                                print(f"[AUTO-CHART] Prepared {len(chart_data)} data points")
                                print(f"[AUTO-CHART] Sample data: {chart_data[0] if chart_data else 'None'}")

                                # Generate chart if we have data
                                if chart_data and len(chart_data) >= 2:
                                    print(f"[AUTO-CHART] Generating chart...")
                                    chart_result = chart_service.auto_generate_chart(
                                        data=chart_data,
                                        chart_type="line",  # Force line chart for time-series
                                        title="Quarterly Market Trends",
                                        description="Quarterly supply and sales data"
                                    )
                                    print(f"[AUTO-CHART] Chart result status: {chart_result.get('status')}")
                                    if chart_result.get("status") == "success":
                                        # CRITICAL: Must use nonlocal to update the outer chart_spec variable
                                        chart_spec_temp = chart_result.get("chart")
                                        print(f"[AUTO-CHART] ✅ Chart spec generated! Type: {chart_spec_temp.get('chart_type') if chart_spec_temp else 'None'}")
                                        # Update the outer chart_spec (Python scoping - this WILL work)
                                        chart_spec = chart_spec_temp
                                else:
                                    print(f"[AUTO-CHART] ✗ Not enough data for chart (need >=2, have {len(chart_data)})")
                        except Exception as chart_error:
                            # Don't fail the whole request if charting fails
                            print(f"[AUTO-CHART] ✗ Exception: {chart_error}")
                            import traceback
                            traceback.print_exc()

                    elif output.name == "unit_size_range_lookup":
                        function_results = self._execute_unit_size_range_function(
                            dict(output.arguments)
                        )
                        tool_used = "unit_size_range_kg"

                    elif output.name == "unit_ticket_size_lookup":
                        function_results = self._execute_unit_ticket_size_function(
                            dict(output.arguments)
                        )
                        tool_used = "unit_ticket_size_kg"

                    elif output.name == "generate_chart":
                        chart_results = self._execute_chart_function(
                            dict(output.arguments)
                        )
                        # Extract chart specification for frontend rendering
                        if chart_results.get("status") == "success":
                            chart_spec = chart_results.get("chart")
                        function_results = chart_results
                        tool_used = "chart_visualization"
                    else:
                        continue  # Unknown function, skip

                    # Send results back to Gemini for final answer synthesis
                    final_interaction = self.client.interactions.create(
                        model=self.model,
                        previous_interaction_id=interaction.id,
                        input=[{
                            "type": "function_result",
                            "name": output.name,
                            "call_id": output.id,
                            "result": str(function_results)
                        }]
                    )

                    # Get final answer
                    answer = self._extract_text(final_interaction)

                    # Post-process answer for calculated metrics (PSF Gap, MOI)
                    answer = self._post_process_answer(user_query, answer, function_results)
                    break
            else:
                # No function call - direct answer (shouldn't happen with "ALWAYS" directive)
                answer = self._extract_text(interaction)
                answer = self._post_process_answer(user_query, answer, None)

            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            print(f"[AUTO-CHART-FINAL] Returning chart_spec: {'PRESENT ✅' if chart_spec else 'MISSING ✗'}")
            if chart_spec:
                print(f"[AUTO-CHART-FINAL] Chart type: {chart_spec.get('chart_type', 'N/A')}")

            return ATLASResponse(
                answer=answer,
                execution_time_ms=execution_time,
                tool_used=tool_used,
                interaction_id=interaction.id,
                function_results=function_results,
                chart_spec=chart_spec  # Include chart specification if available
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ATLASResponse(
                answer=f"Error: {str(e)}",
                execution_time_ms=execution_time,
                tool_used=None,
                interaction_id=None,
                function_results=None
            )

    def _execute_kg_function(self, function_name: str, arguments: Dict) -> Dict:
        """
        Execute Knowledge Graph function

        Args:
            function_name: Function to call
            arguments: Function arguments

        Returns:
            Function execution results
        """
        if not self.kg_adapter:
            return {"error": "KG adapter not configured"}

        try:
            query_type = arguments.get("query_type")
            project_name = arguments.get("project_name")
            location = arguments.get("location")

            if query_type == "get_project_by_name" and project_name:
                # Fetch ALL project data - let LLM interpret which fields answer the question
                data = self.kg_adapter.get_project_metadata(project_name)
                # Return complete project data for LLM to analyze
                return {
                    "project": project_name,
                    "data": data,
                    "note": "All project attributes returned. Analyze the data to answer the user's question."
                }

            elif query_type == "get_project_metrics" and project_name:
                # Get ALL metrics - let LLM interpret
                data = self.kg_adapter.get_project_metadata(project_name)
                return {
                    "project": project_name,
                    "metrics": data,
                    "note": "All metrics returned. Find the relevant data to answer the question."
                }

            elif query_type == "list_projects_by_location" and location:
                # KG adapter has already been switched to the correct city via city-aware routing
                # get_all_projects() returns projects for the current city (Kolkata, Pune, etc.)
                # NO FILTERING NEEDED - the city routing handles this
                all_projects = self.kg_adapter.get_all_projects()
                return {"location": location, "projects": all_projects}

            elif query_type == "get_all_projects_with_data":
                # Get ALL projects with base data + pre-calculated derived metrics for FAST filtering/sorting
                all_project_names = self.kg_adapter.get_all_projects()

                # Initialize generic formula calculator
                from app.services.derived_metrics_calculator import get_calculator
                calculator = get_calculator()

                projects_data = []
                for project_name in all_project_names:
                    data = self.kg_adapter.get_project_metadata(project_name)

                    # Pre-calculate ALL derived metrics using GENERIC formula calculator
                    # This reads formulas from Excel and evaluates them locally - NO hardcoded logic!
                    if isinstance(data, dict):
                        derived = calculator.calculate_all(data)
                        # Merge derived metrics into data
                        data.update(derived)

                    projects_data.append({
                        "projectName": project_name,
                        "data": data
                    })

                return {
                    "total_projects": len(projects_data),
                    "projects": projects_data,
                    "note": f"""All projects with base data + {len(calculator.formulas)} pre-calculated derived metrics returned for FAST filtering/sorting.

Derived metrics are calculated locally using formulas from LF-Layers_FULLY_ENRICHED_ALL_36.xlsx.
All calculations happen on this machine (cheap local hardware), not via LLM.

You can now instantly sort, filter, calculate averages/medians, find top-N on any attribute."""
                }

            else:
                return {"error": "Invalid query parameters. Provide query_type and project_name or location."}

        except Exception as e:
            return {"error": str(e)}

    def _post_process_answer(self, user_query: str, answer: str, function_results: Optional[Dict]) -> str:
        """
        Post-process answer to enforce proper formatting for calculated metrics

        This bypasses model instruction-following limitations by programmatically
        enforcing the format for PSF Gap and MOI queries.

        Args:
            user_query: Original user query
            answer: Model-generated answer
            function_results: Results from KG function call

        Returns:
            Formatted answer with proper structure
        """
        import re

        query_lower = user_query.lower()

        # Detect location query and remove coordinates from answer
        location_keywords = ["where is", "location of", "location", "address", "where can i find"]
        if any(keyword in query_lower for keyword in location_keywords):
            # Remove latitude/longitude mentions (comprehensive patterns)
            answer = re.sub(r'The\s+(approximate\s+)?coordinates\s+are.*?\.', '', answer, flags=re.IGNORECASE)
            answer = re.sub(r'The\s+(latitude|longitude)\s+is.*?\.', '', answer, flags=re.IGNORECASE)
            answer = re.sub(r'\*\*?Latitude:?\*\*?:?\s*[\d.]+°?', '', answer, flags=re.IGNORECASE)
            answer = re.sub(r'\*\*?Longitude:?\*\*?:?\s*[\d.]+°?', '', answer, flags=re.IGNORECASE)
            answer = re.sub(r'[\d.]+\s*\(latitude\)', '', answer, flags=re.IGNORECASE)
            answer = re.sub(r'[\d.]+\s*\(longitude\)', '', answer, flags=re.IGNORECASE)
            answer = re.sub(r'GPS Coordinates:?.*?(?=\n\n|\*|$)', '', answer, flags=re.IGNORECASE | re.DOTALL)
            # NEW: Remove "situated at latitude X and longitude Y" pattern
            answer = re.sub(r'It\s+is\s+situated\s+at\s+latitude\s+[\d.]+\s+and\s+longitude\s+[\d.]+\.?', '', answer, flags=re.IGNORECASE)
            answer = re.sub(r'[Ss]ituated\s+at\s+latitude\s+[\d.]+\s+and\s+longitude\s+[\d.]+\.?', '', answer, flags=re.IGNORECASE)
            answer = re.sub(r'at\s+latitude\s+[\d.]+\s+and\s+longitude\s+[\d.]+\.?', '', answer, flags=re.IGNORECASE)
            # Clean up multiple newlines and spaces
            answer = re.sub(r'\n{3,}', '\n\n', answer)
            answer = re.sub(r'  +', ' ', answer)
            answer = answer.strip()
            return answer

        # Detect PSF Gap query
        if "psf gap" in query_lower:
            return self._format_psf_gap_answer(answer, function_results)

        # Detect MOI query
        if "moi" in query_lower or "months of inventory" in query_lower:
            return self._format_moi_answer(answer, function_results)

        # For other queries, return as-is
        return answer

    def _format_psf_gap_answer(self, answer: str, function_results: Optional[Dict]) -> str:
        """Format PSF Gap answer with detailed structure"""
        import re

        # Extract project name from answer or function results
        project_name = "the project"
        if function_results and "project" in function_results:
            project_name = function_results["project"]

        # Try to extract numeric values from the answer
        launch_psf = None
        current_psf = None
        gap = None
        launch_date = None

        # Look for PSF Gap value in answer
        gap_match = re.search(r'psf gap.*?(-?\d+)', answer, re.IGNORECASE)
        if gap_match:
            gap = int(gap_match.group(1))

        # Try to extract from function results
        if function_results and "data" in function_results:
            data = function_results["data"]
            if isinstance(data, dict):
                launch_psf = data.get("launchPricePSF")
                current_psf = data.get("currentPricePSF")
                launch_date = data.get("launchDate")  # Extract launch date

                if launch_psf and current_psf:
                    gap = launch_psf - current_psf

        # If we couldn't extract the data, return original answer
        if gap is None and launch_psf is None and current_psf is None:
            return answer

        # Format numbers with Indian comma notation
        def format_indian(num):
            if num is None:
                return "N/A"
            s = f"{int(num):,}"
            return s.replace(",", "_TEMP_").replace("_TEMP_", ",")  # Already formatted

        # Generate formatted answer
        gap_formatted = format_indian(abs(gap)) if gap is not None else "N/A"
        launch_formatted = format_indian(launch_psf)
        current_formatted = format_indian(current_psf)

        # Determine insight based on gap value
        if gap is None:
            insight = "Unable to calculate PSF Gap - missing data."
        elif abs(gap) < 100:
            insight = f"This is actually quite positive! The PSF has marginally {'decreased' if gap > 0 else 'increased'} by just **Rs.{gap_formatted}** since launch, which indicates stable pricing in the market. This level of price stability suggests healthy demand and good developer credibility."
        elif gap > 100:
            insight = f"Hmm, this needs attention. The PSF has dropped by **Rs.{gap_formatted}** since launch, which suggests some pricing pressure in the market. This could be due to slower absorption or competitive pressure from nearby projects."
        else:  # gap < -100
            insight = f"Oh! This is excellent news! The PSF has actually increased by **Rs.{gap_formatted}** since launch, showing strong appreciation. This indicates robust demand and validates the developer's pricing strategy!"

        # Build launch date context if available
        launch_context = f" (**Launch Date:** {launch_date})" if launch_date else ""

        formatted_answer = f"""**Definition:**
PSF Gap represents the difference between the Launch Price PSF (initial offering price per square foot) and the Current Price PSF (actual market realization price per square foot). It indicates how pricing has evolved since the project launch.

**Formula:**
PSF Gap = Launch Price PSF - Current Price PSF

**Calculation:**
• Launch Price PSF: **Rs.{launch_formatted}/Sq.Ft.{launch_context}** (from Liases Foras data)
• Current Price PSF: **Rs.{current_formatted}/Sq.Ft.** (from Liases Foras data)
• PSF Gap = **Rs.{launch_formatted}/Sq.Ft.** - **Rs.{current_formatted}/Sq.Ft.** = **Rs.{gap_formatted}/Sq.Ft.**

**Result:**
The PSF Gap for {project_name} is **Rs.{gap_formatted}/Sq.Ft.**

**Insight:**
{insight}

*Source: Liases Foras - Pricing Analytics Database*"""

        return formatted_answer

    def _format_moi_answer(self, answer: str, function_results: Optional[Dict]) -> str:
        """Format MOI answer with 3-step calculation"""
        import re

        # Extract project name from answer
        project_name = "the project"
        if function_results and "project" in function_results:
            project_name = function_results["project"]
        else:
            # Try to extract from answer
            name_match = re.search(r'for\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', answer)
            if name_match:
                project_name = name_match.group(1)

        total_supply = None
        unsold_percent = None
        annual_sales = None

        # Try to extract data from function results first
        if function_results and "data" in function_results:
            data = function_results["data"]
            if isinstance(data, dict):
                total_supply = data.get("totalSupplyUnits")
                unsold_percent = data.get("unsoldPercent")
                annual_sales = data.get("annualSalesUnits")

        # If no function results, try to extract from answer text
        if not total_supply or not annual_sales or unsold_percent is None:
            # Extract total supply units
            supply_match = re.search(r'(\d+,?\d*)\s+total\s+units', answer, re.IGNORECASE)
            if supply_match:
                total_supply = int(supply_match.group(1).replace(',', ''))

            # Extract unsold percentage (try multiple patterns)
            if unsold_percent is None:
                # Pattern 1: "11% unsold" or "unsold 11%"
                unsold_match = re.search(r'(\d+\.?\d*)%\s+(?:of.*?)?unsold|unsold.*?(\d+\.?\d*)%', answer, re.IGNORECASE)
                if unsold_match:
                    unsold_percent = float(unsold_match.group(1) or unsold_match.group(2))
                else:
                    # Pattern 2: "1 - 0.89 sold" (calculate unsold from sold)
                    sold_match = re.search(r'1\s*-\s*0\.(\d+)\s+sold|0\.(\d+)\s+sold', answer, re.IGNORECASE)
                    if sold_match:
                        sold_decimal = float(f"0.{sold_match.group(1) or sold_match.group(2)}")
                        unsold_percent = (1 - sold_decimal) * 100

            # Extract annual sales (try multiple patterns)
            annual_match = re.search(r'(\d+,?\d*)\s+annual\s+sales|annual\s+sales.*?(\d+,?\d*)\s+units', answer, re.IGNORECASE)
            if annual_match:
                annual_sales = int((annual_match.group(1) or annual_match.group(2)).replace(',', ''))
            else:
                # Alternative pattern: "**Annual Sales Units:** 527"
                alt_match = re.search(r'annual\s+sales\s+units.*?(\d+,?\d*)', answer, re.IGNORECASE)
                if alt_match:
                    annual_sales = int(alt_match.group(1).replace(',', ''))

        if total_supply and unsold_percent is not None and annual_sales:
            # Calculate MOI
            unsold_units = total_supply * (unsold_percent / 100)
            monthly_sales = annual_sales / 12
            moi = unsold_units / monthly_sales if monthly_sales > 0 else 0

            formatted_answer = f"""**Definition:**
Months of Inventory (MOI) represents how many months it would take to sell all unsold units at the current sales rate. It's a key indicator of inventory turnover and market demand.

**Formula:**
MOI = Unsold Units ÷ Monthly Units Sold

**Calculation:**

• **Step 1 - Calculate Unsold Units:**
  - Total Supply Units: **{total_supply:,} units** (from Liases Foras data)
  - Unsold Percentage: **{unsold_percent}%** (from Liases Foras data)
  - Unsold Units = {total_supply:,} × ({unsold_percent}/100) = **{unsold_units:,.0f} units**

• **Step 2 - Calculate Monthly Units Sold:**
  - Annual Sales Units: **{annual_sales:,} units** (from Liases Foras data)
  - Monthly Units Sold = {annual_sales:,} ÷ 12 = **{monthly_sales:,.2f} units/month**

• **Step 3 - Calculate MOI:**
  - MOI = {unsold_units:,.0f} ÷ {monthly_sales:,.2f} = **{moi:,.2f} months**

**Result:**
The Months of Inventory (MOI) for {project_name} is **{moi:,.2f} months**.

**Insight:**
{'This is excellent! An MOI below 6 months indicates strong market demand and healthy inventory turnover.' if moi < 6 else 'This is reasonable. An MOI between 6-12 months suggests moderate demand with stable inventory levels.' if moi < 12 else 'This needs attention. An MOI above 12 months indicates slower absorption and may require pricing or marketing adjustments.'}

*Source: Liases Foras - Market Intelligence Database*"""

            return formatted_answer

        # If we couldn't extract data, return original answer
        return answer

    def _execute_distance_function(self, arguments: Dict) -> Dict:
        """
        Execute distance calculation function using FunctionRegistry

        Args:
            arguments: Function arguments (source_project, target_project)

        Returns:
            Function execution results
        """
        try:
            from app.services.function_registry import get_function_registry

            registry = get_function_registry(city=self.current_city)
            result = registry.execute_function("getDistanceFromProject", arguments)

            return result
        except Exception as e:
            return {
                "error": str(e),
                "source_project": arguments.get("source_project"),
                "target_project": arguments.get("target_project")
            }

    def _execute_proximity_function(self, arguments: Dict) -> Dict:
        """
        Execute proximity search function using FunctionRegistry

        Args:
            arguments: Function arguments (center_project, radius_km)

        Returns:
            Function execution results
        """
        try:
            from app.services.function_registry import get_function_registry

            registry = get_function_registry(city=self.current_city)
            result = registry.execute_function("find_projects_within_radius", arguments)

            return result
        except Exception as e:
            return {
                "error": str(e),
                "center_project": arguments.get("center_project"),
                "radius_km": arguments.get("radius_km")
            }

    def _execute_map_visualization_function(self, arguments: Dict) -> Dict:
        """
        Execute map visualization function using FunctionRegistry

        Args:
            arguments: Function arguments (project_name, latitude, longitude, city, zoom)

        Returns:
            Function execution results with map URLs and POI details
        """
        try:
            from app.services.function_registry import get_function_registry

            registry = get_function_registry(city=self.current_city)
            result = registry.execute_function("generate_location_map_with_poi", arguments)

            return result
        except Exception as e:
            return {
                "error": str(e),
                "project_name": arguments.get("project_name"),
                "latitude": arguments.get("latitude"),
                "longitude": arguments.get("longitude")
            }

    def _execute_quarterly_market_function(self, function_name: str, arguments: Dict) -> Dict:
        """
        Execute quarterly market data functions using FunctionRegistry

        Args:
            function_name: Name of quarterly function (get_quarters_by_year_range, get_recent_quarters, get_all_quarterly_data)
            arguments: Function arguments (start_year, end_year, n, etc.)

        Returns:
            Quarterly market data with location context and aggregated metrics
        """
        try:
            from app.services.function_registry import get_function_registry

            registry = get_function_registry(city=self.current_city)
            result = registry.execute_function(function_name, arguments)

            return result
        except Exception as e:
            return {
                "error": str(e),
                "function_name": function_name,
                "arguments": arguments
            }

    def _execute_chart_function(self, arguments: Dict) -> Dict:
        """
        Execute chart generation function using FunctionRegistry

        Args:
            arguments: Chart function arguments (data, chart_type, title, description)

        Returns:
            Chart specification with Plotly-compatible structure
        """
        try:
            from app.services.function_registry import get_function_registry

            registry = get_function_registry(city=self.current_city)
            result = registry.execute_function("generate_chart", arguments)

            return result
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "arguments": arguments
            }

    def _execute_unit_size_range_function(self, arguments: Dict) -> Dict:
        """
        Execute unit size range lookup function using FunctionRegistry

        Args:
            arguments: Function arguments (flat_type, min_efficiency, min_sales, size_range, top_n, metric)

        Returns:
            Size range data with Layer 0 + Layer 1 + Layer 2 derivatives, location context, aggregated metrics
        """
        try:
            from app.services.function_registry import get_function_registry

            registry = get_function_registry(city=self.current_city)
            result = registry.execute_function("unit_size_range_lookup", arguments)

            return result
        except Exception as e:
            return {
                "error": str(e),
                "function_name": "unit_size_range_lookup",
                "arguments": arguments
            }

    def _execute_unit_ticket_size_function(self, arguments: Dict) -> Dict:
        """
        Execute unit ticket size lookup function using FunctionRegistry

        Args:
            arguments: Function arguments (price_lacs, min_efficiency, min_sales, max_affordability, top_n, metric)

        Returns:
            Ticket size range data with Layer 0 + Layer 1 + Layer 2 derivatives, location context, aggregated metrics
        """
        try:
            from app.services.function_registry import get_function_registry

            registry = get_function_registry(city=self.current_city)
            result = registry.execute_function("unit_ticket_size_lookup", arguments)

            return result
        except Exception as e:
            return {
                "error": str(e),
                "function_name": "unit_ticket_size_lookup",
                "arguments": arguments
            }

    def _extract_text(self, interaction) -> str:
        """Extract text from interaction outputs and strip formatting instructions"""
        text = ""
        if hasattr(interaction, 'outputs') and interaction.outputs:
            for output in interaction.outputs:
                if hasattr(output, 'type') and output.type == "text":
                    text += output.text
                elif hasattr(output, 'text'):  # Fallback
                    text += output.text

        # Strip out formatting instructions if they were echoed back by the LLM
        # Remove everything from the start up to and including "User Query:" separator
        import re
        # Pattern to match the entire formatting instruction block
        pattern = r'🚨\s*CRITICAL FORMATTING INSTRUCTIONS.*?---\s*\*\*User Query:\*\*.*?---\s*'
        text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

        # Also remove if it appears at the start without markdown
        if text.startswith('🚨'):
            # Find where the actual answer starts (after formatting instructions)
            lines = text.split('\n')
            answer_start_idx = 0
            for i, line in enumerate(lines):
                # Look for the end of formatting instructions (separator line or bullet point start)
                if line.strip().startswith('•') or line.strip().startswith('-'):
                    answer_start_idx = i
                    break
                if '---' in line and i > 5:  # Skip first few lines with separators in instructions
                    answer_start_idx = i + 1
                    break
            if answer_start_idx > 0:
                text = '\n'.join(lines[answer_start_idx:])

        return text.strip()


# Global singleton
_atlas_performance_adapter = None


def get_atlas_performance_adapter(api_key: Optional[str] = None, kg_adapter=None) -> ATLASPerformanceAdapter:
    """
    Get or create ATLAS Performance Adapter singleton

    Args:
        api_key: Optional Google API key
        kg_adapter: Optional Knowledge Graph adapter

    Returns:
        ATLASPerformanceAdapter instance
    """
    global _atlas_performance_adapter

    if _atlas_performance_adapter is None:
        _atlas_performance_adapter = ATLASPerformanceAdapter(api_key=api_key)
        if kg_adapter:
            _atlas_performance_adapter.set_kg_adapter(kg_adapter)

    return _atlas_performance_adapter
