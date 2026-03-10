# Range Query & Conversation State Implementation Guide

**Status**: Foundation Complete (2/8 components)
**Date**: 2025-12-11
**Feature**: Multi-project range queries with conversation state memory

---

## ✅ Completed Components

### 1. Conversation State Manager (`app/services/conversation_state_manager.py`)

**Status**: ✅ COMPLETE
**Lines**: 350

**Features**:
- Session-based conversation tracking
- Redis backend with in-memory fallback (no Redis installation required)
- Yes/no intent detection for follow-up handling
- Configurable session TTL (24 hours default)
- Follow-up question tracking

**API**:
```python
from app.services.conversation_state_manager import get_conversation_state_manager

state_mgr = get_conversation_state_manager()

# Add conversation turn
state_mgr.add_turn(
    session_id="user_123",
    query="Show projects with units around 600 sq.ft",
    response="[list of projects]",
    intent="COMPARATIVE",
    follow_up_question="Would you like me to show pricing for these projects?",
    follow_up_context={'projects': [...]}
)

# Check for yes/no response
is_yes = state_mgr.is_yes_no_response("yes")  # Returns True
pending = state_mgr.get_pending_follow_up("user_123")  # Get follow-up context

# Get conversation history for LLM context
history = state_mgr.get_conversation_history("user_123", max_turns=5)
```

---

### 2. Range Query Support (`app/adapters/data_service_kg_adapter.py:255`)

**Status**: ✅ COMPLETE
**Method**: `filter_projects_by_range()`

**Signature**:
```python
def filter_projects_by_range(
    self,
    attribute: str,              # e.g., "Unit Saleable Size"
    target_value: float,         # e.g., 600
    tolerance_pct: float = 10.0, # ±10%
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
```

**Returns**:
```python
[
    {
        'project': 'Pradnyesh Shriniwas',
        'attribute': 'Unit Saleable Size',
        'value': 562,
        'unit': 'sq. ft.',
        'distance_from_target': 38,
        'percentage_diff': 6.33
    },
    {
        'project': 'Sara Abhiruchi Tower',
        'attribute': 'Unit Saleable Size',
        'value': 635,
        'unit': 'sq. ft.',
        'distance_from_target': 35,
        'percentage_diff': 5.83
    },
    ...
]
```

---

## 🔄 Remaining Implementation

### Step 3: Add COMPARATIVE Intent to Gemini LLM Adapter

**File**: `app/adapters/gemini_llm_adapter.py`
**Location**: Update `classify_intent()` method's prompt

**Current Intent Types**:
- OBJECTIVE: Fetch single value from single project
- ANALYTICAL: Compare/analyze values
- FINANCIAL: Calculate metrics (NPV, IRR)

**Add**:
- **COMPARATIVE**: List/filter multiple projects by criteria

**Implementation**:
```python
# Find the intent classification prompt (around line 180-220)
# Add to the intent type descriptions:

"""
Intent Type Descriptions:

... existing descriptions ...

4. COMPARATIVE
   - Queries that ask to list, show, find, or filter multiple projects based on criteria
   - Contains words like: "show", "list", "find", "which", "all projects", "around", "between"
   - Examples:
     * "Show projects with units around 600 sq.ft"
     * "List all projects under 100 Crore"
     * "Find projects with absorption rate > 1%"
     * "Which projects have 3BHK units?"

   Key indicators:
   - No specific project mentioned initially (or asks for "all")
   - Requests a list/set of matching projects
   - Contains comparison/range operators (around, under, over, between)
"""
```

**Also add yes/no intent detection**:
```python
def detect_followup_response(self, query: str) -> Optional[str]:
    """
    Detect if query is responding to a follow-up question

    Returns: 'yes', 'no', or None
    """
    prompt = f"""
    Analyze if this is a yes/no response to a previous question:

    Query: "{query}"

    Rules:
    - Yes indicators: yes, yeah, sure, ok, go ahead, proceed, affirmative
    - No indicators: no, nope, skip, cancel, don't
    - If neither, return "unknown"

    Respond with ONLY: "yes", "no", or "unknown"
    """

    response = self.model.generate_content(prompt)
    result = response.text.strip().lower()

    if result == "yes":
        return "yes"
    elif result == "no":
        return "no"
    return None
```

---

### Step 4: Update KG Query Planner for Range Queries

**File**: `app/nodes/kg_query_planner_node.py`
**Location**: After line 80 (inside `kg_query_planner_node()` function)

**Add COMPARATIVE Intent Handler**:
```python
# Around line 85, after the existing intent checks:

elif intent == 'comparative':
    # Range/filter query
    print(f"Planning COMPARATIVE query (range/filter)")

    # Extract target value and attribute from query
    # Use LLM to extract: "around 600 sq.ft" → target=600, attribute="Unit Saleable Size"
    extraction_prompt = f"""
    Extract the target value and attribute from this query:

    Query: {state['query']}
    Resolved Attributes: {resolved_attributes}

    Extract:
    1. Target value (numeric)
    2. Attribute name (use resolved attribute name if available)
    3. Comparison type (range, greater_than, less_than, equals)
    4. Tolerance (if "around" or similar, use 10%)

    Return JSON:
    {{
        "target_value": <number>,
        "attribute": "<name>",
        "comparison": "range|gt|lt|eq",
        "tolerance_pct": <number>
    }}
    """

    extraction = llm.generate_json(extraction_prompt)

    query_plan.append({
        'action': 'filter',  # NEW action type
        'attribute': extraction.get('attribute'),
        'operation': extraction.get('comparison', 'range'),
        'target_value': extraction.get('target_value'),
        'tolerance_pct': extraction.get('tolerance_pct', 10.0),
        'location': resolved_locations[0] if resolved_locations else None,
        'sort_by': 'relevance'
    })

    print(f"✓ Filter plan: {extraction.get('attribute')} {extraction.get('comparison')} {extraction.get('target_value')}")
```

---

### Step 5: Update KG Executor to Handle 'filter' Action

**File**: `app/nodes/kg_executor_node.py`
**Location**: After line 100 (inside action handler)

**Add 'filter' Action Handler**:
```python
# After the existing 'fetch' and 'aggregate' handlers:

elif action == 'filter':
    # Handle range/filter queries
    attribute = step.get('attribute')
    operation = step.get('operation')
    target_value = step.get('target_value')
    tolerance_pct = step.get('tolerance_pct', 10.0)
    location = step.get('location')

    print(f"  Filtering projects by {attribute}")
    print(f"    Operation: {operation}")
    print(f"    Target: {target_value}")
    print(f"    Tolerance: ±{tolerance_pct}%")
    if location:
        print(f"    Location: {location}")

    if operation == 'range':
        results = kg.filter_projects_by_range(
            attribute=attribute,
            target_value=target_value,
            tolerance_pct=tolerance_pct,
            location=location
        )

        kg_data['filter_results'] = results
        kg_data['filter_metadata'] = {
            'attribute': attribute,
            'target_value': target_value,
            'tolerance_pct': tolerance_pct,
            'location': location,
            'result_count': len(results)
        }

        print(f"  ✓ Found {len(results)} matching projects")

        # Show top 5 results in logs
        for i, r in enumerate(results[:5], 1):
            print(f"    {i}. {r['project']}: {r['value']} {r['unit']} (diff: {r['percentage_diff']:.1f}%)")

        if len(results) > 5:
            print(f"    ... and {len(results) - 5} more")
```

---

### Step 6: Update Answer Composer for Multi-Result Formatting

**File**: `app/nodes/answer_composer_node.py`
**Location**: Add new function before `answer_composer_node()` (around line 20)

**Add Multi-Result Formatter**:
```python
def format_comparative_answer(state: QueryState, llm: LLMPort) -> str:
    """
    Format answer for COMPARATIVE queries with multiple results

    Generates:
    1. Numbered list of matching projects
    2. LLM-generated insights about the results
    3. Follow-up question to continue exploration
    """
    filter_results = state.get('kg_data', {}).get('filter_results', [])
    filter_metadata = state.get('kg_data', {}).get('filter_metadata', {})
    query = state.get('query')

    if not filter_results:
        return "No projects found matching your criteria. Try adjusting the target value or tolerance."

    # Build structured result list (top 10)
    result_items = []
    for i, r in enumerate(filter_results[:10], 1):
        result_items.append(
            f"{i}. **{r['project']}**: {r['value']} {r['unit']} "
            f"({r['percentage_diff']:.1f}% from target)"
        )

    result_list = "\n".join(result_items)

    if len(filter_results) > 10:
        result_list += f"\n\n*... and {len(filter_results) - 10} more projects*"

    # Generate insights using LLM
    insight_prompt = f"""
    Analyze these search results and provide 2-3 bullet point insights:

    Query: {query}
    Target: {filter_metadata.get('target_value')} {filter_metadata.get('attribute')}
    Total Results: {len(filter_results)} projects

    Top matches:
    {chr(10).join([f"- {r['project']}: {r['value']} {r['unit']}" for r in filter_results[:10]])}

    Provide insights about:
    - Range/distribution of values
    - Standout projects (closest match, interesting outliers)
    - Patterns you notice

    Format as 2-3 bullet points, concise and actionable.
    """

    try:
        insights = llm.generate_text(insight_prompt)
    except:
        insights = "• Results sorted by closest match to your target value"

    # Generate follow-up question
    followup_prompt = f"""
    User searched for: {query}
    Found: {len(filter_results)} projects
    Attribute: {filter_metadata.get('attribute')}

    Suggest ONE specific follow-up question to help them explore further.

    Examples of good follow-ups:
    - "Would you like me to show pricing details for these projects?"
    - "Should I compare absorption rates across these projects?"
    - "Would you like to see developer information for these projects?"

    Format: "Would you like me to [specific action]?"

    Respond with ONLY the question, nothing else.
    """

    try:
        followup = llm.generate_text(followup_prompt)
        followup = followup.strip().strip('"\'')
    except:
        followup = "Would you like me to show more details about any of these projects?"

    # Compose final answer
    answer = f"""## Search Results

{result_list}

**Total:** {len(filter_results)} projects found matching your criteria

---

## Insights

{insights}

---

## Next Steps

{followup}
"""

    return answer.strip()
```

**Update `answer_composer_node()` function** (around line 60):
```python
def answer_composer_node(state: QueryState, llm: LLMPort) -> QueryState:
    """Node 8: Compose final answer"""

    print(f"\n{'='*80}")
    print(f"NODE 8: ANSWER COMPOSER")
    print(f"{'='*80}")

    state['execution_path'].append('answer_composer')

    intent = state.get('intent', 'objective')

    # Check if this is a COMPARATIVE query with filter results
    if intent == 'comparative' and state.get('kg_data', {}).get('filter_results'):
        print(f"Formatting COMPARATIVE answer (multi-result)")
        answer = format_comparative_answer(state, llm)

        # Extract follow-up question from answer for state tracking
        lines = answer.split('\n')
        followup_line = [l for l in lines if l.startswith('Would you like')]
        followup_question = followup_line[0] if followup_line else None

        state['answer'] = answer
        state['follow_up_question'] = followup_question
        state['follow_up_context'] = {
            'projects': [r['project'] for r in state['kg_data']['filter_results']],
            'attribute': state['kg_data']['filter_metadata']['attribute']
        }

    else:
        # Existing logic for objective/analytical/financial queries
        # ... (keep existing code)
        pass

    # Build provenance
    state['provenance'] = build_provenance_trail(state)

    state['next_action'] = 'answer'

    print(f"\n✓ Answer composed")
    print(f"✓ Length: {len(state.get('answer', ''))} characters")

    return state
```

---

### Step 7: Integrate Conversation State into Orchestrator

**File**: `app/orchestration/langgraph_orchestrator.py`
**Location**: Update `query()` method (around line 210)

**Add at the beginning of `query()` method**:
```python
from app.services.conversation_state_manager import get_conversation_state_manager

def query(
    self,
    query: str,
    session_id: str = "default",
    conversation_history: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """Execute query through LangGraph"""

    # Initialize conversation state manager
    state_mgr = get_conversation_state_manager()

    # Check for yes/no response to pending follow-up
    pending_followup = state_mgr.get_pending_follow_up(session_id)
    is_yes_no = state_mgr.is_yes_no_response(query)

    if pending_followup and is_yes_no is not None:
        if is_yes_no:
            # User said "yes" - execute the follow-up action
            print(f"✓ User accepted follow-up question")
            print(f"  Follow-up: {pending_followup['question']}")
            print(f"  Context: {pending_followup['context']}")

            # Reconstruct query from follow-up context
            # Example: "Show pricing for projects: X, Y, Z"
            followup_context = pending_followup.get('context', {})
            projects = followup_context.get('projects', [])
            attribute = followup_context.get('attribute', '')

            # Override query with explicit follow-up query
            query = f"Show pricing details for: {', '.join(projects)}"
            print(f"  Executing follow-up: {query}")
        else:
            # User said "no" - acknowledge and continue with new query
            print(f"✓ User declined follow-up question")

        # Clear pending follow-up
        state_mgr.clear_pending_follow_up(session_id)

    # Get conversation history for LLM context
    if not conversation_history:
        conversation_history = state_mgr.get_conversation_history(
            session_id,
            max_turns=5
        )

    # ... rest of existing query() implementation ...

    # At the end, after getting result, save to conversation state:
    state_mgr.add_turn(
        session_id=session_id,
        query=query,
        response=result.get('answer', ''),
        intent=result.get('intent', 'unknown'),
        follow_up_question=result.get('follow_up_question'),
        follow_up_context=result.get('follow_up_context')
    )

    return result
```

---

### Step 8: Update Knowledge Graph Port Interface

**File**: `app/ports/knowledge_graph_port.py`
**Location**: Add method signature to interface (around line 50)

**Add**:
```python
@abstractmethod
def filter_projects_by_range(
    self,
    attribute: str,
    target_value: float,
    tolerance_pct: float = 10.0,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter projects where attribute value is within tolerance of target

    Args:
        attribute: Attribute name
        target_value: Target value
        tolerance_pct: Tolerance percentage (default 10%)
        location: Optional location filter

    Returns:
        List of matching projects with values
    """
    pass
```

---

## 🧪 Testing Plan

Once all steps are complete, test with:

```bash
# Start FastAPI server (if not running)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Test 1: Range query
curl -X POST "http://localhost:8000/api/qa/question" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show projects with units around 600 sq.ft", "project_id": null}'

# Expected response:
# - Intent: COMPARATIVE
# - 3-5 projects listed (Pradnyesh Shriniwas: 562, Sara Abhiruchi Tower: 635, etc.)
# - Insights about range
# - Follow-up question offered

# Test 2: Follow-up with "yes"
curl -X POST "http://localhost:8000/api/qa/question" \
  -H "Content-Type: application/json" \
  -d '{"question": "yes", "project_id": null, "session_id": "test_session_1"}'

# Expected: Executes follow-up action based on previous context

# Test 3: Follow-up with "no"
curl -X POST "http://localhost:8000/api/qa/question" \
  -H "Content-Type: application/json" \
  -d '{"question": "no", "project_id": null, "session_id": "test_session_2"}'

# Expected: Acknowledges "no", clears follow-up, ready for new query
```

---

## 📋 Implementation Checklist

- [x] **Step 1**: Conversation State Manager
- [x] **Step 2**: Range Query Support (KG Adapter)
- [ ] **Step 3**: COMPARATIVE Intent (Gemini LLM Adapter)
- [ ] **Step 4**: Range Query Planning (KG Query Planner Node)
- [ ] **Step 5**: Filter Action Execution (KG Executor Node)
- [ ] **Step 6**: Multi-Result Formatting (Answer Composer Node)
- [ ] **Step 7**: Conversation State Integration (Orchestrator)
- [ ] **Step 8**: Interface Update (Knowledge Graph Port)
- [ ] **Step 9**: End-to-end Testing

**Estimated Remaining Time**: 2-3 hours for Steps 3-9

---

## 🎯 Success Criteria

1. ✅ Query "Show projects with units around 600 sq.ft" returns 3-5 projects sorted by relevance
2. ✅ Response includes insights and follow-up question
3. ✅ Follow-up question is tracked in conversation state
4. ✅ Replying "yes" executes the follow-up action with previous context
5. ✅ Replying "no" clears follow-up and allows new query
6. ✅ Session state persists across multiple queries (same session_id)
7. ✅ Provenance includes all data sources

---

**Generated**: 2025-12-11
**Next Action**: Implement Steps 3-8 sequentially
