"""
Attribute Resolver Node - LangGraph Node 2

Resolves attributes using Vector DB semantic search.

Flow:
1. Takes raw attributes from entity extraction
2. Uses Vector DB to search for matching canonical attributes
3. Returns rich metadata about each attribute (unit, dimension, formula, layer)
4. Updates state with resolved_attributes
5. Routes to entity_resolver_node

Key Principle: Vector DB provides SCHEMA understanding (what attributes mean),
NOT data values. This is purely metadata lookup.
"""

from typing import Dict, List
from app.orchestration.state_schema import QueryState
from app.ports.vector_db_port import VectorDBPort


def attribute_resolver_node(state: QueryState, vector_db: VectorDBPort) -> QueryState:
    """
    Node 2: Resolve attributes using Vector DB semantic search

    Args:
        state: Current QueryState with raw_entities
        vector_db: Vector DB adapter instance (injected dependency)

    Returns:
        Updated state with resolved_attributes

    State Updates:
        - resolved_attributes: List of attribute metadata dicts
        - attribute_search_results: Raw search results with scores
        - execution_path: Appends "attribute_resolver"
    """
    print(f"\n{'='*80}")
    print(f"NODE 2: ATTRIBUTE RESOLVER")
    print(f"{'='*80}")

    # Track execution
    state['execution_path'].append('attribute_resolver')

    # Get raw attributes from entity extraction
    raw_attributes = state.get('raw_entities', {}).get('attributes', [])

    if not raw_attributes:
        print(f"⚠ No attributes mentioned in query, inferring from intent...")

        # For queries without explicit attributes, use query itself for semantic search
        raw_attributes = [state['query']]

    print(f"Raw attributes to resolve: {raw_attributes}")

    # Resolve each attribute using Vector DB
    resolved_attributes = []
    all_search_results = []

    for raw_attr in raw_attributes:
        print(f"\n[Resolving] '{raw_attr}'")

        try:
            # Semantic search in Vector DB
            search_results = vector_db.search_attributes(query=raw_attr, k=3)

            if search_results:
                # Take top result as the resolved attribute
                top_result = search_results[0]
                resolved_attributes.append(top_result)

                print(f"  ✓ Matched: {top_result.get('Target Attribute')}")
                print(f"    - Unit: {top_result.get('Unit')}")
                print(f"    - Dimension: {top_result.get('Dimension')}")
                print(f"    - Layer: {top_result.get('Layer')}")

                # Store all search results for debugging
                all_search_results.extend(search_results)
            else:
                print(f"  ✗ No match found for '{raw_attr}'")

        except Exception as e:
            print(f"  ✗ Error resolving '{raw_attr}': {e}")

    # Update state
    state['resolved_attributes'] = resolved_attributes
    state['attribute_search_results'] = all_search_results

    # Summary
    print(f"\n{'─'*80}")
    print(f"Resolved {len(resolved_attributes)} attributes:")
    for attr in resolved_attributes:
        print(f"  • {attr.get('Target Attribute')} ({attr.get('Layer')})")
    print(f"{'='*80}\n")

    return state


def get_attribute_layers(state: QueryState) -> List[str]:
    """
    Helper: Extract unique layers from resolved attributes

    Args:
        state: Current QueryState with resolved_attributes

    Returns:
        List of unique layer identifiers (e.g., ["L0", "L1"])
    """
    layers = set()
    for attr in state.get('resolved_attributes', []):
        layer = attr.get('Layer', '')
        if layer:
            layers.add(layer)
    return sorted(list(layers))


def requires_computation(state: QueryState) -> bool:
    """
    Helper: Check if any resolved attributes require computation

    Args:
        state: Current QueryState with resolved_attributes

    Returns:
        True if any attribute is from Layer 2 or Layer 3 (requires computation)
    """
    layers = get_attribute_layers(state)
    return any(layer in ['L2', 'L3'] for layer in layers)
