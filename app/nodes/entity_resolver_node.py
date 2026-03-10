"""
Entity Resolver Node - LangGraph Node 3

Resolves fuzzy entity names to canonical names using Knowledge Graph.

Flow:
1. Takes raw entities (projects, developers, locations)
2. Uses KG to resolve fuzzy names to canonical names
3. Handles typos, case differences, and GraphRAG-powered matching
4. Updates state with resolved entities
5. Routes to kg_query_planner_node

Key Principle: KG provides entity resolution with fuzzy matching.
This is NOT data retrieval, just name normalization.
"""

from typing import Dict, List, Optional
from app.orchestration.state_schema import QueryState
from app.ports.knowledge_graph_port import KnowledgeGraphPort


def entity_resolver_node(state: QueryState, kg: KnowledgeGraphPort) -> QueryState:
    """
    Node 3: Resolve entity names to canonical forms

    Args:
        state: Current QueryState with raw_entities
        kg: Knowledge Graph adapter instance (injected dependency)

    Returns:
        Updated state with resolved_projects, resolved_developers, resolved_locations

    State Updates:
        - resolved_projects: List of canonical project names
        - resolved_developers: List of canonical developer names
        - resolved_locations: List of canonical location names
        - entity_resolution_details: Dict with resolution metadata
        - execution_path: Appends "entity_resolver"
    """
    print(f"\n{'='*80}")
    print(f"NODE 3: ENTITY RESOLVER")
    print(f"{'='*80}")

    # Track execution
    state['execution_path'].append('entity_resolver')

    raw_entities = state.get('raw_entities', {})

    # Initialize resolution results
    resolved_projects = []
    resolved_developers = []
    resolved_locations = []
    resolution_details = {
        'projects': {},
        'developers': {},
        'locations': {},
        'fuzzy_matches': []
    }

    # Resolve Projects
    print(f"\n[1/3] Resolving Projects...")
    raw_projects = raw_entities.get('projects', [])

    if raw_projects:
        for raw_project in raw_projects:
            print(f"  Resolving: '{raw_project}'")

            try:
                canonical_name = kg.resolve_project(raw_project)

                if canonical_name:
                    resolved_projects.append(canonical_name)
                    resolution_details['projects'][raw_project] = canonical_name
                    print(f"    ✓ Matched: '{canonical_name}'")

                    # Track fuzzy match if names differ
                    if raw_project.lower() != canonical_name.lower():
                        resolution_details['fuzzy_matches'].append({
                            'type': 'project',
                            'input': raw_project,
                            'match': canonical_name
                        })
                else:
                    print(f"    ✗ No match found")

            except Exception as e:
                print(f"    ✗ Error: {e}")
    else:
        print(f"  No projects to resolve")

    # Resolve Developers
    print(f"\n[2/3] Resolving Developers...")
    raw_developers = raw_entities.get('developers', [])

    if raw_developers:
        for raw_dev in raw_developers:
            print(f"  Resolving: '{raw_dev}'")

            try:
                canonical_name = kg.resolve_developer(raw_dev)

                if canonical_name:
                    resolved_developers.append(canonical_name)
                    resolution_details['developers'][raw_dev] = canonical_name
                    print(f"    ✓ Matched: '{canonical_name}'")

                    if raw_dev.lower() != canonical_name.lower():
                        resolution_details['fuzzy_matches'].append({
                            'type': 'developer',
                            'input': raw_dev,
                            'match': canonical_name
                        })
                else:
                    print(f"    ✗ No match found")

            except Exception as e:
                print(f"    ✗ Error: {e}")
    else:
        print(f"  No developers to resolve")

    # Resolve Locations
    print(f"\n[3/3] Resolving Locations...")
    raw_locations = raw_entities.get('locations', [])

    if raw_locations:
        for raw_loc in raw_locations:
            print(f"  Resolving: '{raw_loc}'")

            try:
                canonical_name = kg.resolve_location(raw_loc)

                if canonical_name:
                    resolved_locations.append(canonical_name)
                    resolution_details['locations'][raw_loc] = canonical_name
                    print(f"    ✓ Matched as location: '{canonical_name}'")

                    if raw_loc.lower() != canonical_name.lower():
                        resolution_details['fuzzy_matches'].append({
                            'type': 'location',
                            'input': raw_loc,
                            'match': canonical_name
                        })
                else:
                    # Fallback: Try resolving as a project (LLM may have misclassified)
                    print(f"    ⚠ Not a location, trying as project...")
                    project_name = kg.resolve_project(raw_loc)

                    if project_name:
                        resolved_projects.append(project_name)
                        resolution_details['projects'][raw_loc] = project_name
                        print(f"    ✓ Matched as project: '{project_name}'")

                        resolution_details['fuzzy_matches'].append({
                            'type': 'location_to_project',
                            'input': raw_loc,
                            'match': project_name,
                            'note': 'LLM classified as location but resolved as project'
                        })
                    else:
                        print(f"    ✗ No match found as location or project")

            except Exception as e:
                print(f"    ✗ Error: {e}")
    else:
        print(f"  No locations to resolve")

    # Special case: If no projects but location specified, find all projects in that location
    if not resolved_projects and resolved_locations:
        print(f"\n[Special Case] Finding all projects in location: {resolved_locations[0]}")
        try:
            projects_in_location = kg.find_projects_by_filter({'location': resolved_locations[0]})
            if projects_in_location:
                resolved_projects.extend(projects_in_location)
                print(f"  ✓ Found {len(projects_in_location)} projects in {resolved_locations[0]}")
        except Exception as e:
            print(f"  ✗ Error finding projects: {e}")

    # Update state
    state['resolved_projects'] = resolved_projects
    state['resolved_developers'] = resolved_developers
    state['resolved_locations'] = resolved_locations
    state['entity_resolution_details'] = resolution_details

    # Summary
    print(f"\n{'─'*80}")
    print(f"Resolution Summary:")
    print(f"  Projects: {len(resolved_projects)} resolved")
    print(f"  Developers: {len(resolved_developers)} resolved")
    print(f"  Locations: {len(resolved_locations)} resolved")
    if resolution_details['fuzzy_matches']:
        print(f"  Fuzzy matches: {len(resolution_details['fuzzy_matches'])}")
    print(f"{'='*80}\n")

    return state


def has_entities(state: QueryState) -> bool:
    """
    Helper: Check if any entities were resolved

    Args:
        state: Current QueryState with resolved entities

    Returns:
        True if at least one entity was resolved
    """
    return bool(
        state.get('resolved_projects') or
        state.get('resolved_developers') or
        state.get('resolved_locations')
    )


def get_filter_dict(state: QueryState) -> Dict[str, str]:
    """
    Helper: Build filter dictionary for KG queries

    Args:
        state: Current QueryState with resolved entities

    Returns:
        Dict suitable for KG filter parameter
    """
    filters = {}

    if state.get('resolved_locations'):
        filters['location'] = state['resolved_locations'][0]

    if state.get('resolved_developers'):
        filters['developer'] = state['resolved_developers'][0]

    return filters
