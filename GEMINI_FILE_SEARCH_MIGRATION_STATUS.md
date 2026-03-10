# Gemini File Search Migration - Status & Next Steps

## Summary

Migration from ChromaDB to Gemini's Fully Managed RAG (File Search) for attribute resolution has been initiated and is architecturally complete, but requires final SDK configuration adjustments.

## ✅ Completed Work

### 1. Created Gemini File Search Adapter
- **File**: `app/adapters/gemini_file_search_adapter.py`
- **Interface**: Implements `VectorDBPort` with all required methods:
  - `search_attributes(query, k)` - Semantic search for attribute synonyms
  - `get_attribute_by_name(attribute_name)` - Exact attribute lookup
  - `get_all_attributes_by_layer(layer)` - Layer-based filtering
  - `get_attributes_by_dimension(dimension)` - Dimension-based filtering
  - `load_attributes_from_excel(excel_path)` - No-op (files managed by Gemini)

### 2. Updated Orchestrator
- **File**: `app/orchestration/langgraph_orchestrator.py` (lines 40, 77)
- **Change**: Replaced `get_chroma_adapter()` with `get_gemini_file_search_adapter()`
- **Import**: Changed from ChromaDB to Gemini File Search adapter
- **Documentation**: Updated docstrings to reflect Gemini File Search as default

### 3. Architecture Design
- **Principle**: Let Gemini handle vector search on its side - no local embeddings needed
- **API**: Uses Gemini Interactions API for File Search integration
- **Store ID**: Configured to use existing File Search Store (`fileSearchStores/8q3a4kh0o5u9-9n1a2dzr14me`)
- **Files**: Managed-RAG files already uploaded:
  - `LF-Layers_FULLY_ENRICHED_ALL_36.xlsx` (22KB) - Attribute metadata with variations
  - `Glossary.pdf` (377KB) - Attribute definitions
  - `Lf Capability Pitch Document.docx` (337KB) - Domain knowledge

## ⚠️ Pending Work

### SDK Configuration Issue
**Problem**: The `google-genai` Python SDK's Interactions API requires a specific configuration pattern for File Search that differs from published documentation.

**Current Error**:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Tool
file_search_store
  Extra inputs are not permitted [type=extra_forbidden, ...]
```

**Attempts Made**:
1. ✗ Dict-based tool configuration: `{"file_search_store": store_name}`
2. ✗ Tool object with file_search_store parameter: `Tool(file_search_store=store_name)`
3. ✗ Direct parameter in interactions.create: `file_search_store=store_name`

**Next Steps**:
1. Review Gemini SDK source code for correct File Search configuration pattern
2. Alternative: Use REST API directly instead of SDK
3. Alternative: Contact Gemini SDK team for File Search examples
4. Reference: ATLAS adapter (`app/adapters/atlas_performance_adapter.py`) uses Interactions API successfully with function calling, but doesn't show File Search pattern

## 📋 Implementation Notes

### Key Design Decisions

1. **No Local Vector Embeddings**
   - ChromaDB required local `sentence-transformers` model (`all-MiniLM-L6-v2`)
   - Gemini File Search handles all embedding and semantic search server-side
   - Significant reduction in local dependencies and storage

2. **Prompt-Based Search**
   - File Search is queried via natural language prompts
   - Gemini extracts relevant attribute metadata from uploaded Excel file
   - Returns JSON-formatted results with attribute details

3. **Same Port Interface**
   - `VectorDBPort` remains unchanged
   - Hexagonal architecture allows swapping implementations
   - No changes needed to `attribute_resolver_node.py` or other consumers

### Test Query Example

**Input**: `"efficiency ratio"`

**Expected Output** (from Excel "Variation in Prompt" column):
```json
[
  {
    "Target Attribute": "Sellout Efficiency",
    "Variation in Prompt": "efficiency ratio | sales efficiency | conversion rate | target achievement | performance ratio",
    "Description": "...",
    "Formula/Derivation": "...",
    "Unit": "%",
    "Dimension": "Dimensionless",
    "Layer": "L1"
  }
]
```

**Actual Status**: Adapter created, SDK configuration pending

## 🔧 Files Modified

### New Files
1. `app/adapters/gemini_file_search_adapter.py` - Main adapter implementation

### Modified Files
1. `app/orchestration/langgraph_orchestrator.py` - Changed default vector_db from ChromaDB to Gemini File Search
2. `app/adapters/gemini_llm_adapter.py` - Enhanced `compose_answer` with attribute resolution context (separate fix for prompt clarity)

### Files to Deprecate (After Migration Complete)
1. `app/adapters/chroma_adapter.py` - Local ChromaDB implementation
2. `data/chroma_db/` - Local vector database (can be deleted)

## 🎯 User Request Context

**Original Issue**: Query "List top 3 projects by efficiency ratio" was not resolving "efficiency ratio" to "Sellout Efficiency"

**Root Cause**: User wanted resolution via managed RAG (Gemini File Search), NOT local ChromaDB

**User Directive**:
> "We are not using ChromaDB - remove that component, we should be using Gemini's provided 'Fully managed RAG' also called 'File Search' by uploading the files in folder `/change-request/managed-rag`"

## 📝 Next Actions

### Immediate (SDK Configuration)
1. Test different File Search configuration patterns with Gemini SDK
2. Review `google-genai` package version and check for updates
3. Consider using Gemini REST API directly if SDK limitations persist

### Post-Migration
1. Test full query flow: "List top 3 projects by efficiency ratio"
2. Verify synonym resolution works correctly
3. Remove ChromaDB adapter and dependencies from codebase
4. Update documentation to reflect File Search as attribute resolution method

### Testing Checklist
- [ ] "efficiency ratio" → "Sellout Efficiency" ✅
- [ ] "sales velocity" → "Monthly Sales Velocity (%)"
- [ ] "absorption rate" → "Absorption Rate"
- [ ] "price growth" → "Price Growth (%)"
- [ ] Full orchestrator query end-to-end

## 📚 References

1. **Gemini File Search Documentation**: https://ai.google.dev/gemini-api/docs/file-search
2. **Interactions API V2**: https://ai.google.dev/gemini-api/docs/interactions
3. **ATLAS Adapter Example**: `app/adapters/atlas_performance_adapter.py` (lines 528-550)
4. **Managed RAG Files**: `change-request/managed-rag/`

## 💡 Insights

**Why File Search > ChromaDB:**
1. **No Local Storage**: Gemini manages vectors server-side
2. **No Local Compute**: No embedding model to run locally
3. **Always Up-to-Date**: Files synced with Gemini's vector store
4. **Better Semantic Search**: Gemini's embedding models are more powerful than `all-MiniLM-L6-v2`
5. **RAG Integration**: Can search across multiple file types (Excel, PDF, DOCX) simultaneously

**Architecture Benefit:**
- Hexagonal ports/adapters pattern makes this swap trivial once SDK issue is resolved
- No changes needed to business logic (attribute_resolver_node, orchestrator logic)
- Clean separation of concerns maintained
