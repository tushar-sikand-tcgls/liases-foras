# ChromaDB Rebuild Summary

## Issue Identified

**User Report:** System returning wrong metric for "Sellout Efficiency" query.
- Query: "What is Sellout Efficiency of Sara City?"
- **Wrong Answer:** 47.52% (Annual Absorption Rate)
- **Correct Answer:** 5.7% (Sellout Efficiency)

**Root Cause:** ChromaDB was using stale schema that didn't include:
1. "Sellout Efficiency" as a separate metric
2. Synonym mapping: "efficiency ratio" → "Sellout Efficiency"
3. Case-insensitive attribute matching

## Actions Taken

### 1. Removed Hardcoded Synonym Mappings ✅
- **File:** `app/services/gemini_function_calling_service.py`
- **Lines removed:** 315-322 (hardcoded synonym dictionary)
- **Replaced with:** RAG-aware instructions to use vectorized Excel knowledge base

### 2. Enriched JSON with Derived Metrics ✅
- **Script:** `scripts/enrich_json_with_derived_attributes.py`
- **Calculated:** All 19 derived metrics including "Sellout Efficiency"
- **Formula:** `(AnnualSales × 12) / Supply`
- **Result for Sara City:** 5.7%

### 3. Rebuilt ChromaDB Schema ✅
- **Script Created:** `scripts/rebuild_chromadb.py`
- **Executed:** Successfully reloaded 36 attributes from Excel
- **Verification:** "Sellout Efficiency" now loaded with synonyms:
  - efficiency ratio
  - sales efficiency
  - conversion rate
  - target achievement
  - performance ratio

## Files Modified

1. **app/services/gemini_function_calling_service.py**
   - Removed hardcoded metric synonyms (lines 315-322)
   - Added RAG-aware knowledge base instructions

2. **data/extracted/v4_clean_nested_structure.json**
   - Replaced with enriched version containing all 19 derived metrics
   - Each project now has "Sellout Efficiency" with formula and calculated value

3. **scripts/rebuild_chromadb.py** (NEW)
   - Forces ChromaDB to reload schema from Excel
   - Verifies "Sellout Efficiency" is loaded with synonyms
   - Provides next steps for testing

## Verification Steps

### Script Output:
```
================================================================================
✅ REBUILD COMPLETE
================================================================================
   Loaded 36 attributes into ChromaDB
   Collection: lf_attributes

🔍 Verifying 'Sellout Efficiency' attribute...
   ✅ Found: Sellout Efficiency
      Unit: %
      Layer: L0
      Formula: (AnnualSales × 12) / Supply
      Synonyms: efficiency ratio | sales efficiency | conversion rate | target achievement | performance ratio
```

### Test Query (In Progress):
```python
Query: "What is the sellout efficiency of Sara City?"
Expected Answer: 5.7% (not 47.52%)
```

## Pending Issues

1. **Case-Insensitive Matching:** Need to verify attribute resolution works case-insensitively for:
   - "Sellout Efficiency"
   - "sellout efficiency"
   - "efficiency ratio"
   - "SELLOUT EFFICIENCY"

2. **Synonym Resolution:** Ensure ChromaDB's semantic search properly matches synonym phrases to official metric names.

3. **Query Test:** Waiting for test query to complete to verify correct answer is returned.

## Next Steps

1. ✅ ChromaDB rebuild complete
2. 🔄 Test query running (awaiting Ollama response)
3. ⏳ Verify case-insensitive matching works
4. ⏳ Verify synonym resolution works ("efficiency ratio" → "Sellout Efficiency")
5. ⏳ Run full BDD test suite to ensure no regressions

## Rollback Plan

If issues arise:
```bash
# Restore original JSON (without enriched metrics)
cp data/extracted/v4_clean_nested_structure_backup_*.json data/extracted/v4_clean_nested_structure.json

# Rebuild ChromaDB from scratch
python scripts/rebuild_chromadb.py
```

## Key Learnings

1. **ChromaDB Persistence:** ChromaDB checks if collection exists and skips reloading. Need explicit rebuild script.
2. **Derived Metrics in KG:** Pre-calculating derived metrics at KG load time is faster than RAG-based formula retrieval at query time.
3. **Synonym Handling:** Excel "Variation in Prompt" column is the source of truth for metric synonyms.
4. **Case Sensitivity:** User emphasized "metrics should be case insensitive" - this is a critical requirement.

---

**Generated:** 2025-12-22
**Status:** ChromaDB rebuild complete, test query in progress
