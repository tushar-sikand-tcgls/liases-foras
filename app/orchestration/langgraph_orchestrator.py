"""
LangGraph Orchestrator - Main query orchestration state machine

This is the central orchestrator that wires together all 8 nodes into a
LangGraph state machine with conditional routing based on intent.

Three main branches:
1. OBJECTIVE: Direct retrieval → Answer
2. ANALYTICAL: Aggregation/comparison → Answer
3. FINANCIAL: Multi-turn with parameter gathering → Computation → Answer

Key Features:
- Hexagonal architecture with dependency injection
- Conditional routing based on intent and state
- Multi-turn conversation support
- Comprehensive error handling
- Performance monitoring
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from app.orchestration.state_schema import QueryState, create_initial_state

# Import all nodes
from app.nodes.intent_classifier_node import intent_classifier_node
from app.nodes.attribute_resolver_node import attribute_resolver_node
from app.nodes.entity_resolver_node import entity_resolver_node
from app.nodes.kg_query_planner_node import kg_query_planner_node
from app.nodes.kg_executor_node import kg_executor_node, fetch_cash_flow_data_if_needed
from app.nodes.parameter_gatherer_node import parameter_gatherer_node
from app.nodes.computation_node import computation_node
from app.nodes.answer_composer_node import answer_composer_node

# Import port interfaces
from app.ports.vector_db_port import VectorDBPort
from app.ports.knowledge_graph_port import KnowledgeGraphPort
from app.ports.llm_port import LLMPort

# Import adapters (for default initialization)
# TEMPORARY: Using ChromaDB until Gemini File Search SDK configuration is fixed
from app.adapters.chroma_adapter import get_chroma_adapter
# from app.adapters.gemini_file_search_adapter import get_gemini_file_search_adapter
from app.adapters.data_service_kg_adapter import get_data_service_kg_adapter
from app.adapters.gemini_llm_adapter import get_gemini_llm_adapter

import time


class LangGraphOrchestrator:
    """
    Main orchestrator using LangGraph state machine with hexagonal architecture

    This orchestrator wires together 8 nodes with conditional routing:
    - Intent classification
    - Attribute resolution (Vector DB semantic search)
    - Entity resolution (KG fuzzy matching)
    - Query planning (LLM-driven)
    - KG execution (data retrieval)
    - Parameter gathering (multi-turn support)
    - Computation (deterministic financial calculations)
    - Answer composition (LLM-driven with provenance)
    """

    def __init__(
        self,
        vector_db: Optional[VectorDBPort] = None,
        kg: Optional[KnowledgeGraphPort] = None,
        llm: Optional[LLMPort] = None
    ):
        """
        Initialize orchestrator with injected dependencies

        Args:
            vector_db: Vector DB adapter (default: Gemini File Search)
            kg: Knowledge Graph adapter (default: DataService)
            llm: LLM adapter (default: Gemini)
        """
        # Use provided adapters or initialize defaults
        # TEMPORARY: Using ChromaDB until Gemini File Search SDK configuration is fixed
        self.vector_db = vector_db or get_chroma_adapter()
        self.kg = kg or get_data_service_kg_adapter()
        self.llm = llm or get_gemini_llm_adapter()

        # Build LangGraph state machine
        self.graph = self._build_graph()

        print(f"\n{'='*80}")
        print(f"LANGGRAPH ORCHESTRATOR INITIALIZED")
        print(f"{'='*80}")
        print(f"  Vector DB: {type(self.vector_db).__name__}")
        print(f"  Knowledge Graph: {type(self.kg).__name__}")
        print(f"  LLM: {type(self.llm).__name__}")
        print(f"{'='*80}\n")

    def _build_graph(self) -> StateGraph:
        """
        Build LangGraph state machine with all nodes and routing

        Returns:
            Compiled StateGraph ready for execution
        """
        # Create state graph
        workflow = StateGraph(QueryState)

        # ====================================================================
        # ADD NODES (with dependency injection via lambda wrappers)
        # ====================================================================

        # Node 1: Intent Classifier
        workflow.add_node(
            "intent_classifier",
            lambda state: intent_classifier_node(state, self.llm)
        )

        # Node 2: Attribute Resolver
        workflow.add_node(
            "attribute_resolver",
            lambda state: attribute_resolver_node(state, self.vector_db)
        )

        # Node 3: Entity Resolver
        workflow.add_node(
            "entity_resolver",
            lambda state: entity_resolver_node(state, self.kg)
        )

        # Node 4: KG Query Planner
        workflow.add_node(
            "kg_query_planner",
            lambda state: kg_query_planner_node(state, self.llm)
        )

        # Node 5: KG Executor
        workflow.add_node(
            "kg_executor",
            lambda state: kg_executor_node(state, self.kg)
        )

        # Node 6: Parameter Gatherer
        workflow.add_node(
            "parameter_gatherer",
            lambda state: parameter_gatherer_node(state, self.llm)
        )

        # Node 7: Computation
        workflow.add_node(
            "computation",
            lambda state: computation_node(state)
        )

        # Node 8: Answer Composer
        workflow.add_node(
            "answer_composer",
            lambda state: answer_composer_node(state, self.llm)
        )

        # ====================================================================
        # DEFINE ROUTING LOGIC
        # ====================================================================

        # Entry point: Always start with intent classification
        workflow.set_entry_point("intent_classifier")

        # Intent Classifier → Attribute Resolver (always)
        workflow.add_edge("intent_classifier", "attribute_resolver")

        # Attribute Resolver → Entity Resolver (always)
        workflow.add_edge("attribute_resolver", "entity_resolver")

        # Entity Resolver → KG Query Planner (always)
        workflow.add_edge("entity_resolver", "kg_query_planner")

        # KG Query Planner → KG Executor (always)
        workflow.add_edge("kg_query_planner", "kg_executor")

        # KG Executor → Conditional routing based on intent
        workflow.add_conditional_edges(
            "kg_executor",
            self._route_after_kg_execution,
            {
                "parameter_gatherer": "parameter_gatherer",  # Financial query
                "answer_composer": "answer_composer"         # Objective/Analytical
            }
        )

        # Parameter Gatherer → Conditional routing based on parameter completeness
        workflow.add_conditional_edges(
            "parameter_gatherer",
            self._route_after_parameter_gathering,
            {
                "computation": "computation",                # All params present
                "answer_composer": "answer_composer"         # Need clarification
            }
        )

        # Computation → Answer Composer (always)
        workflow.add_edge("computation", "answer_composer")

        # Answer Composer → END (always)
        workflow.add_edge("answer_composer", END)

        # Compile graph
        compiled_graph = workflow.compile()

        return compiled_graph

    def _route_after_kg_execution(self, state: QueryState) -> str:
        """
        Routing function: Decide next step after KG execution

        Args:
            state: Current QueryState

        Returns:
            "parameter_gatherer" for financial queries, "answer_composer" otherwise
        """
        intent = state.get('intent', '')

        if intent == 'financial':
            # Financial queries need parameter checking
            return "parameter_gatherer"
        else:
            # Objective/Analytical queries can go straight to answer
            return "answer_composer"

    def _route_after_parameter_gathering(self, state: QueryState) -> str:
        """
        Routing function: Decide next step after parameter gathering

        Args:
            state: Current QueryState

        Returns:
            "computation" if all params present, "answer_composer" if need clarification
        """
        has_all_params = state.get('has_all_parameters', False)

        if has_all_params:
            # All parameters present - proceed to computation
            return "computation"
        else:
            # Missing parameters - compose clarification question
            return "answer_composer"

    def query(
        self,
        query: str,
        session_id: str = "default",
        conversation_history: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Execute query through LangGraph orchestrator

        Args:
            query: User's natural language query
            session_id: Session identifier for multi-turn conversations
            conversation_history: Previous conversation turns (if any)

        Returns:
            Dict with:
            - answer: Natural language answer
            - provenance: Full provenance trail
            - intent: Classified intent
            - execution_path: List of nodes executed
            - execution_time_ms: Total execution time
        """
        print(f"\n{'#'*80}")
        print(f"NEW QUERY: {query}")
        print(f"Session ID: {session_id}")
        print(f"{'#'*80}\n")

        start_time = time.time()

        # Create initial state
        initial_state = create_initial_state(
            query=query,
            session_id=session_id,
            conversation_history=conversation_history
        )

        # Execute graph
        try:
            final_state = self.graph.invoke(initial_state)

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            final_state['total_execution_time_ms'] = execution_time_ms

            # Build response
            response = {
                'answer': final_state.get('answer', 'No answer generated'),
                'provenance': final_state.get('provenance', {}),
                'intent': final_state.get('intent', 'unknown'),
                'subcategory': final_state.get('subcategory', ''),
                'execution_path': final_state.get('execution_path', []),
                'execution_time_ms': execution_time_ms,
                'next_action': final_state.get('next_action', 'answer'),
                'clarification_question': final_state.get('clarification_question'),
                'session_id': session_id
            }

            # Summary
            print(f"\n{'#'*80}")
            print(f"QUERY COMPLETE")
            print(f"{'#'*80}")
            print(f"  Intent: {response['intent']}")
            print(f"  Execution path: {' → '.join(response['execution_path'])}")
            print(f"  Execution time: {execution_time_ms:.2f}ms")
            print(f"  Next action: {response['next_action']}")
            print(f"{'#'*80}\n")

            return response

        except Exception as e:
            print(f"\n✗ ERROR IN ORCHESTRATION: {e}")
            import traceback
            traceback.print_exc()

            return {
                'answer': f"Error processing query: {str(e)}",
                'error': str(e),
                'intent': 'error',
                'execution_time_ms': (time.time() - start_time) * 1000,
                'session_id': session_id
            }

    def get_graph_visualization(self) -> str:
        """
        Get Mermaid diagram representation of the graph

        Returns:
            Mermaid diagram as string
        """
        # This would generate a Mermaid diagram showing the state machine
        # For now, return a simple text representation
        return """
        graph TD
            START([Start]) --> A[Intent Classifier]
            A --> B[Attribute Resolver]
            B --> C[Entity Resolver]
            C --> D[KG Query Planner]
            D --> E[KG Executor]
            E --> F{Intent?}
            F -->|Financial| G[Parameter Gatherer]
            F -->|Objective/Analytical| H[Answer Composer]
            G --> I{All params?}
            I -->|Yes| J[Computation]
            I -->|No| H
            J --> H
            H --> END([End])
        """


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_orchestrator_instance = None


def get_orchestrator(
    vector_db: Optional[VectorDBPort] = None,
    kg: Optional[KnowledgeGraphPort] = None,
    llm: Optional[LLMPort] = None
) -> LangGraphOrchestrator:
    """
    Get or create singleton orchestrator instance

    Args:
        vector_db: Optional Vector DB adapter
        kg: Optional Knowledge Graph adapter
        llm: Optional LLM adapter

    Returns:
        LangGraphOrchestrator singleton instance
    """
    global _orchestrator_instance

    if _orchestrator_instance is None:
        _orchestrator_instance = LangGraphOrchestrator(
            vector_db=vector_db,
            kg=kg,
            llm=llm
        )

    return _orchestrator_instance
