# Qwen 2.5 Integration for QA Tests - Action Required

## 🔍 Problem Identified

You were **correct** - Qwen 2.5 was NOT being used for the QA tests!

The tests ran with **Gemini** (which is why all 121 tests failed - likely hit rate limits or had connection issues).

## 🎯 Root Cause

The QA automation system is **hardcoded** to use Gemini:

**File:** `app/orchestration/langgraph_orchestrator.py`
**Line 79:**
```python
self.llm = llm or get_gemini_llm_adapter()  # ← HARDCODED!
```

Setting `export LLM_PROVIDER=ollama` had **no effect** because the code doesn't check this variable.

## 📋 What Needs to Be Done

To use Qwen 2.5 for QA tests, we need to:

### Step 1: Create Ollama LLM Adapter

Create `app/adapters/ollama_llm_adapter.py` that implements the `LLMPort` interface (same as Gemini adapter).

**Methods to implement:**
- `classify_intent()` - Classify query intent
- `extract_entities()` - Extract projects, developers, locations
- `plan_kg_queries()` - Generate KG query plan
- `compose_answer()` - Compose natural language answer
- `ask_clarification()` - Generate clarification questions
- `generate_json_response()` - Generate structured JSON
- `explain_calculation()` - Explain financial calculations

**Challenge:** The Gemini adapter uses JSON mode and structured outputs. Qwen 2.5 via Ollama needs prompting to return valid JSON.

### Step 2: Create LLM Adapter Factory

Create `app/adapters/llm_adapter_factory.py`:

```python
import os
from app.adapters.gemini_llm_adapter import get_gemini_llm_adapter
from app.adapters.ollama_llm_adapter import get_ollama_llm_adapter

def get_llm_adapter():
    """Get LLM adapter based on LLM_PROVIDER environment variable"""
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "ollama":
        return get_ollama_llm_adapter()
    elif provider == "gemini":
        return get_gemini_llm_adapter()
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
```

### Step 3: Update Orchestrator

**File:** `app/orchestration/langgraph_orchestrator.py`
**Line 42:** Change from:
```python
from app.adapters.gemini_llm_adapter import get_gemini_llm_adapter
```

To:
```python
from app.adapters.llm_adapter_factory import get_llm_adapter
```

**Line 79:** Change from:
```python
self.llm = llm or get_gemini_llm_adapter()
```

To:
```python
self.llm = llm or get_llm_adapter()
```

### Step 4: Test

```bash
# Use Ollama (Qwen 2.5)
export LLM_PROVIDER=ollama
python3 -m app.testing.cli_runner --excel-path change-request/BDD-test-cases/BDD_Test_Cases_Micro.xlsx --run-id qwen_test

# Use Gemini (original)
export LLM_PROVIDER=gemini
python3 -m app.testing.cli_runner --excel-path change-request/BDD-test-cases/BDD_Test_Cases_Micro.xlsx --run-id gemini_test
```

## 🚀 Quick Alternative (Simpler)

If you want a quick workaround without full adapter implementation:

### Option A: Modify Gemini Adapter to Use Qwen

**File:** `app/adapters/gemini_llm_adapter.py`

Add environment variable check in `__init__`:

```python
def __init__(self, api_key: Optional[str] = None):
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "ollama":
        # Use Ollama service instead
        from app.services.ollama_service import get_ollama_service
        self.ollama = get_ollama_service()
        self.use_ollama = True
        print("✅ Using Ollama (Qwen 2.5) instead of Gemini")
    else:
        # Original Gemini code
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.use_ollama = False
```

Then in each method, check `self.use_ollama` and call Ollama service accordingly.

**Pros:**
- Quick to implement
- No new files needed
- Works immediately

**Cons:**
- Mixes concerns (Gemini adapter knows about Ollama)
- Less clean architecture

## 📊 Why Tests Failed (0/121)

The tests likely failed because:

1. **Gemini was used** (not Qwen) - you saw no Ollama console output
2. **Rate limits** - Gemini has 60 requests/min limit, full suite has 121 tests
3. **Connection issues** - Network problems or API timeouts

## ✅ Next Steps

**Recommended Approach:**

1. **Immediate:** Use the Quick Alternative (Option A) to get Qwen working fast
2. **Long-term:** Implement proper Ollama adapter following the `LLMPort` interface
3. **Test:** Run micro tests first (5 tests) to validate it works
4. **Scale:** Run full suite (121 tests) once micro tests pass

## 💡 Benefits Once Integrated

With Qwen 2.5 properly integrated:

✅ **No rate limits** - Run 121 tests without delays
✅ **No API costs** - Completely free
✅ **Faster iteration** - Test locally without network latency
✅ **Privacy** - Data stays on your machine

## 📁 Files Referenced

- `app/orchestration/langgraph_orchestrator.py` - Needs update (line 79)
- `app/adapters/gemini_llm_adapter.py` - Template for Ollama adapter
- `app/services/ollama_service.py` - Already created ✅
- `app/services/llm_factory.py` - Already created ✅ (but not used by QA system)

## 🔧 Current Status

- ✅ Ollama service created and working
- ✅ LLM factory created and working
- ❌ QA system not integrated with LLM factory
- ❌ Ollama LLM adapter not created
- ❌ Environment variable not respected by orchestrator

---

**The good news:** You now have all the Ollama infrastructure ready. It just needs to be connected to the QA system!

**Would you like me to implement one of these approaches?**
