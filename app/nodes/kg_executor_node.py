"""
KG Executor Node - LangGraph Node 5

Executes query plan against Knowledge Graph to retrieve data.

Flow:
1. Takes kg_query_plan from planner
2. Executes each query step against KG
3. Collects all data into kg_data dict
4. Updates state with execution results
5. Routes to parameter_gatherer_node (if financial) or answer_composer_node

Key Principle: KG is the SINGLE SOURCE OF TRUTH for all numeric data.
This node NEVER invents data - only retrieves from KG.
"""

from typing import Dict, List, Any
from app.orchestration.state_schema import QueryState
from app.ports.knowledge_graph_port import KnowledgeGraphPort
import time


def kg_executor_node(state: QueryState, kg: KnowledgeGraphPort) -> QueryState:
    """
    Node 5: Execute query plan against Knowledge Graph

    Args:
        state: Current QueryState with kg_query_plan
        kg: Knowledge Graph adapter instance (injected dependency)

    Returns:
        Updated state with kg_data and execution metadata

    State Updates:
        - kg_data: Dict with all retrieved data
        - kg_execution_details: Metadata about execution
        - execution_path: Appends "kg_executor"
    """
    print(f"\n{'='*80}")
    print(f"NODE 5: KG EXECUTOR")
    print(f"{'='*80}")

    # Track execution
    state['execution_path'].append('kg_executor')
    start_time = time.time()

    query_plan = state.get('kg_query_plan', [])

    if not query_plan:
        print(f"⚠ No query plan found - skipping KG execution")
        state['kg_data'] = {}
        return state

    print(f"Executing {len(query_plan)} query step(s)...\n")

    # Initialize results
    kg_data = {}
    query_count = 0

    # Execute each step in the plan (LLM decides which actions to use)
    for i, step in enumerate(query_plan, 1):
        action = step.get('action')
        projects = step.get('projects', [])
        attributes = step.get('attributes', [])
        filters = step.get('filters', {})
        aggregation = step.get('aggregation')

        # Filter-specific parameters (LLM decided these)
        operation = step.get('operation')
        target_value = step.get('target_value')
        min_value = step.get('min_value')
        max_value = step.get('max_value')
        tolerance_pct = step.get('tolerance_pct', 10.0)

        # Sort/Group parameters (LLM decided these)
        order = step.get('order', 'desc')
        limit = step.get('limit')
        group_by = step.get('group_by')

        # Calculate parameters (LLM decided these)
        formula = step.get('formula')

        print(f"[Step {i}/{len(query_plan)}] Action: {action}")

        try:
            if action == 'fetch':
                # Fetch specific attributes for projects
                # If no projects specified, fetch from ALL projects
                if not projects:
                    print(f"  Fetching from ALL projects (no specific projects provided)")
                    all_project_names = kg.get_all_projects()
                    projects = all_project_names
                    print(f"  Found {len(projects)} projects in KG")

                for project in projects:
                    print(f"  Fetching from project: {project}")

                    # Check if this is a location or overview query (keywords in attributes)
                    location_overview_keywords = ['location', 'latitude', 'longitude', 'overview', 'details', 'info', 'about', 'coordinates', 'gps']
                    is_overview_query = any(
                        keyword in str(attr).lower()
                        for attr in attributes
                        for keyword in location_overview_keywords
                    ) if attributes else False

                    # If it's an overview/location query, fetch FULL project metadata
                    if is_overview_query:
                        print(f"  → Overview/Location query detected - fetching full metadata")
                        full_metadata = kg.get_project_metadata(project)
                        if full_metadata:
                            # Store full metadata in kg_data (not nested under project name)
                            kg_data.update(full_metadata)
                            print(f"    ✓ Fetched full metadata: {len(full_metadata)} fields")

                    for attribute in attributes:
                        query_count += 1
                        value = kg.fetch_attribute(project=project, attribute=attribute)

                        key = f"{project}.{attribute}"
                        kg_data[key] = value

                        print(f"    ✓ {attribute}: {value}")

            elif action == 'filter':
                # Filter projects by criteria (LLM-decided operation)
                print(f"  Filtering: {operation} operation")
                print(f"    Attribute: {attributes[0] if attributes else 'N/A'}")

                if operation == 'range':
                    # Range query: projects within ±tolerance% of target
                    print(f"    Target: {target_value} ±{tolerance_pct}%")
                    if filters.get('location'):
                        print(f"    Location filter: {filters['location']}")

                    query_count += 1
                    results = kg.filter_projects_by_range(
                        attribute=attributes[0] if attributes else '',
                        target_value=target_value,
                        tolerance_pct=tolerance_pct,
                        location=filters.get('location')
                    )

                    key = f"filter_{operation}_{attributes[0] if attributes else 'projects'}"
                    kg_data[key] = results

                    print(f"    ✓ Found {len(results)} projects:")
                    for result in results[:5]:  # Show first 5
                        print(f"      - {result.get('project')}: {result.get('value')} {result.get('unit')}")
                    if len(results) > 5:
                        print(f"      ... and {len(results) - 5} more")

                elif operation == 'greater_than':
                    # Filter projects where attribute > value
                    print(f"    Condition: > {target_value}")
                    query_count += 1
                    results = kg.filter_projects_by_comparison(
                        attribute=attributes[0] if attributes else '',
                        operator='>',
                        value=target_value,
                        location=filters.get('location')
                    )

                    key = f"filter_{operation}_{attributes[0] if attributes else 'projects'}"
                    kg_data[key] = results

                    print(f"    ✓ Found {len(results)} projects:")
                    for result in results[:5]:  # Show first 5
                        print(f"      - {result.get('project')}: {result.get('value')} {result.get('unit')}")
                    if len(results) > 5:
                        print(f"      ... and {len(results) - 5} more")

                elif operation == 'less_than':
                    # Filter projects where attribute < value
                    print(f"    Condition: < {target_value}")
                    query_count += 1
                    results = kg.filter_projects_by_comparison(
                        attribute=attributes[0] if attributes else '',
                        operator='<',
                        value=target_value,
                        location=filters.get('location')
                    )

                    key = f"filter_{operation}_{attributes[0] if attributes else 'projects'}"
                    kg_data[key] = results

                    print(f"    ✓ Found {len(results)} projects:")
                    for result in results[:5]:  # Show first 5
                        print(f"      - {result.get('project')}: {result.get('value')} {result.get('unit')}")
                    if len(results) > 5:
                        print(f"      ... and {len(results) - 5} more")

                elif operation == 'between':
                    # Filter projects where min <= attribute <= max
                    print(f"    Range: {min_value} to {max_value}")
                    query_count += 1
                    results = kg.filter_projects_by_between(
                        attribute=attributes[0] if attributes else '',
                        min_value=min_value,
                        max_value=max_value,
                        location=filters.get('location')
                    )

                    key = f"filter_{operation}_{attributes[0] if attributes else 'projects'}"
                    kg_data[key] = results

                    print(f"    ✓ Found {len(results)} projects:")
                    for result in results[:5]:  # Show first 5
                        print(f"      - {result.get('project')}: {result.get('value')} {result.get('unit')}")
                    if len(results) > 5:
                        print(f"      ... and {len(results) - 5} more")

                elif operation == 'equals':
                    # Filter projects where attribute == value
                    print(f"    Condition: = {target_value}")
                    query_count += 1
                    results = kg.filter_projects_by_comparison(
                        attribute=attributes[0] if attributes else '',
                        operator='=',
                        value=target_value,
                        location=filters.get('location')
                    )

                    key = f"filter_{operation}_{attributes[0] if attributes else 'projects'}"
                    kg_data[key] = results

                    print(f"    ✓ Found {len(results)} projects:")
                    for result in results[:5]:  # Show first 5
                        print(f"      - {result.get('project')}: {result.get('value')} {result.get('unit')}")
                    if len(results) > 5:
                        print(f"      ... and {len(results) - 5} more")

            elif action == 'aggregate':
                # Aggregate attribute across multiple projects
                for attribute in attributes:
                    query_count += 1
                    print(f"  Aggregating: {attribute} ({aggregation})")
                    if filters:
                        print(f"    Filters: {filters}")

                    result = kg.aggregate(
                        attribute=attribute,
                        aggregation=aggregation,
                        filters=filters
                    )

                    key = f"{aggregation}_{attribute}"
                    kg_data[key] = result

                    print(f"    ✓ Result: {result}")

            elif action == 'compare':
                # Compare attribute across multiple projects
                for attribute in attributes:
                    query_count += 1
                    print(f"  Comparing: {attribute} across {len(projects)} projects")

                    comparison_results = kg.compare(
                        projects=projects,
                        attribute=attribute
                    )

                    key = f"compare_{attribute}"
                    kg_data[key] = comparison_results

                    print(f"    ✓ Retrieved {len(comparison_results)} values:")
                    for result in comparison_results:
                        print(f"      - {result.get('project')}: {result.get('value')}")

            elif action == 'sort':
                # Sort results from previous fetch/filter actions
                sort_attr = attributes[0] if attributes else step.get('attribute')
                print(f"  Sorting by: {sort_attr} ({order})")
                if limit:
                    print(f"    Limit: Top {limit}")

                # Extract data points that match the sort attribute
                sortable_data = []
                for key, value in kg_data.items():
                    # Keys are in format "ProjectName.AttributeName"
                    if '.' in key and sort_attr in key:
                        project_name = key.split('.')[0]
                        # Extract numeric value (handle dict format {value: X, unit: Y})
                        if isinstance(value, dict):
                            numeric_val = value.get('value')
                        else:
                            numeric_val = value

                        # Only add if we have a valid numeric value
                        if numeric_val is not None:
                            try:
                                sortable_data.append({
                                    'project': project_name,
                                    'value': float(numeric_val) if not isinstance(numeric_val, (int, float)) else numeric_val,
                                    'key': key
                                })
                            except (ValueError, TypeError):
                                pass  # Skip non-numeric values

                # Sort the data
                if sortable_data:
                    reverse = (order == 'desc')
                    sortable_data.sort(key=lambda x: x['value'], reverse=reverse)

                    # Apply limit if specified
                    if limit:
                        sortable_data = sortable_data[:limit]

                    # Store sorted results
                    sorted_key = f"sorted_{sort_attr}"
                    kg_data[sorted_key] = sortable_data

                    print(f"    ✓ Sorted {len(sortable_data)} projects:")
                    for item in sortable_data:
                        print(f"      - {item['project']}: {item['value']}")
                else:
                    print(f"    ⚠ No sortable data found for attribute: {sort_attr}")

            elif action == 'group':
                # Group projects and calculate per-group metrics
                print(f"  Grouping by: {group_by}")
                print(f"    Aggregation: {aggregation}")
                print(f"    Attributes: {attributes}")

                # TODO: Implement grouping in KG adapter
                print(f"    ⚠ group action not yet implemented")

            elif action == 'calculate':
                # Perform calculations (math/formulaic)
                print(f"  Calculation: {operation}")
                print(f"    Attributes: {attributes}")
                if formula:
                    print(f"    Formula: {formula}")

                # TODO: Implement calculation logic
                print(f"    ⚠ calculate action not yet implemented")

            elif action == 'proximity':
                # Find projects within radius of reference project
                reference_project = step.get('reference_project')
                radius_km = step.get('radius_km')

                print(f"  Proximity search:")
                print(f"    Reference project: {reference_project}")
                print(f"    Radius: {radius_km} KM")

                if not reference_project:
                    print(f"    ✗ Error: reference_project required for proximity search")
                elif not radius_km:
                    print(f"    ✗ Error: radius_km required for proximity search")
                else:
                    try:
                        query_count += 1
                        results = kg.find_projects_near(
                            reference_project_name=reference_project,
                            radius_km=radius_km
                        )

                        key = f"proximity_{reference_project}_{radius_km}km"
                        kg_data[key] = results

                        print(f"    ✓ Found {len(results)} projects within {radius_km} KM:")
                        for result in results[:5]:  # Show first 5
                            project_name = kg.get_value(result.get('projectName'))
                            distance = result.get('distance_km')
                            print(f"      - {project_name}: {distance:.3f} km")
                        if len(results) > 5:
                            print(f"      ... and {len(results) - 5} more")

                    except ValueError as e:
                        print(f"    ✗ Error: {e}")
                    except Exception as e:
                        print(f"    ✗ Unexpected error: {e}")
                        import traceback
                        traceback.print_exc()

            else:
                print(f"  ⚠ Unknown action: {action}")

        except Exception as e:
            print(f"  ✗ Error executing step: {e}")
            import traceback
            traceback.print_exc()
            # Continue with next step rather than failing completely

        print()  # Blank line between steps

    # Calculate execution time
    execution_time_ms = (time.time() - start_time) * 1000

    # Update state
    state['kg_data'] = kg_data
    state['kg_execution_details'] = {
        'query_count': query_count,
        'execution_time_ms': execution_time_ms,
        'steps_executed': len(query_plan)
    }

    # Summary
    print(f"{'─'*80}")
    print(f"KG Execution Summary:")
    print(f"  Data points retrieved: {len(kg_data)}")
    print(f"  Queries executed: {query_count}")
    print(f"  Execution time: {execution_time_ms:.2f}ms")
    print(f"{'='*80}\n")

    return state


def has_kg_data(state: QueryState) -> bool:
    """
    Helper: Check if KG data was retrieved

    Args:
        state: Current QueryState with kg_data

    Returns:
        True if kg_data is not empty
    """
    kg_data = state.get('kg_data', {})
    return bool(kg_data)


def get_kg_data_keys(state: QueryState) -> List[str]:
    """
    Helper: Get all keys from kg_data

    Args:
        state: Current QueryState with kg_data

    Returns:
        List of data keys
    """
    kg_data = state.get('kg_data', {})
    return list(kg_data.keys())


def fetch_cash_flow_data_if_needed(state: QueryState, kg: KnowledgeGraphPort) -> QueryState:
    """
    Helper: For financial queries, fetch additional cash flow data

    Args:
        state: Current QueryState
        kg: Knowledge Graph adapter

    Returns:
        Updated state with cash flow data added to kg_data
    """
    if state.get('intent') != 'financial':
        return state

    projects = state.get('resolved_projects', [])

    if not projects:
        return state

    print(f"[Cash Flow Data] Fetching for financial calculation...")

    for project in projects:
        try:
            cash_flow_data = kg.fetch_cash_flow_data(project)

            if cash_flow_data:
                # Add to kg_data with special prefix
                for key, value in cash_flow_data.items():
                    state['kg_data'][f"{project}.cf.{key}"] = value

                print(f"  ✓ {project}: {len(cash_flow_data)} cash flow fields")

        except Exception as e:
            print(f"  ✗ Error fetching cash flow for {project}: {e}")

    return state
