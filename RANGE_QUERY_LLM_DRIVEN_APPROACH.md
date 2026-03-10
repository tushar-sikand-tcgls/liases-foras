# Range Query Implementation: LLM-Driven Approach

**Philosophy**: Let the LLM make intelligent decisions, not hardcoded logic
**Architecture**: Hexagonal (Ports & Adapters) + LLM-driven query planning

---

## 🏗️ Architecture Principles

### 1. **LLM as Decision Maker** (via LLMPort)
- LLM classifies intent: COMPARATIVE for range queries
- LLM extracts parameters: target value, tolerance, comparison type
- LLM decides which KG action to use: `filter`, `fetch`, `aggregate`
- LLM generates insights and follow-up questions

### 2. **Adapters as Executors** (via KnowledgeGraphPort)
- KG adapter provides capabilities: `filter_projects_by_range()`, `fetch_attribute()`, etc.
- Executor node is **generic** - it routes to adapter methods based on LLM's plan
- No hardcoded rules in executor - it just interprets LLM's JSON plan

### 3. **Hexagonal Separation**
```
┌─────────────────────────────────────────┐
│ Core Domain (Orchestrator + Nodes)      │
│ - Intent classification                 │
│ - Query planning                        │
│ - Execution coordination                │
│ - Answer composition                    │
└─────────────────────────────────────────┘
              ↕ (Ports - Interfaces)
┌─────────────────────────────────────────┐
│ Adapters (External integrations)        │
│ - LLM Adapter (Gemini/Ollama)          │
│ - KG Adapter (DataService)             │
│ - Vector DB Adapter (ChromaDB)         │
│ - State Manager (Redis/In-memory)      │
└─────────────────────────────────────────┘
```

---

## ✅ Current Status

### Completed Components
1. ✅ **Conversation State Manager** (`app/services/conversation_state_manager.py`)
2. ✅ **KG Adapter Range Method** (`app/adapters/data_service_kg_adapter.py:255`)
   - `filter_projects_by_range()` method added to KnowledgeGraphPort implementation
3. ✅ **COMPARATIVE Intent** (`app/adapters/gemini_llm_adapter.py:104`)
   - LLM now recognizes 4 intents: OBJECTIVE, COMPARATIVE, ANALYTICAL, FINANCIAL

---

## 🔄 Remaining Implementation (LLM-Driven)

### Step 1: Update `plan_kg_queries()` Prompt (LLM Adapter)

**File**: `app/adapters/gemini_llm_adapter.py:175`

**Current Prompt**: Only knows `fetch`, `aggregate`, `compare` actions

**Update to**:
```python
def plan_kg_queries(self, context: Dict) -> List[Dict]:
    """Generate KG query plan - LLM decides the strategy"""

    prompt = f"""Generate a Knowledge Graph query plan for this context:

Intent: {context.get('intent')}
Attributes: {context.get('attributes', [])}
Projects: {context.get('projects', [])}
Locations: {context.get('locations', [])}
Original Query: "{context.get('query', '')}"

AVAILABLE KG ACTIONS:
1. **fetch** - Get specific value from ONE project
   Use when: Query mentions a specific project name

2. **filter** - Find multiple projects matching criteria
   Use when: Query asks to "show", "list", "find" projects OR uses range/comparison words
   Parameters:
   - attribute: The attribute to filter by
   - operation: "range" | "greater_than" | "less_than" | "equals"
   - target_value: Numeric value to compare against
   - tolerance_pct: For "range" operation (default 10%)
   - location: Optional location filter

3. **aggregate** - Calculate across multiple projects
   Use when: Query asks for "total", "average", "maximum" across projects

4. **compare** - Side-by-side comparison of specific projects
   Use when: Query asks to compare 2-3 named projects

RANGE QUERY EXAMPLES:
Query: "Show projects with units around 600 sq.ft"
Plan: [{{
  "action": "filter",
  "attribute": "Unit Saleable Size",
  "operation": "range",
  "target_value": 600,
  "tolerance_pct": 10,
  "location": null
}}]

Query: "Find projects under 100 Crore in Chakan"
Plan: [{{
  "action": "filter",
  "attribute": "Annual Sales Value",
  "operation": "less_than",
  "target_value": 100,
  "location": "Chakan"
}}]

Query: "List all projects with absorption rate > 1%"
Plan: [{{
  "action": "filter",
  "attribute": "Monthly Absorption Rate",
  "operation": "greater_than",
  "target_value": 1,
  "location": null
}}]

INSTRUCTIONS:
1. Analyze the query to extract numeric values and comparison words
2. Decide which KG action best fits the intent
3. For COMPARATIVE intent, prefer "filter" action
4. Extract target_value from phrases like "around 600", "under 100", "> 1%"
5. Infer tolerance: "around" = 10%, "approximately" = 15%, exact number = 5%

Return ONLY valid JSON array (no markdown):
[{{"action": "...", ...}}]
"""

    if self.use_ollama:
        response = self.ollama.generate(prompt, temperature=0.3)
        result = self._parse_json_from_text(response)
    else:
        response = self.model.generate_content(prompt)
        result = json.loads(response.text)

    if isinstance(result, dict):
        return [result]
    return result
```

**Key Changes**:
- ✅ **LLM Decides**: Prompt teaches LLM when to use `filter` action
- ✅ **Examples Included**: LLM learns from range query examples
- ✅ **Flexible**: LLM extracts target_value and tolerance from natural language
- ✅ **No Hardcoded Logic**: Just clear instructions for the LLM

---

### Step 2: Update KG Executor to Handle `filter` Action

**File**: `app/nodes/kg_executor_node.py:70`

**Current**: Only handles `fetch` and `aggregate`

**Add** (after existing action handlers):
```python
elif action == 'filter':
    # Filter projects by criteria - LLM decided to use this action
    attribute = step.get('attribute')
    operation = step.get('operation')
    target_value = step.get('target_value')
    tolerance_pct = step.get('tolerance_pct', 10.0)
    location = step.get('location')

    print(f"  Filtering projects: {attribute} {operation} {target_value}")
    if location:
        print(f"    Location filter: {location}")

    # Route to appropriate KG port method based on operation
    if operation == 'range':
        results = kg.filter_projects_by_range(
            attribute=attribute,
            target_value=float(target_value),
            tolerance_pct=float(tolerance_pct),
            location=location
        )
    # elif operation == 'greater_than':  # Future enhancement
    #     results = kg.filter_projects_gt(attribute, target_value, location)
    # elif operation == 'less_than':     # Future enhancement
    #     results = kg.filter_projects_lt(attribute, target_value, location)
    else:
        # Default to range for now
        results = kg.filter_projects_by_range(
            attribute=attribute,
            target_value=float(target_value),
            tolerance_pct=10.0,
            location=location
        )

    kg_data['filter_results'] = results
    kg_data['filter_metadata'] = {
        'attribute': attribute,
        'operation': operation,
        'target_value': target_value,
        'tolerance_pct': tolerance_pct,
        'location': location,
        'result_count': len(results)
    }

    print(f"  ✓ Found {len(results)} matching projects")
    for i, r in enumerate(results[:5], 1):
        print(f"    {i}. {r['project']}: {r['value']} {r['unit']}")
```

**Key Points**:
- ✅ **Generic Executor**: Just interprets LLM's plan, no hardcoded rules
- ✅ **Adapter Pattern**: Routes to KG port methods (`filter_projects_by_range`)
- ✅ **Extensible**: Can add `greater_than`, `less_than` operations later
- ✅ **Hexagonal**: Executor doesn't know HOW filtering works, just calls the port

---

### Step 3: Add Multi-Result Formatting to Answer Composer

**File**: `app/nodes/answer_composer_node.py`

**Add new method** (before `answer_composer_node()`):
```python
def format_comparative_answer(state: QueryState, llm: LLMPort) -> str:
    """
    Format answer for COMPARATIVE queries - LLM generates insights

    Returns:
    - Numbered list of results
    - LLM-generated insights
    - LLM-generated follow-up question
    """
    filter_results = state.get('kg_data', {}).get('filter_results', [])
    filter_metadata = state.get('kg_data', {}).get('filter_metadata', {})
    query = state.get('query')

    if not filter_results:
        return "No projects found matching your criteria."

    # Build result list (top 10)
    result_items = []
    for i, r in enumerate(filter_results[:10], 1):
        result_items.append(
            f"{i}. **{r['project']}**: {r['value']} {r['unit']} "
            f"({r['percentage_diff']:.1f}% from target)"
        )

    result_list = "\n".join(result_items)
    if len(filter_results) > 10:
        result_list += f"\n\n*... and {len(filter_results) - 10} more projects*"

    # LLM generates insights
    insight_prompt = f"""Analyze these search results and provide 2-3 insights:

Query: {query}
Target: {filter_metadata.get('target_value')} {filter_metadata.get('attribute')}
Results: {len(filter_results)} projects

Top matches:
{chr(10).join([f"- {r['project']}: {r['value']} {r['unit']}" for r in filter_results[:10]])}

Provide 2-3 bullet points about:
- Range/distribution of values
- Standout projects or patterns
- Market insights

Be concise and actionable. Use bullet points (•).
"""

    try:
        insights = llm.generate_text(insight_prompt)
    except:
        insights = "• Results sorted by closest match to target value"

    # LLM generates follow-up question
    followup_prompt = f"""User searched: {query}
Found: {len(filter_results)} projects

Suggest ONE specific follow-up question to help them explore further.

Good examples:
- "Would you like me to show pricing details for these projects?"
- "Should I compare absorption rates across these projects?"
- "Would you like to see developer information?"

Format: "Would you like me to [action]?"
Respond with ONLY the question.
"""

    try:
        followup = llm.generate_text(followup_prompt)
        followup = followup.strip().strip('"\'')
    except:
        followup = "Would you like more details about any of these projects?"

    # Compose answer
    answer = f"""## Search Results

{result_list}

**Total:** {len(filter_results)} projects found

---

## Insights

{insights}

---

## Next Steps

{followup}
"""

    return answer.strip()
```

**Update `answer_composer_node()`** function:
```python
def answer_composer_node(state: QueryState, llm: LLMPort) -> QueryState:
    """Node 8: Compose answer - LLM decides format"""

    print(f"\n{'='*80}")
    print(f"NODE 8: ANSWER COMPOSER")
    print(f"{'='*80}")

    state['execution_path'].append('answer_composer')

    intent = state.get('intent', 'objective')

    # Check if COMPARATIVE with filter results
    if intent == 'comparative' and state.get('kg_data', {}).get('filter_results'):
        print(f"Formatting COMPARATIVE answer (multi-result)")
        answer = format_comparative_answer(state, llm)

        # Extract follow-up for conversation state
        lines = answer.split('\n')
        followup_lines = [l for l in lines if 'Would you like' in l]
        followup_question = followup_lines[0] if followup_lines else None

        state['answer'] = answer
        state['follow_up_question'] = followup_question
        state['follow_up_context'] = {
            'projects': [r['project'] for r in state['kg_data']['filter_results']],
            'attribute': state['kg_data']['filter_metadata']['attribute']
        }

    else:
        # Existing logic for objective/analytical/financial
        # ... keep existing code ...
        pass

    # Build provenance
    state['provenance'] = build_provenance_trail(state)
    state['next_action'] = 'answer'

    return state
```

**Key Points**:
- ✅ **LLM Generates Insights**: Not templated, LLM creates contextual insights
- ✅ **LLM Generates Follow-up**: LLM suggests relevant next question
- ✅ **Hexagonal**: Uses `llm.generate_text()` via LLMPort interface

---

### Step 4: Integrate Conversation State (Orchestrator)

**File**: `app/orchestration/langgraph_orchestrator.py`

**Update `query()` method** (beginning):
```python
def query(
    self,
    query: str,
    session_id: str = "default",
    conversation_history: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """Execute query through LangGraph"""

    from app.services.conversation_state_manager import get_conversation_state_manager

    # Get conversation state manager
    state_mgr = get_conversation_state_manager()

    # Check for yes/no response to pending follow-up
    pending_followup = state_mgr.get_pending_follow_up(session_id)
    is_yes_no = state_mgr.is_yes_no_response(query)

    if pending_followup and is_yes_no is not None:
        if is_yes_no:
            # User said "yes" - reconstruct query from context
            print(f"✓ User accepted follow-up")
            context = pending_followup.get('context', {})
            projects = context.get('projects', [])

            # Build new query based on follow-up
            query = f"Show details for: {', '.join(projects[:3])}"
            print(f"  Executing: {query}")
        else:
            print(f"✓ User declined follow-up")

        state_mgr.clear_pending_follow_up(session_id)

    # Get conversation history for LLM context
    if not conversation_history:
        conversation_history = state_mgr.get_conversation_history(
            session_id,
            max_turns=5
        )

    # ... rest of existing query() implementation ...

    # At end, save conversation turn
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

**Key Points**:
- ✅ **Conversation Memory**: Tracks multi-turn dialogue
- ✅ **Yes/No Handling**: Interprets follow-up responses
- ✅ **Hexagonal**: Uses State Manager port, orchestrator doesn't know implementation

---

## 🎯 Complete Flow Example

### Query: "Show projects with units around 600 sq.ft in Chakan"

**Step 1: Intent Classification (LLM)**
```json
{
  "intent": "comparative",
  "subcategory": "range_filter",
  "confidence": 0.95,
  "reasoning": "User wants list of projects matching range criteria"
}
```

**Step 2: Attribute Resolution (Vector DB)**
```
"units around 600 sq.ft" → "Unit Saleable Size"
```

**Step 3: Entity Resolution (KG)**
```
"Chakan" → Location: "Chakan"
No specific project → skip
```

**Step 4: Query Planning (LLM)**
```json
[{
  "action": "filter",
  "attribute": "Unit Saleable Size",
  "operation": "range",
  "target_value": 600,
  "tolerance_pct": 10,
  "location": "Chakan"
}]
```

**Step 5: Execution (KG Adapter)**
```python
kg.filter_projects_by_range(
    attribute="Unit Saleable Size",
    target_value=600.0,
    tolerance_pct=10.0,
    location="Chakan"
)
# Returns: [
#   {'project': 'Pradnyesh Shriniwas', 'value': 562, 'unit': 'sq. ft.'},
#   {'project': 'Sara Abhiruchi Tower', 'value': 635, 'unit': 'sq. ft.'},
#   {'project': 'Siddhivinayak Residency', 'value': 573, 'unit': 'sq. ft.'}
# ]
```

**Step 6: Answer Composition (LLM)**
```markdown
## Search Results

1. **Pradnyesh Shriniwas**: 562 sq. ft. (6.3% from target)
2. **Sara Abhiruchi Tower**: 635 sq. ft. (5.8% from target)
3. **Siddhivinayak Residency**: 573 sq. ft. (4.5% from target)

**Total:** 3 projects found

---

## Insights

• All three projects cluster tightly around your 600 sq.ft target
• Siddhivinayak Residency is the closest match at 573 sq.ft
• This unit size is popular in Chakan for 2BHK configurations

---

## Next Steps

Would you like me to show pricing details for these projects?
```

**Step 7: Conversation State**
```python
state_mgr.add_turn(
    session_id="user_123",
    query="Show projects with units around 600 sq.ft in Chakan",
    response="[answer above]",
    intent="comparative",
    follow_up_question="Would you like me to show pricing details for these projects?",
    follow_up_context={'projects': ['Pradnyesh Shriniwas', 'Sara Abhiruchi Tower', 'Siddhivinayak Residency']}
)
```

**User: "yes"**

**Step 8: Follow-up Execution**
```python
# Orchestrator detects yes/no response
is_yes = state_mgr.is_yes_no_response("yes")  # True
pending = state_mgr.get_pending_follow_up("user_123")  # {...}

# Reconstruct query
new_query = "Show pricing for: Pradnyesh Shriniwas, Sara Abhiruchi Tower, Siddhivinayak Residency"

# Execute new query...
```

---

## 📊 Implementation Checklist

- [x] **Step 1**: Conversation State Manager
- [x] **Step 2**: KG Adapter Range Method
- [x] **Step 3**: COMPARATIVE Intent (LLM Adapter)
- [ ] **Step 4**: Update `plan_kg_queries()` prompt (LLM Adapter)
- [ ] **Step 5**: Add `filter` action handler (KG Executor)
- [ ] **Step 6**: Multi-result formatting (Answer Composer)
- [ ] **Step 7**: Conversation state integration (Orchestrator)
- [ ] **Step 8**: End-to-end testing

**Estimated Time**: 1-2 hours for Steps 4-8

---

## 🏗️ Hexagonal Architecture Compliance

```
┌─────────────────────────────────────────────┐
│ CORE DOMAIN (Business Logic)                │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │ LangGraph Orchestrator               │  │
│  │ - Intent classification              │  │
│  │ - Query planning                     │  │
│  │ - Execution coordination             │  │
│  └──────────────────────────────────────┘  │
│             ↕ (Uses Ports)                  │
│  ┌──────────────────────────────────────┐  │
│  │ Ports (Interfaces)                   │  │
│  │ - LLMPort: classify_intent(),        │  │
│  │           plan_kg_queries(),         │  │
│  │           generate_text()            │  │
│  │ - KnowledgeGraphPort:                │  │
│  │           filter_projects_by_range() │  │
│  │ - VectorDBPort: search()             │  │
│  │ - StateManagerPort: (implicit)       │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
             ↕ (Implemented by)
┌─────────────────────────────────────────────┐
│ ADAPTERS (External Integrations)            │
│                                             │
│  • GeminiLLMAdapter (implements LLMPort)   │
│  • DataServiceKGAdapter                    │
│    (implements KnowledgeGraphPort)         │
│  • ChromaVectorDBAdapter                   │
│    (implements VectorDBPort)               │
│  • ConversationStateManager (standalone)   │
└─────────────────────────────────────────────┘
```

**Key Principles Maintained**:
1. ✅ **Core never depends on adapters** - only on port interfaces
2. ✅ **LLM makes decisions** - adapters just execute
3. ✅ **Swappable implementations** - can replace Gemini with Ollama via port
4. ✅ **Testable** - can mock LLMPort and KnowledgeGraphPort

---

**Next Action**: Implement Step 4 (Update `plan_kg_queries()` prompt)
**File**: `app/adapters/gemini_llm_adapter.py:175`
