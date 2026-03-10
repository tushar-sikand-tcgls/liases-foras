"""
LLM Port - Interface for LLM-based Intelligence

This port defines the contract for LLM operations.
LLM provides intelligence: classification, planning, explanation.

Implementations: Gemini, OpenAI, Claude, etc.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any


class LLMPort(ABC):
    """Port for LLM-based intelligence and natural language processing"""

    @abstractmethod
    def classify_intent(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Classify user query intent into one of three categories

        Args:
            query: User's natural language query
            conversation_history: Optional conversation context

        Returns:
            Dict with:
            - intent: "objective" | "analytical" | "financial"
            - subcategory: Specific type within intent
            - confidence: 0.0-1.0
            - reasoning: Why this classification was chosen

        Example:
            classify_intent("What is the total units for Sara City?")
            ' {
                "intent": "objective",
                "subcategory": "direct_retrieval",
                "confidence": 0.95,
                "reasoning": "Direct request for specific attribute value"
              }
        """
        pass

    @abstractmethod
    def extract_entities(self, query: str) -> Dict:
        """
        Extract entities (projects, developers, locations) from query

        Args:
            query: User's natural language query

        Returns:
            Dict with:
            - projects: List[str]
            - developers: List[str]
            - locations: List[str]
            - attributes: List[str]

        Example:
            extract_entities("What is the sold % for Sara City in Chakan?")
            ' {
                "projects": ["Sara City"],
                "developers": [],
                "locations": ["Chakan"],
                "attributes": ["sold %"]
              }
        """
        pass

    @abstractmethod
    def plan_kg_queries(self, context: Dict) -> List[Dict]:
        """
        Generate structured KG query plan based on intent and entities

        Args:
            context: Dict with:
                - intent: str
                - attributes: List[str]
                - projects: List[str]
                - locations: List[str]
                - query: str (original user query)

        Returns:
            List of query plan dicts:
            [
              {
                "action": "fetch|aggregate|compare",
                "projects": List[str],
                "attributes": List[str],
                "filters": Dict,
                "aggregation": Optional[str]
              }
            ]

        Example:
            plan_kg_queries({
                "intent": "analytical",
                "attributes": ["Sold %"],
                "locations": ["Chakan"]
            })
            ' [
                {
                    "action": "aggregate",
                    "attributes": ["Sold %"],
                    "aggregation": "max",
                    "filters": {"location": "Chakan"}
                }
              ]
        """
        pass

    @abstractmethod
    def compose_answer(
        self,
        query: str,
        kg_data: Dict,
        computation_results: Optional[Dict] = None,
        attributes_metadata: Optional[List[Dict]] = None
    ) -> str:
        """
        Compose natural language answer with proper provenance

        Args:
            query: Original user query
            kg_data: Data fetched from KG
            computation_results: Optional computation results (IRR, NPV, etc.)
            attributes_metadata: Optional attribute metadata from Vector DB

        Returns:
            Natural language answer with provenance markers:
            - [DIRECT] for KG-retrieved values
            - [COMPUTED] for calculated values
            - [ASSUMED] for assumption-based values

        Example:
            compose_answer(
                query="What is the total units for Sara City?",
                kg_data={"Sara City.totalUnits": 3018},
                attributes_metadata=[{"name": "Total Units", "unit": "Units", ...}]
            )
            ' "Sara City has 3,018 units. [DIRECT - KG]

               This represents the total number of residential units in the project.

               [Provenance]
               - Data source: Knowledge Graph
               - Project: Sara City
               - Attribute: Total Units (Layer 0)
               - Last updated: 2024-Q4"
        """
        pass

    @abstractmethod
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

        Example:
            ask_clarification(
                missing_parameters=["discount_rate", "holding_period"],
                context={"intent": "financial", "subcategory": "IRR", "project": "Sara City"}
            )
            ' "To calculate IRR for Sara City, I need additional information:
               1. What is your expected holding period (in years)?
               2. What discount rate should I use? (e.g., 12%)

               Alternatively, I can estimate these based on market averages. Would you like me to proceed with estimates?"
        """
        pass

    @abstractmethod
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

        Example:
            Used for structured outputs like query plans, entity extraction, etc.
        """
        pass

    @abstractmethod
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

        Example:
            explain_calculation(
                calculation_type="IRR",
                inputs={"cash_flows": [100, 150, 200, 250]},
                result=18.7
            )
            ' "The Internal Rate of Return (IRR) is 18.7%.

               This represents the annualized rate of return that makes the net present value
               of all cash flows equal to zero.

               Cash flows used:
               - Year 0: Rs.100 Cr
               - Year 1: Rs.150 Cr
               - Year 2: Rs.200 Cr
               - Year 3: Rs.250 Cr

               An IRR of 18.7% indicates strong project performance, exceeding typical
               real estate benchmarks of 12-15%."
        """
        pass
