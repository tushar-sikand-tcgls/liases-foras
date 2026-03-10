"""
Intent Classifier Node - LangGraph Node 1

Classifies user query into one of three intents and extracts raw entities.

Flow:
1. Takes query + conversation history
2. Uses LLM to classify intent (objective/analytical/financial)
3. Extracts raw entities (projects, developers, locations, attributes)
4. Updates state with classification results
5. Routes to attribute_resolver_node

Key Principle: LLM provides intelligence for classification, but does NOT
invent any data. All entities are just recognized patterns, not validated facts.
"""

from typing import Dict
from app.orchestration.state_schema import QueryState
from app.ports.llm_port import LLMPort


def intent_classifier_node(state: QueryState, llm: LLMPort) -> QueryState:
    """
    Node 1: Classify intent and extract raw entities

    Args:
        state: Current QueryState with query and conversation_history
        llm: LLM adapter instance (injected dependency)

    Returns:
        Updated state with intent, subcategory, confidence, and raw_entities

    State Updates:
        - intent: "objective" | "analytical" | "financial"
        - subcategory: Specific query type
        - confidence: 0.0-1.0
        - classification_reasoning: LLM's explanation
        - raw_entities: Dict with projects, developers, locations, attributes lists
        - execution_path: Appends "intent_classifier"
    """
    print(f"\n{'='*80}")
    print(f"NODE 1: INTENT CLASSIFIER")
    print(f"{'='*80}")
    print(f"Query: {state['query']}")

    # Track execution
    if 'execution_path' not in state:
        state['execution_path'] = []
    state['execution_path'].append('intent_classifier')

    # Step 1: Classify intent
    print(f"\n[1/2] Classifying intent with LLM...")
    try:
        classification_result = llm.classify_intent(
            query=state['query'],
            conversation_history=state.get('conversation_history', [])
        )

        state['intent'] = classification_result['intent']
        state['subcategory'] = classification_result.get('subcategory', '')
        state['confidence'] = classification_result.get('confidence', 0.0)
        state['classification_reasoning'] = classification_result.get('reasoning', '')

        print(f"✓ Intent: {state['intent']} (confidence: {state['confidence']:.2f})")
        print(f"✓ Subcategory: {state['subcategory']}")
        print(f"✓ Reasoning: {state['classification_reasoning']}")

    except Exception as e:
        print(f"✗ Error classifying intent: {e}")
        state['error'] = f"Intent classification failed: {str(e)}"
        state['next_action'] = 'error'
        return state

    # Step 2: Extract raw entities
    print(f"\n[2/2] Extracting entities with LLM...")
    try:
        entities_result = llm.extract_entities(query=state['query'])

        state['raw_entities'] = {
            'projects': entities_result.get('projects', []),
            'developers': entities_result.get('developers', []),
            'locations': entities_result.get('locations', []),
            'attributes': entities_result.get('attributes', [])
        }

        print(f"✓ Projects: {state['raw_entities']['projects']}")
        print(f"✓ Developers: {state['raw_entities']['developers']}")
        print(f"✓ Locations: {state['raw_entities']['locations']}")
        print(f"✓ Attributes: {state['raw_entities']['attributes']}")

    except Exception as e:
        print(f"✗ Error extracting entities: {e}")
        # Non-fatal error - can proceed with empty entities
        state['raw_entities'] = {
            'projects': [],
            'developers': [],
            'locations': [],
            'attributes': []
        }

    print(f"\n{'='*80}")
    print(f"NODE 1 COMPLETE: Intent={state['intent']}, Entities extracted")
    print(f"{'='*80}\n")

    return state


def should_continue_after_classification(state: QueryState) -> bool:
    """
    Routing function: Check if we can proceed after intent classification

    Args:
        state: Current QueryState

    Returns:
        True if classification succeeded and we can continue, False if error
    """
    if state.get('error'):
        return False

    if not state.get('intent'):
        return False

    return True
