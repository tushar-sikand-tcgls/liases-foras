# Gemini Interactions API Integration - Complete Guide

## Overview

The Gemini client wrapper has been refactored to use Google's **Interactions API** (Beta) for server-side conversation state management. This eliminates manual conversation history tracking and enables true chain-of-thought capabilities across multi-turn dialogues.

### Key Benefits

1. **Server-side State Management**: Google stores conversation context server-side, eliminating client-side history management
2. **Implicit Caching**: Using `previous_interaction_id` leverages Google's caching for faster, cheaper API calls
3. **Stateless Client**: Your agent only needs to pass interaction IDs, not full conversation history
4. **Chain-of-Thought**: LLM can link queries across turns (e.g., Turn 1: "What is IRR?", Turn 2: user provides parameters → LLM calculates)
5. **Conversation Reload**: Retrieve full interaction history after app restarts using `get_interaction()`

---

## Architecture Changes

### Before (Manual State Management)

```python
# Client manually tracked conversation history
conversation_history = []

# Turn 1
response1 = llm.classify_intent(query1, conversation_history)
conversation_history.append({"role": "user", "content": query1})
conversation_history.append({"role": "assistant", "content": response1})

# Turn 2
response2 = llm.classify_intent(query2, conversation_history)
# ... more manual appending
```

**Problems:**
- Client must maintain full conversation history
- No caching benefits
- History grows unbounded (memory issues)
- No server-side persistence

### After (Interactions API)

```python
# Turn 1: Start interaction
result1 = llm.classify_intent(query1, previous_interaction_id=None)
interaction_id = result1["interaction_id"]  # Store this ID

# Turn 2: Continue interaction
result2 = llm.classify_intent(query2, previous_interaction_id=interaction_id)
new_interaction_id = result2["interaction_id"]  # Update ID

# Turn 3: Continue...
result3 = llm.classify_intent(query3, previous_interaction_id=new_interaction_id)
```

**Advantages:**
- Client only passes a single ID (not full history)
- Google handles state server-side
- Automatic caching optimization
- Can reload history anytime with `get_interaction(id)`

---

## Components Added

### 1. `GeminiInteractionsAdapter` (New)
**File:** `app/adapters/gemini_interactions_adapter.py`

Low-level wrapper around Google's Interactions API.

**Key Methods:**

#### `start_interaction(input_text, model=None, tools=None, system_instruction=None)`
Start a new conversation (first turn).

```python
from app.adapters.gemini_interactions_adapter import get_gemini_interactions_adapter

adapter = get_gemini_interactions_adapter()
result = adapter.start_interaction(
    input_text="What is IRR?",
    system_instruction="You are a real estate financial analyst."
)

print(result.interaction_id)  # Save this for next turn
print(result.text_response)
```

**Returns:** `InteractionResult` with:
- `interaction_id`: String ID to use in next turn
- `text_response`: LLM's response text
- `function_calls`: List of function calls made (if any)
- `status`: "completed", "in_progress", etc.
- `usage`: Token usage statistics

#### `continue_interaction(previous_interaction_id, input_text, model=None, tools=None)`
Continue an existing conversation (subsequent turns).

```python
# Turn 2
result2 = adapter.continue_interaction(
    previous_interaction_id=result.interaction_id,  # Link to Turn 1
    input_text="Calculate with investment of 100 Crore"
)

print(result2.interaction_id)  # New ID for Turn 3
print(result2.text_response)
```

#### `get_interaction(interaction_id)`
Retrieve past interaction history.

```python
# Reload conversation after app restart
history = adapter.get_interaction("abc123...")
print(history["inputs"])   # All user inputs
print(history["outputs"])  # All LLM outputs
print(history["status"])   # Interaction status
```

#### `start_interaction_with_functions()` / `continue_interaction_with_functions()`
Convenience methods for function calling.

```python
from google.generativeai.types import FunctionDeclaration

functions = [
    FunctionDeclaration(
        name="get_project_irr",
        description="Calculate IRR for a project",
        parameters={...}
    )
]

result = adapter.start_interaction_with_functions(
    input_text="What's the IRR of Sara City?",
    function_declarations=functions
)
```

---

### 2. `GeminiLLMAdapter` (Refactored)
**File:** `app/adapters/gemini_llm_adapter.py`

High-level LLM adapter now uses Interactions API internally.

**Updated Methods:**

All methods now accept `previous_interaction_id` parameter and return `interaction_id` in result:

#### `classify_intent(query, previous_interaction_id=None)`
```python
llm = get_gemini_llm_adapter()

# Turn 1
result1 = llm.classify_intent("What is IRR of Sara City?")
# Returns: {"intent": "financial", "interaction_id": "abc123..."}

# Turn 2 - with context
result2 = llm.classify_intent(
    "Calculate it",
    previous_interaction_id=result1["interaction_id"]
)
# LLM remembers "it" refers to IRR of Sara City from Turn 1
```

#### `extract_entities(query, previous_interaction_id=None)`
```python
# Turn 1
result1 = llm.extract_entities("Tell me about Sara City")
# Returns: {"projects": ["Sara City"], "interaction_id": "abc123..."}

# Turn 2 - ambiguous query but uses context
result2 = llm.extract_entities(
    "What's the sold percentage?",
    previous_interaction_id=result1["interaction_id"]
)
# LLM infers "Sara City" from Turn 1 context
```

#### `plan_kg_queries(context, previous_interaction_id=None)`
```python
result = llm.plan_kg_queries(
    context={
        "intent": "financial",
        "projects": ["Sara City"],
        "attributes": ["IRR"],
        "query": "Calculate IRR"
    },
    previous_interaction_id=interaction_id  # Optional context
)
# Returns: {"query_plan": [...], "interaction_id": "abc123..."}
```

#### `compose_answer(query, kg_data, previous_interaction_id=None, ...)`
```python
result = llm.compose_answer(
    query="What is IRR of Sara City?",
    kg_data={"project_name": "Sara City"},
    project_metadata={...},
    computation_results=None,  # No IRR calculated yet
    previous_interaction_id=None  # First turn
)
# Returns: {"answer": "IRR is...", "interaction_id": "abc123..."}

# Turn 2 - provide parameters
result2 = llm.compose_answer(
    query="Initial investment: 100 Crore, ...",
    kg_data={"project_name": "Sara City"},
    computation_results={"irr": 18.5},  # Now calculated
    previous_interaction_id=result["interaction_id"]  # Link to Turn 1
)
# LLM uses context from Turn 1 to generate answer
```

---

### 3. `GeminiFunctionCallingService` (Updated)
**File:** `app/services/gemini_function_calling_service.py`

Function calling service now accepts and returns `interaction_id`.

```python
service = get_gemini_function_calling_service()

# Turn 1
result1 = service.process_query(
    query="What is the IRR of Sara City?",
    system_prompt="You are a real estate analyst.",
    previous_interaction_id=None  # First turn
)

# Turn 2
result2 = service.process_query(
    query="Calculate it with 100 Cr investment",
    previous_interaction_id=result1["interaction_id"]  # Link to Turn 1
)
```

**Note:** Current implementation maintains backward compatibility. Full Interactions API integration for function calling loop is planned for future optimization (flag: `uses_interactions_api: False` in metadata).

---

## Usage Patterns

### Pattern 1: Simple Q&A with Context

```python
from app.adapters.gemini_llm_adapter import get_gemini_llm_adapter

llm = get_gemini_llm_adapter()

# Store interaction_id in your application state (e.g., session, database)
current_interaction_id = None

def handle_user_query(query):
    global current_interaction_id

    # Classify intent with context
    intent_result = llm.classify_intent(
        query=query,
        previous_interaction_id=current_interaction_id
    )

    # Extract entities with context
    entities_result = llm.extract_entities(
        query=query,
        previous_interaction_id=intent_result["interaction_id"]
    )

    # ... process query ...

    # Update interaction_id for next turn
    current_interaction_id = entities_result["interaction_id"]

    return response
```

### Pattern 2: Financial Query with Parameter Gathering

```python
# Turn 1: User asks about IRR without parameters
def turn_1():
    result = llm.compose_answer(
        query="What is IRR of Sara City?",
        kg_data={},
        computation_results=None,  # No parameters yet
        previous_interaction_id=None
    )
    # LLM provides educational answer + asks for parameters
    # Store result["interaction_id"] in session

# Turn 2: User provides parameters
def turn_2(session_interaction_id):
    result = llm.compose_answer(
        query="Initial investment: 100 Crore, Sales: 60 Crore/year, ...",
        kg_data={},
        computation_results={"irr": 18.5},  # Calculated
        previous_interaction_id=session_interaction_id  # Link to Turn 1
    )
    # LLM uses context to provide IRR calculation + explanation
```

### Pattern 3: Conversation State in Streamlit/Web App

```python
import streamlit as st
from app.adapters.gemini_llm_adapter import get_gemini_llm_adapter

# Initialize session state
if "interaction_id" not in st.session_state:
    st.session_state.interaction_id = None

llm = get_gemini_llm_adapter()

# User input
query = st.text_input("Ask a question:")

if query:
    # Process with context from previous turns
    result = llm.classify_intent(
        query=query,
        previous_interaction_id=st.session_state.interaction_id
    )

    # Update interaction_id for next turn
    st.session_state.interaction_id = result["interaction_id"]

    # Display response
    st.write(result)
```

### Pattern 4: Reload Conversation After Restart

```python
from app.adapters.gemini_interactions_adapter import get_gemini_interactions_adapter

adapter = get_gemini_interactions_adapter()

# App starts up - reload last conversation
last_interaction_id = get_from_database()  # Retrieve stored ID

if last_interaction_id:
    # Reload full conversation history
    history = adapter.get_interaction(last_interaction_id)

    print("Conversation history:")
    for input_data in history["inputs"]:
        print(f"User: {input_data}")
    for output_data in history["outputs"]:
        print(f"Assistant: {output_data}")

    # Continue conversation
    result = adapter.continue_interaction(
        previous_interaction_id=last_interaction_id,
        input_text="Continue from where we left off..."
    )
```

---

## Testing

Run the comprehensive test suite:

```bash
python test_interactions_api.py
```

**Tests included:**

1. **Basic Interaction Chaining**: 3-turn conversation testing context memory
2. **Financial Query Chaining**: Exact user scenario - IRR query across 2 turns
3. **Retrieval of Past Interactions**: Reload conversation after "restart"
4. **Entity Extraction with Context**: Ambiguous queries resolved via context

**Expected Output:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║               GEMINI INTERACTIONS API TEST SUITE                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

TEST 1: Basic Interaction Chaining
...
✅ Test 1 Passed: Context maintained across 3 turns

TEST 2: Financial Query Chaining (IRR Scenario)
...
✅ Test 2 Passed: Financial query chaining with parameter gathering

TEST 3: Retrieve Past Interaction
...
✅ Test 3 Passed: Successfully retrieved past interaction

TEST 4: Entity Extraction with Context
...
✅ Test 4 Passed: Entity extraction leverages conversation context

════════════════════════════════════════════════════════════════════════════════
✅ ALL TESTS PASSED
════════════════════════════════════════════════════════════════════════════════

Key Takeaways:
1. ✅ Conversation context is maintained across turns via interaction_id
2. ✅ Server-side state management eliminates manual history tracking
3. ✅ Client remains stateless - only passes interaction IDs
4. ✅ Past interactions can be retrieved for auditing/debugging
5. ✅ Chain-of-thought works: LLM links Turn 1 query with Turn 2 parameters
```

---

## Migration Guide

### For Existing Code Using `GeminiLLMAdapter`

**Old Code:**
```python
llm = get_gemini_llm_adapter()
conversation_history = []

result = llm.classify_intent(query, conversation_history)
conversation_history.append(...)  # Manual tracking
```

**New Code:**
```python
llm = get_gemini_llm_adapter()
interaction_id = None  # Start with None

result = llm.classify_intent(query, previous_interaction_id=interaction_id)
interaction_id = result["interaction_id"]  # Update for next turn
```

### Backward Compatibility

All methods still accept `conversation_history` parameter (deprecated but functional). However, `previous_interaction_id` is preferred:

```python
# Both work, but prefer new style
result = llm.classify_intent(query, conversation_history=[...])  # Old style
result = llm.classify_intent(query, previous_interaction_id=id)  # New style (recommended)
```

---

## API Reference

### `InteractionResult` Dataclass

```python
@dataclass
class InteractionResult:
    interaction_id: str           # ID for this interaction (use in next turn)
    text_response: str            # LLM's text response
    function_calls: List[Dict]    # List of function calls made (if any)
    status: str                   # "completed", "in_progress", "failed"
    usage: Optional[Dict]         # Token usage stats
    outputs: Optional[List]       # Raw output objects from API
```

### Token Usage Tracking

```python
result = adapter.start_interaction("Hello")
print(result.usage)
# {
#   "prompt_tokens": 150,
#   "candidates_tokens": 45,
#   "total_tokens": 195,
#   "cached_tokens": 0  # Will be > 0 when using previous_interaction_id
# }
```

---

## Best Practices

### 1. Always Update `interaction_id`

```python
# ❌ Wrong - interaction_id not updated
result1 = llm.classify_intent(query1, previous_interaction_id=id)
result2 = llm.classify_intent(query2, previous_interaction_id=id)  # Still using old ID!

# ✅ Correct - chain the IDs
result1 = llm.classify_intent(query1, previous_interaction_id=id)
id = result1["interaction_id"]  # Update
result2 = llm.classify_intent(query2, previous_interaction_id=id)  # Use new ID
```

### 2. Store `interaction_id` in Application State

```python
# Web app session
session["current_interaction_id"] = result["interaction_id"]

# Database for persistence
db.save("user_123", "last_interaction_id", result["interaction_id"])

# In-memory cache
cache.set(f"conversation:{session_id}", result["interaction_id"])
```

### 3. Handle Errors Gracefully

```python
try:
    result = adapter.continue_interaction(
        previous_interaction_id=interaction_id,
        input_text=query
    )
except Exception as e:
    print(f"Interaction failed: {e}")
    # Fallback: start new interaction
    result = adapter.start_interaction(input_text=query)
```

### 4. Monitor Token Usage

```python
if result.usage["cached_tokens"] > 0:
    print(f"✅ Saved tokens via caching: {result.usage['cached_tokens']}")
else:
    print("⚠️ No caching benefit - check if previous_interaction_id is set")
```

---

## Limitations & Future Work

### Current Limitations

1. **Ollama Mode**: Interactions API not supported when `LLM_PROVIDER=ollama` (returns `interaction_id: None`)
2. **Function Calling Service**: Uses old chat API for function calling loop (flag: `uses_interactions_api: False`)
3. **Beta API**: Interactions API is in Beta - schemas may change

### Planned Enhancements

1. **Full Function Calling Integration**: Refactor `GeminiFunctionCallingService` to use Interactions API for the entire function calling loop
2. **Conversation Analytics**: Add methods to analyze conversation flow (`get_conversation_tree()`, `get_turn_count()`, etc.)
3. **Conversation Branching**: Support creating branches from specific interaction points
4. **Automatic Cleanup**: Implement TTL-based cleanup of old interactions

---

## Resources

- **Google Interactions API Docs**: https://ai.google.dev/gemini-api/docs/interactions
- **Test Script**: `test_interactions_api.py`
- **Implementation Files**:
  - `app/adapters/gemini_interactions_adapter.py` (Low-level wrapper)
  - `app/adapters/gemini_llm_adapter.py` (High-level LLM adapter)
  - `app/services/gemini_function_calling_service.py` (Function calling service)

---

## Summary

The Interactions API integration provides:

✅ **Server-side state management** - No manual conversation history tracking
✅ **Stateless client design** - Only pass interaction IDs
✅ **Implicit caching** - Cost & speed optimization via `previous_interaction_id`
✅ **Chain-of-thought** - LLM links queries across turns (your requested feature!)
✅ **Conversation reload** - Retrieve history after restarts
✅ **Backward compatibility** - Existing code continues to work

The refactoring solves your original request: **"It should be able to chain of thought to link the 2 queries and answer the question."** Now the LLM can remember Turn 1 context when processing Turn 2!
