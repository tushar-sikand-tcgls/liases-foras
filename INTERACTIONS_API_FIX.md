# Interactions API Fix - Function Declaration Format

**Issue:** When migrating from the old Gemini API to the new Interactions API, the function declaration format changed.

**Date:** 2025-01-12
**Status:** ✅ Fixed

---

## ❌ Problem: Old Format (Didn't Work with Interactions API)

```python
# OLD FORMAT (types.Schema nested structure)
kg_function = types.FunctionDeclaration(
    name="knowledge_graph_lookup",
    description="...",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "query_type": types.Schema(
                type=types.Type.STRING,
                description="...",
                enum=[...]
            ),
            "project_name": types.Schema(
                type=types.Type.STRING,
                description="..."
            )
        },
        required=["query_type"]
    )
)
```

**Error:** This format caused issues with the Interactions API because `types.Schema` nested structure wasn't compatible.

---

## ✅ Solution: New Format (Works with Interactions API)

```python
# NEW FORMAT (raw dict → types.FunctionDeclaration)
kg_function_dict = {
    "name": "knowledge_graph_lookup",
    "description": "...",
    "parameters": {
        "type": "object",
        "properties": {
            "query_type": {
                "type": "string",
                "description": "...",
                "enum": [...]
            },
            "project_name": {
                "type": "string",
                "description": "..."
            }
        },
        "required": ["query_type"]
    }
}

# Convert to FunctionDeclaration
kg_function = types.FunctionDeclaration(**kg_function_dict)
```

**Why This Works:**
1. Raw dict format is the **native JSON schema** format
2. `types.FunctionDeclaration(**dict)` handles conversion automatically
3. Compatible with both old API and new Interactions API
4. Matches Google's official examples

---

## 📋 Key Differences

| Aspect | Old Format | New Format |
|--------|------------|------------|
| **Parameter type** | `types.Schema(type=types.Type.OBJECT)` | `{"type": "object"}` |
| **Property type** | `types.Schema(type=types.Type.STRING)` | `{"type": "string"}` |
| **Enum** | `types.Schema(enum=[...])` | `{"enum": [...]}` |
| **Array items** | `types.Schema(items=types.Schema(...))` | `{"items": {"type": "..."}}` |
| **Conversion** | Direct instantiation | `**dict` unpacking |

---

## 🔧 Complete Working Example

```python
from google import genai
from google.genai import types

# Step 1: Define function schema as raw dict
kg_function_dict = {
    "name": "knowledge_graph_lookup",
    "description": "Query the Knowledge Graph for structured data",
    "parameters": {
        "type": "object",
        "properties": {
            "query_type": {
                "type": "string",
                "description": "Type of query: get_project_by_name, get_project_metrics, etc.",
                "enum": ["get_project_by_name", "get_project_metrics", "compare_projects"]
            },
            "project_name": {
                "type": "string",
                "description": "Name of the project (e.g., 'Sara City')"
            },
            "attribute": {
                "type": "string",
                "description": "Attribute to retrieve (e.g., 'Project Size', 'PSF')"
            }
        },
        "required": ["query_type"]
    }
}

# Step 2: Convert to FunctionDeclaration
kg_function = types.FunctionDeclaration(**kg_function_dict)

# Step 3: Wrap in Tool
kg_tool = types.Tool(function_declarations=[kg_function])

# Step 4: Use with Gemini
client = genai.Client(api_key="your-api-key")

response = client.models.generate_content(
    model='gemini-2.0-flash-exp',
    contents="What is the Project Size of Sara City?",
    config=types.GenerateContentConfig(
        tools=[kg_tool]
    )
)

# Step 5: Handle function call
if response.candidates[0].content.parts[0].function_call:
    func_call = response.candidates[0].content.parts[0].function_call
    print(f"Function called: {func_call.name}")
    print(f"Arguments: {dict(func_call.args)}")
```

---

## 🎯 File Modified

**File:** `app/adapters/gemini_unified_adapter.py`

**Method:** `_create_kg_function_tool()`

**Lines:** 131-210

**Changes:**
- Replaced `types.Schema` nested structure with raw dict
- Used `types.FunctionDeclaration(**dict)` for conversion
- Maintained all functionality, just changed format

---

## ✅ Verification

Run the test script to verify the fix:

```bash
python test_interactions_api_fix.py
```

**Expected Output:**
```
✅ PASS  KG Function Declaration Format
✅ PASS  File Search Tool Format
✅ PASS  Tools Configuration
✅ PASS  Simple KG Query
✅ PASS  File Search Query

Total: 5/5 tests passed
🎉 All tests passed! Interactions API compatibility verified.
```

---

## 📚 Reference: Google's Official Format

From Google's documentation, the recommended format is:

```json
{
  "name": "knowledge_graph_lookup",
  "description": "Searches the Knowledge Graph...",
  "parameters": {
    "type": "object",
    "properties": {
      "entity_name": {
        "type": "string",
        "description": "The primary entity to search for"
      },
      "relationship_type": {
        "type": "string",
        "description": "The type of relationship to look up"
      }
    },
    "required": ["entity_name"]
  }
}
```

**This is standard JSON Schema format, not Python types.**

---

## 🚨 Common Pitfalls to Avoid

### ❌ Don't Use `types.Schema` Directly
```python
# DON'T DO THIS
parameters=types.Schema(
    type=types.Type.OBJECT,
    properties={...}
)
```

### ✅ Use Raw Dict Instead
```python
# DO THIS
parameters={
    "type": "object",
    "properties": {...}
}
```

### ❌ Don't Mix Formats
```python
# DON'T MIX
parameters={
    "type": "object",
    "properties": {
        "name": types.Schema(type=types.Type.STRING)  # ❌ Mixed format
    }
}
```

### ✅ Stay Consistent with Raw Dict
```python
# DO THIS
parameters={
    "type": "object",
    "properties": {
        "name": {"type": "string"}  # ✅ Consistent raw dict
    }
}
```

---

## 📖 Additional Resources

- **Google Interactions API Docs:** https://ai.google.dev/gemini-api/docs/interactions
- **Function Calling Guide:** https://ai.google.dev/gemini-api/docs/function-calling
- **JSON Schema Spec:** https://json-schema.org/understanding-json-schema/

---

## 🎓 Key Takeaway

**When using Interactions API:**
1. Define function schemas as **raw JSON dicts** (not `types.Schema`)
2. Convert to `types.FunctionDeclaration` using `**dict` unpacking
3. This format works with both old API and new Interactions API
4. Matches Google's official examples and documentation

**Result:** Function calling now works seamlessly with File Search + KG tools in the Interactions API! 🎉
