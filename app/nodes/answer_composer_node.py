"""
Answer Composer Node - LangGraph Node 8 (FINAL)

Composes natural language answer with provenance tracking.

Flow:
1. Takes query, kg_data, computation_results, and resolved_attributes
2. Uses LLM to compose clear, factual answer
3. Adds provenance markers: [DIRECT - KG], [COMPUTED], [ASSUMED]
4. Includes full provenance trail
5. Sets next_action to "answer"

Key Principle: LLM provides natural language generation and explanation,
but NEVER invents data. All numbers come from kg_data or computation_results.
"""

from typing import Dict, Any
from app.orchestration.state_schema import QueryState
from app.ports.llm_port import LLMPort
from datetime import datetime


def answer_composer_node(state: QueryState, llm: LLMPort) -> QueryState:
    """
    Node 8: Compose final natural language answer with provenance

    Args:
        state: Current QueryState with all data
        llm: LLM adapter instance (injected dependency)

    Returns:
        Updated state with answer, provenance, and next_action="answer"

    State Updates:
        - answer: Natural language answer with provenance markers
        - provenance: Full provenance trail
        - next_action: "answer"
        - execution_path: Appends "answer_composer"
    """
    print(f"\n{'='*80}")
    print(f"NODE 8: ANSWER COMPOSER (FINAL)")
    print(f"{'='*80}")

    # Track execution
    state['execution_path'].append('answer_composer')

    # Gather all context for answer composition
    query = state.get('query', '')
    kg_data = state.get('kg_data', {})
    computation_results = state.get('computation_results', {})
    resolved_attributes = state.get('resolved_attributes', [])

    print(f"Composing answer for: '{query}'")
    print(f"  KG data points: {len(kg_data)}")
    print(f"  Computation results: {'Yes' if computation_results else 'No'}")
    print(f"  Attributes resolved: {len(resolved_attributes)}")

    # Check if we have data to answer with
    # EXCEPTION: Financial queries should proceed even with no kg_data (they'll get educational explanation)
    financial_keywords = ['irr', 'npv', 'payback', 'internal rate of return', 'net present value',
                         'return on investment', 'roi', 'profitability index', 'cap rate',
                         'discounted cash flow', 'dcf']
    is_financial_query = any(keyword in query.lower() for keyword in financial_keywords)

    if not kg_data and not computation_results and not is_financial_query:
        print(f"\n⚠ No data available to answer query")
        state['answer'] = "I don't have sufficient data to answer this query. The Knowledge Graph returned no results."
        state['next_action'] = 'answer'
        return state

    # Extract project metadata for rich answer generation
    project_metadata = extract_project_metadata(kg_data, state)
    if project_metadata:
        print(f"  Project metadata extracted: {project_metadata.get('projectName', 'N/A')}")

    # Compose answer using Gemini LLM ONLY
    print(f"\n[Composing Answer with Gemini]...")
    print(f"  ⚡ Using Gemini for expert-level answer composition")

    try:
        # Import and use Gemini adapter
        from app.adapters.gemini_llm_adapter import GeminiLLMAdapter
        gemini_llm = GeminiLLMAdapter()
        result = gemini_llm.compose_answer(
            query=query,
            kg_data=kg_data,
            computation_results=computation_results if computation_results else None,
            attributes_metadata=resolved_attributes,
            project_metadata=project_metadata
        )

        # Extract answer string from result dict
        if isinstance(result, dict):
            answer = result.get('answer', '')
            interaction_id = result.get('interaction_id')
            if interaction_id:
                state['interaction_id'] = interaction_id
        else:
            answer = result  # Fallback if string returned directly

        state['answer'] = answer

        print(f"✓ Answer composed ({len(answer)} characters)")

        # Show preview
        preview = answer[:200] + "..." if len(answer) > 200 else answer
        print(f"\nAnswer Preview:")
        print(f"{preview}\n")

    except Exception as e:
        print(f"✗ Gemini error: {e}")
        state['answer'] = f"Error composing answer with Gemini: {str(e)}"
        state['error'] = str(e)

    # Build provenance trail
    provenance = build_provenance_trail(state)
    state['provenance'] = provenance

    print(f"[Provenance Trail]")
    print(f"  Data sources: {', '.join(provenance.get('data_sources', []))}")
    print(f"  LF pillars: {', '.join(provenance.get('lf_pillars', []))}")
    if provenance.get('calculation_methods'):
        print(f"  Calculation methods: {', '.join(provenance['calculation_methods'])}")
    if provenance.get('assumptions'):
        print(f"  Assumptions: {len(provenance['assumptions'])}")

    # Set next action
    state['next_action'] = 'answer'

    # Calculate total execution time
    if 'node_timings' in state:
        total_time = sum(state['node_timings'].values())
        state['total_execution_time_ms'] = total_time
        print(f"\nTotal execution time: {total_time:.2f}ms")

    print(f"\n{'='*80}")
    print(f"QUERY ORCHESTRATION COMPLETE")
    print(f"{'='*80}\n")

    return state


def extract_project_metadata(kg_data: Dict, state: QueryState) -> Dict[str, Any]:
    """
    Extract project metadata (developer, location, launch date, map URLs) from kg_data

    Args:
        kg_data: Retrieved KG data with keys like "ProjectName.Attribute"
        state: Current QueryState with entity resolution info

    Returns:
        Dict with project metadata fields (projectName, developerName, location, launchDate, latitude, longitude, map_url, satellite_url)
    """
    from app.ports.knowledge_graph_port import KnowledgeGraphPort
    from app.adapters.data_service_kg_adapter import DataServiceKGAdapter

    metadata = {}

    # Extract project name from kg_data keys
    if not kg_data:
        return metadata

    # Get first project name from kg_data keys (format: "ProjectName.Attribute")
    project_name = None
    for key in kg_data.keys():
        if '.' in key:
            project_name = key.split('.')[0]
            break

    if not project_name:
        # Try to get from resolved entities
        entities = state.get('resolved_entities', [])
        for entity in entities:
            if entity.get('entity_type') == 'project':
                project_name = entity.get('canonical_name')
                break

    if not project_name:
        return metadata

    # Fetch metadata fields from KG using DataServiceKGAdapter
    try:
        kg_adapter = DataServiceKGAdapter()

        # Fetch metadata fields
        metadata['projectName'] = project_name
        metadata['developerName'] = kg_adapter.fetch_attribute(project_name, 'developerName') or 'Unknown Developer'
        metadata['location'] = kg_adapter.fetch_attribute(project_name, 'location') or 'Unknown Location'
        metadata['launchDate'] = kg_adapter.fetch_attribute(project_name, 'launchDate') or 'N/A'

        # Clean up developer name (remove newlines)
        if metadata['developerName']:
            metadata['developerName'] = metadata['developerName'].replace('\n', ' ')

        # Fetch geographic coordinates (L0 attributes added by geocoding enrichment)
        latitude = kg_adapter.fetch_attribute(project_name, 'latitude')
        longitude = kg_adapter.fetch_attribute(project_name, 'longitude')

        if latitude and longitude:
            metadata['latitude'] = latitude
            metadata['longitude'] = longitude

            # Generate map URLs using ContextService
            try:
                from app.services.context_service import ContextService
                context_service = ContextService()

                # Generate Google Maps URLs
                location_str = f"{project_name}, {metadata['location']}"

                # Get map URLs
                map_data = context_service._get_map_url(location_str, zoom=15)

                if map_data:
                    metadata['map_url'] = map_data.get('static_map_url')
                    metadata['embed_url'] = map_data.get('embed_url')

                    # Generate directions URL manually
                    encoded_location = location_str.replace(' ', '+')
                    metadata['directions_url'] = f"https://www.google.com/maps/dir/?api=1&destination={encoded_location}"

                    print(f"  ✓ Generated map URLs for {project_name} ({latitude:.6f}, {longitude:.6f})")

            except Exception as e:
                print(f"  ⚠️ Could not generate map URLs: {e}")

    except Exception as e:
        print(f"⚠ Could not fetch project metadata: {e}")

    return metadata


def build_provenance_trail(state: QueryState) -> Dict[str, Any]:
    """
    Build comprehensive provenance trail for the answer

    Args:
        state: Current QueryState with all data

    Returns:
        Provenance dict with data sources, layers, methods, timestamp
    """
    provenance = {
        'data_sources': [],
        'lf_pillars': [],
        'lf_data_version': 'Q3_FY25',  # TODO: Get from config/state
        'calculation_methods': [],
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'layer0_inputs': [],
        'layer1_intermediates': [],
        'layer2_dependencies': [],
        'assumptions': []
    }

    # Identify data sources
    if state.get('kg_data'):
        provenance['data_sources'].append('Liases Foras')

    if state.get('resolved_attributes'):
        provenance['data_sources'].append('Vector DB (Schema)')

    # Extract layers from resolved attributes
    layer0_attrs = []
    layer1_attrs = []
    layer2_attrs = []

    for attr in state.get('resolved_attributes', []):
        attr_name = attr.get('Target Attribute', '')
        layer = attr.get('Layer', '')

        if layer == 'L0':
            layer0_attrs.append(attr_name)
        elif layer == 'L1':
            layer1_attrs.append(attr_name)
        elif layer == 'L2' or layer == 'L3':
            layer2_attrs.append(attr_name)

    provenance['layer0_inputs'] = layer0_attrs
    provenance['layer1_intermediates'] = layer1_attrs
    provenance['layer2_dependencies'] = layer2_attrs

    # Extract LF pillars from attributes
    # (In real implementation, would map attributes to pillars)
    if layer1_attrs:
        provenance['lf_pillars'].append('1.1')  # Market Intelligence
    if layer2_attrs:
        provenance['lf_pillars'].append('4.3')  # Financial Analysis

    # Extract calculation methods from computation results
    computation = state.get('computation_results', {})
    if computation:
        calc_method = computation.get('calculation_method', '')
        if calc_method:
            provenance['calculation_methods'].append(calc_method)

        # Extract assumptions
        assumptions = computation.get('assumptions', [])
        provenance['assumptions'].extend(assumptions)

    # Infer LLM usage
    if state.get('answer'):
        provenance['data_sources'].append('LLM (Composition)')

    return provenance


def format_provenance_footer(provenance: Dict[str, Any]) -> str:
    """
    Format provenance trail as markdown footer

    Args:
        provenance: Provenance dict

    Returns:
        Markdown-formatted provenance footer
    """
    lines = [
        "\n---",
        "## Provenance",
        ""
    ]

    # Data sources
    if provenance.get('data_sources'):
        lines.append(f"**Data Sources:** {', '.join(provenance['data_sources'])}")

    # LF pillars
    if provenance.get('lf_pillars'):
        lines.append(f"**LF Pillars:** {', '.join(provenance['lf_pillars'])}")
        lines.append(f"**LF Data Version:** {provenance.get('lf_data_version')}")

    # Layer inputs
    if provenance.get('layer0_inputs'):
        lines.append(f"**Layer 0 Inputs:** {', '.join(provenance['layer0_inputs'])}")

    if provenance.get('layer1_intermediates'):
        lines.append(f"**Layer 1 Metrics:** {', '.join(provenance['layer1_intermediates'])}")

    if provenance.get('layer2_dependencies'):
        lines.append(f"**Layer 2 Calculations:** {', '.join(provenance['layer2_dependencies'])}")

    # Calculation methods
    if provenance.get('calculation_methods'):
        lines.append(f"**Calculation Methods:** {', '.join(provenance['calculation_methods'])}")

    # Assumptions
    if provenance.get('assumptions'):
        lines.append(f"**Assumptions:**")
        for assumption in provenance['assumptions']:
            lines.append(f"  - {assumption}")

    # Timestamp
    lines.append(f"\n**Generated:** {provenance.get('timestamp')}")

    return "\n".join(lines)


def should_include_explanation(state: QueryState) -> bool:
    """
    Helper: Determine if answer should include calculation explanation

    Args:
        state: Current QueryState

    Returns:
        True if explanation should be included (for financial queries)
    """
    return state.get('intent') == 'financial' and bool(state.get('computation_results'))


def add_calculation_explanation(state: QueryState, llm: LLMPort) -> QueryState:
    """
    Helper: Add detailed calculation explanation for financial queries

    Args:
        state: Current QueryState with computation_results
        llm: LLM adapter instance

    Returns:
        Updated state with explanation appended to answer
    """
    computation = state.get('computation_results', {})

    if not computation:
        return state

    # Identify calculation type
    calc_type = None
    result_value = None

    if 'irr' in computation:
        calc_type = 'IRR'
        result_value = computation['irr']
    elif 'npv' in computation:
        calc_type = 'NPV'
        result_value = computation['npv']
    elif 'payback_period_months' in computation:
        calc_type = 'Payback Period'
        result_value = computation['payback_period_months']

    if not calc_type:
        return state

    # Generate explanation
    try:
        explanation = llm.explain_calculation(
            calculation_type=calc_type,
            inputs=computation,
            result=result_value
        )

        # Append to answer
        current_answer = state.get('answer', '')
        state['answer'] = current_answer + f"\n\n---\n## Calculation Details\n\n{explanation}"

    except Exception as e:
        print(f"⚠ Could not generate calculation explanation: {e}")

    return state
