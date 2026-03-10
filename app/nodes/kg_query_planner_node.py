"""
KG Query Planner Node - LangGraph Node 4

Generates structured KG query plan using LLM.

Flow:
1. Takes intent, resolved attributes, and resolved entities
2. Uses LLM to generate structured query plan
3. Query plan specifies: action (fetch/aggregate/compare), projects, attributes, filters
4. Updates state with kg_query_plan
5. Routes to kg_executor_node

Key Principle: LLM provides planning intelligence (HOW to query KG),
but does NOT execute queries or invent data.
"""

from typing import Dict, List
from app.orchestration.state_schema import QueryState
from app.ports.llm_port import LLMPort


def kg_query_planner_node(state: QueryState, llm: LLMPort) -> QueryState:
    """
    Node 4: Generate structured KG query plan

    Args:
        state: Current QueryState with intent, resolved entities, resolved attributes
        llm: LLM adapter instance (injected dependency)

    Returns:
        Updated state with kg_query_plan

    State Updates:
        - kg_query_plan: List of structured query dicts
        - execution_path: Appends "kg_query_planner"
    """
    print(f"\n{'='*80}")
    print(f"NODE 4: KG QUERY PLANNER")
    print(f"{'='*80}")

    # Track execution
    state['execution_path'].append('kg_query_planner')

    # Build context for LLM planning
    planning_context = {
        'query': state['query'],
        'intent': state.get('intent', 'objective'),  # Default to 'objective' if missing
        'subcategory': state.get('subcategory', ''),
        'attributes': [attr.get('Target Attribute') for attr in state.get('resolved_attributes', [])],
        'projects': state.get('resolved_projects', []),
        'developers': state.get('resolved_developers', []),
        'locations': state.get('resolved_locations', [])
    }

    print(f"Planning context:")
    print(f"  Intent: {planning_context['intent']}")
    print(f"  Attributes: {planning_context['attributes']}")
    print(f"  Projects: {planning_context['projects']}")
    print(f"  Locations: {planning_context['locations']}")

    # Generate query plan using LLM
    print(f"\n[Generating Query Plan]...")

    try:
        # LLM returns {query_plan: [...], interaction_id: "..."}
        llm_result = llm.plan_kg_queries(context=planning_context)

        # Extract query_plan and interaction_id
        query_plan = llm_result.get("query_plan", [])
        interaction_id = llm_result.get("interaction_id")

        # Store interaction_id for multi-turn context
        if interaction_id:
            state['interaction_id'] = interaction_id

        # Ensure query_plan is a list
        if isinstance(query_plan, dict):
            query_plan = [query_plan]

        # Auto-fix incomplete plans: inject fetch before sort/aggregate if needed
        if len(query_plan) > 0:
            first_action = query_plan[0].get('action')
            if first_action in ['sort', 'aggregate'] and len(query_plan) == 1:
                # Need to fetch data first
                attributes = query_plan[0].get('attributes', []) or query_plan[0].get('attribute', [])
                if isinstance(attributes, str):
                    attributes = [attributes]

                # Create fetch action
                fetch_action = {
                    'action': 'fetch',
                    'attributes': attributes,
                    'projects': query_plan[0].get('projects', []),
                    'filters': {}
                }

                # Insert fetch action at the beginning
                query_plan.insert(0, fetch_action)
                print(f"  ⚡ Auto-injected fetch action before {first_action} (LLM generated incomplete plan)")

        # ⚠️ DEFENSIVE PROGRAMMING: Validate LLM used resolved attributes
        # If LLM generated a plan that ignores resolved attributes, force-inject them
        resolved_attributes = planning_context.get('attributes', [])
        resolved_projects = planning_context.get('projects', [])

        if resolved_attributes:
            # Check if ANY step in the plan uses the resolved attributes
            plan_uses_resolved_attrs = False
            for step in query_plan:
                step_attributes = step.get('attributes', [])
                if isinstance(step_attributes, str):
                    step_attributes = [step_attributes]
                # Check if at least one resolved attribute is used
                if any(attr in resolved_attributes for attr in step_attributes):
                    plan_uses_resolved_attrs = True
                    break

            # If plan doesn't use resolved attributes, force-correct it
            if not plan_uses_resolved_attrs:
                print(f"  ⚠️ LLM ignored resolved attributes - auto-correcting query plan...")
                print(f"    Resolved attributes: {resolved_attributes}")
                print(f"    LLM generated attributes: {[step.get('attributes') for step in query_plan]}")

                # Find fetch actions and replace their attributes
                corrected = False
                for step in query_plan:
                    if step.get('action') == 'fetch':
                        step['attributes'] = resolved_attributes
                        if resolved_projects:
                            step['projects'] = resolved_projects
                        corrected = True
                        print(f"    → Replaced with: {resolved_attributes}")

                # If no fetch action exists, create one
                if not corrected:
                    print(f"    → Creating fetch action with resolved attributes")
                    fetch_action = {
                        'action': 'fetch',
                        'attributes': resolved_attributes,
                        'projects': resolved_projects if resolved_projects else [],
                        'filters': {}
                    }
                    query_plan.insert(0, fetch_action)

        state['kg_query_plan'] = query_plan

        # Display generated plan
        print(f"\n✓ Generated {len(query_plan)} query step(s):")
        for i, step in enumerate(query_plan, 1):
            print(f"\n  Step {i}:")
            print(f"    Action: {step.get('action')}")
            print(f"    Projects: {step.get('projects', 'N/A')}")
            print(f"    Attributes: {step.get('attributes')}")
            print(f"    Filters: {step.get('filters', {})}")
            if step.get('aggregation'):
                print(f"    Aggregation: {step.get('aggregation')}")

    except Exception as e:
        print(f"\n✗ Error generating query plan: {e}")
        state['error'] = f"Query planning failed: {str(e)}"
        state['next_action'] = 'error'
        return state

    print(f"\n{'='*80}\n")

    return state


def get_query_plan_actions(state: QueryState) -> List[str]:
    """
    Helper: Extract actions from query plan

    Args:
        state: Current QueryState with kg_query_plan

    Returns:
        List of action types (e.g., ["fetch", "aggregate"])
    """
    query_plan = state.get('kg_query_plan', [])
    return [step.get('action') for step in query_plan if step.get('action')]


def requires_aggregation(state: QueryState) -> bool:
    """
    Helper: Check if query plan includes aggregation

    Args:
        state: Current QueryState with kg_query_plan

    Returns:
        True if any query step has aggregation
    """
    query_plan = state.get('kg_query_plan', [])
    return any(step.get('aggregation') for step in query_plan)


def is_multi_project_query(state: QueryState) -> bool:
    """
    Helper: Check if query involves multiple projects

    Args:
        state: Current QueryState with kg_query_plan

    Returns:
        True if query plan involves multiple projects
    """
    query_plan = state.get('kg_query_plan', [])

    for step in query_plan:
        projects = step.get('projects', [])
        if projects and len(projects) > 1:
            return True

        # Check if action is aggregate or compare (implies multiple projects)
        action = step.get('action', '')
        if action in ['aggregate', 'compare']:
            return True

    return False
