"""
Parameter Gatherer Node - LangGraph Node 6

Checks for missing parameters in financial calculations.

Flow:
1. Only runs for financial intent queries
2. Checks if all required parameters are present in kg_data
3. If missing, generates clarification question via LLM
4. Updates state with missing_parameters and clarification_question
5. Routes to computation_node (if complete) or back to user (if incomplete)

Key Principle: Enables multi-turn conversations for financial calculations.
State persists across turns via session_id.
"""

from typing import Dict, List, Optional
from app.orchestration.state_schema import QueryState
from app.ports.llm_port import LLMPort


def parameter_gatherer_node(state: QueryState, llm: LLMPort) -> QueryState:
    """
    Node 6: Check for missing parameters in financial calculations

    Args:
        state: Current QueryState with intent and kg_data
        llm: LLM adapter instance (injected dependency)

    Returns:
        Updated state with missing_parameters, has_all_parameters, clarification_question

    State Updates:
        - missing_parameters: List of parameter names needed
        - has_all_parameters: True/False
        - clarification_question: Generated question for user (if params missing)
        - next_action: "gather_parameters" or "continue"
        - execution_path: Appends "parameter_gatherer"
    """
    print(f"\n{'='*80}")
    print(f"NODE 6: PARAMETER GATHERER")
    print(f"{'='*80}")

    # Track execution
    state['execution_path'].append('parameter_gatherer')

    # Only run for financial queries
    if state.get('intent') != 'financial':
        print(f"Intent is '{state.get('intent')}' - skipping parameter check")
        state['has_all_parameters'] = True
        state['missing_parameters'] = []
        print(f"{'='*80}\n")
        return state

    print(f"Financial query detected - checking required parameters...\n")

    # Define required parameters by financial subcategory
    required_parameters_map = {
        'IRR_calculation': ['cash_flows', 'initial_investment'],
        'NPV_calculation': ['cash_flows', 'discount_rate', 'initial_investment'],
        'payback_calculation': ['cash_flows', 'initial_investment'],
        'sensitivity_analysis': ['cash_flows', 'discount_rate', 'variance_range'],
        'default': ['cash_flows']  # Minimal requirement
    }

    subcategory = state.get('subcategory', 'default')
    required_params = required_parameters_map.get(subcategory, required_parameters_map['default'])

    print(f"Subcategory: {subcategory}")
    print(f"Required parameters: {required_params}")

    # Check which parameters are present
    kg_data = state.get('kg_data', {})
    conversation_history = state.get('conversation_history', [])

    present_params = []
    missing_params = []

    for param in required_params:
        # Check in kg_data
        param_found = False

        if param == 'cash_flows':
            # Check if we have cash flow-related data
            cf_keys = [k for k in kg_data.keys() if '.cf.' in k or 'annual_sales' in k or 'revenue' in k]
            if cf_keys:
                param_found = True
                present_params.append(param)

        elif param == 'initial_investment':
            # Check for investment/cost data
            inv_keys = [k for k in kg_data.keys() if 'investment' in k.lower() or 'cost' in k.lower()]
            if inv_keys:
                param_found = True
                present_params.append(param)

        elif param == 'discount_rate':
            # Check if discount rate was mentioned in conversation
            for msg in conversation_history:
                if 'discount' in msg.get('content', '').lower() and any(c.isdigit() for c in msg.get('content', '')):
                    param_found = True
                    present_params.append(param)
                    break

            # Also check query itself
            if not param_found and 'discount' in state.get('query', '').lower():
                # Try to extract rate from query
                import re
                query = state.get('query', '')
                rate_match = re.search(r'(\d+(?:\.\d+)?)\s*%', query)
                if rate_match:
                    param_found = True
                    present_params.append(param)
                    # Store extracted rate in kg_data
                    state['kg_data']['discount_rate'] = float(rate_match.group(1)) / 100

        if not param_found:
            missing_params.append(param)

    # Update state
    state['missing_parameters'] = missing_params
    state['has_all_parameters'] = len(missing_params) == 0

    # Display results
    print(f"\nParameter Check:")
    if present_params:
        print(f"  ✓ Present: {present_params}")
    if missing_params:
        print(f"  ✗ Missing: {missing_params}")

    # Generate clarification question if parameters missing
    if missing_params:
        print(f"\n[Generating Clarification Question]...")

        try:
            clarification_context = {
                'query': state['query'],
                'intent': state['intent'],
                'subcategory': subcategory,
                'present_parameters': present_params,
                'kg_data_summary': list(kg_data.keys())[:5]  # Sample of available data
            }

            clarification_question = llm.ask_clarification(
                missing_parameters=missing_params,
                context=clarification_context
            )

            state['clarification_question'] = clarification_question
            state['next_action'] = 'gather_parameters'

            print(f"✓ Clarification question generated:")
            print(f"\n{clarification_question}\n")

        except Exception as e:
            print(f"✗ Error generating clarification: {e}")
            state['clarification_question'] = f"To complete this calculation, I need: {', '.join(missing_params)}"
            state['next_action'] = 'gather_parameters'

    else:
        print(f"\n✓ All required parameters present - proceeding to computation")
        state['next_action'] = 'continue'

    print(f"{'='*80}\n")

    return state


def should_gather_parameters(state: QueryState) -> bool:
    """
    Routing function: Determine if we need to gather more parameters

    Args:
        state: Current QueryState

    Returns:
        True if parameters are missing, False if all present
    """
    return not state.get('has_all_parameters', True)


def extract_parameters_from_user_response(state: QueryState, user_response: str) -> QueryState:
    """
    Helper: Extract parameters from user's response to clarification question

    This would be called when processing the next turn in a multi-turn conversation.

    Args:
        state: Current QueryState
        user_response: User's answer to clarification question

    Returns:
        Updated state with extracted parameters added to kg_data
    """
    import re

    kg_data = state.get('kg_data', {})

    # Extract discount rate (e.g., "12%", "0.12", "12 percent")
    discount_match = re.search(r'(\d+(?:\.\d+)?)\s*%', user_response)
    if not discount_match:
        discount_match = re.search(r'(?:rate|discount|discount rate)[:\s]+(\d+(?:\.\d+)?)', user_response, re.IGNORECASE)

    if discount_match:
        rate_value = float(discount_match.group(1))
        # Normalize to decimal (12% -> 0.12)
        if rate_value > 1:
            rate_value = rate_value / 100
        kg_data['discount_rate'] = rate_value
        print(f"  ✓ Extracted discount_rate: {rate_value}")

    # Extract holding period (e.g., "5 years", "60 months")
    period_match = re.search(r'(\d+)\s*(year|yr|month|mo)', user_response, re.IGNORECASE)
    if period_match:
        period_value = int(period_match.group(1))
        unit = period_match.group(2).lower()

        # Convert to months
        if 'year' in unit or 'yr' in unit:
            period_value = period_value * 12

        kg_data['holding_period_months'] = period_value
        print(f"  ✓ Extracted holding_period: {period_value} months")

    # Extract exit value/sale price (e.g., "Rs. 500 Cr", "500 crores")
    exit_match = re.search(r'(?:exit|sale|sell)[^\d]*(\d+(?:\.\d+)?)\s*(?:cr|crore)', user_response, re.IGNORECASE)
    if exit_match:
        exit_value = float(exit_match.group(1))
        kg_data['exit_value'] = exit_value
        print(f"  ✓ Extracted exit_value: {exit_value} Cr")

    state['kg_data'] = kg_data

    return state
