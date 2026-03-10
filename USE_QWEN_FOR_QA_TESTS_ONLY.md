# Using Qwen 2.5 for QA Tests Only (Keep Gemini for Streamlit)

## ✅ Summary

You discovered that Qwen 2.5 (Ollama) was **NOT being used** for the QA tests because the system is hardcoded to use Gemini.

**Your requirement:**
- **Streamlit app** → Continue using Gemini (no change)
- **QA CLI tests** → Use Qwen 2.5 (Ollama) to avoid rate limits

This document outlines how to integrate Ollama for testing only, without affecting Streamlit.

## 🎯 What Was Discovered

1. **QA tests used Gemini** - That's why you saw no Ollama console output
2. **Hardcoded in orchestrator** - `app/orchestration/langgraph_orchestrator.py:79` calls `get_gemini_llm_adapter()` directly
3. **Environment variable ignored** - Setting `LLM_PROVIDER=ollama` had no effect

## ⚙️ Current Status

✅ **Already Created:**
- `app/services/ollama_service.py` - Works perfectly
- `app/services/llm_factory.py` - Works for simple text generation
- `test_ollama_qwen.py` - All tests passed
- `example_use_qwen_for_testing.py` - Working examples

❌ **Missing:**
- QA system integration with Ollama
- All QA system methods (7 total) need Ollama equivalents

## 🔧 The Challenge

The Gemini adapter implements 7 methods that the QA system needs:

1. `classify_intent()` - Returns structured JSON
2. `extract_entities()` - Returns structured JSON
3. `plan_kg_queries()` - Returns structured JSON array
4. `compose_answer()` - Returns natural language
5. `ask_clarification()` - Returns natural language
6. `generate_json_response()` - Returns structured JSON
7. `explain_calculation()` - Returns natural language

**Gemini advantage:** Has native JSON mode (`response_mime_type: "application/json"`)
**Qwen challenge:** Needs careful prompting to return valid JSON

## 📋 Implementation Options

### Option A: Quick Integration (Recommended for Testing)

Modify `app/adapters/gemini_llm_adapter.py` to check `LLM_PROVIDER` environment variable in the `__init__` method and delegate JSON methods to Ollama.

**Changes needed:** ~20 lines in one file

**Steps:**
1. Update `__init__` to check `LLM_PROVIDER`
2. Add `self.ollama` and `self.use_ollama` flag
3. Wrap each method to call Ollama if `self.use_ollama == True`

**Usage:**
```bash
# CLI tests with Qwen (no rate limits)
export LLM_PROVIDER=ollama
python3 -m app.testing.cli_runner --excel-path tests.xlsx

# Streamlit with Gemini (unchanged)
streamlit run frontend/streamlit_app.py
```

**Pros:** Quick, minimal changes, won't break Streamlit
**Cons:** Mixes concerns, not architecturally clean

### Option B: Full Adapter Implementation

Create separate `app/adapters/ollama_llm_adapter.py` that implements the `LLMPort` interface.

**Changes needed:** ~400 lines new file + factory pattern

**Pros:** Clean architecture, proper separation
**Cons:** Takes longer, requires implementing all 7 methods correctly

## 🚀 Quickest Path Forward

Since you want **testing only** and you need this working now, I recommend:

### Minimal Modification Approach

Create a wrapper file that doesn't modify the existing adapter:

```python
# app/adapters/test_llm_adapter.py

import os
from app.adapters.gemini_llm_adapter import GeminiLLMAdapter
from app.services.ollama_service import get_ollama_service
import json

class TestLLMAdapter(GeminiLLMAdapter):
    """
    LLM adapter for testing that uses Ollama when LLM_PROVIDER=ollama,
    otherwise uses Gemini
    """

    def __init__(self, api_key=None):
        use_ollama = os.getenv("LLM_PROVIDER", "").lower() == "ollama"

        if use_ollama:
            self.ollama = get_ollama_service()
            self.use_ollama = True
            print("✅ Using Ollama (Qwen 2.5) for testing")
        else:
            super().__init__(api_key)
            self.use_ollama = False

    def compose_answer(self, query, kg_data, computation_results=None,
                      attributes_metadata=None, project_metadata=None):
        if self.use_ollama:
            # Simple Ollama implementation for testing
            context = f"Query: {query}\nData: {json.dumps(kg_data)}"
            return self.ollama.generate(context, temperature=0.3)
        else:
            return super().compose_answer(query, kg_data, computation_results,
                                         attributes_metadata, project_metadata)

    # Add similar wrappers for other methods...
```

Then update `app/orchestration/langgraph_orchestrator.py`:

```python
# Line 42: Change from
from app.adapters.gemini_llm_adapter import get_gemini_llm_adapter

# To
from app.adapters.test_llm_adapter import TestLLMAdapter

# Line 79: Change from
self.llm = llm or get_gemini_llm_adapter()

# To
self.llm = llm or TestLLMAdapter()
```

## ⚠️ Important Notes

1. **JSON Parsing:** Qwen 2.5 doesn't have native JSON mode, so responses may need cleanup
2. **Prompt Engineering:** Each method needs careful prompts to get structured output
3. **Testing Required:** Test micro suite first before running full 121 tests
4. **Streamlit Unaffected:** Streamlit won't set `LLM_PROVIDER`, so it'll always use Gemini

## 📊 Expected Results

Once integrated:

**With Gemini (Streamlit):**
- ✅ No changes to existing behavior
- ✅ JSON mode works perfectly
- ⚠️ 60 requests/min rate limit

**With Qwen (CLI Tests):**
- ✅ No rate limits (unlimited tests)
- ✅ Completely free
- ✅ Data stays local
- ⚠️ May need prompt tuning for JSON accuracy

## 📝 Next Steps

1. **Decide:** Choose Option A (quick) or Option B (proper)
2. **Implement:** Make the minimal changes above
3. **Test Micro:** Run 5-test micro suite first
   ```bash
   export LLM_PROVIDER=ollama
   python3 -m app.testing.cli_runner --excel-path BDD_Test_Cases_Micro.xlsx
   ```
4. **Debug:** Fix any JSON parsing issues
5. **Scale:** Run full 121-test suite once micro works

## 💡 Key Insight

**The integration is ~80% done!** You have:
- ✅ Ollama service working
- ✅ Qwen 2.5 running locally
- ✅ Test infrastructure ready

You just need the "glue code" to make the QA system call Ollama instead of Gemini when `LLM_PROVIDER=ollama`.

---

**Would you like me to implement the minimal approach now?** It's about 50 lines of code to get Qwen working for your QA tests while keeping Streamlit on Gemini.
