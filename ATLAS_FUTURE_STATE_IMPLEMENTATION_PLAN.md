# ATLAS Future State Implementation Plan
## Migration to Gemini-Centric, AI-First Hexagonal Architecture

**Date:** 2025-01-12
**Status:** Design Phase
**Target:** Incremental evolution within v4 architecture

---

## 🎯 Vision: Future-State ATLAS

ATLAS will become a **LangGraph-orchestrated, Gemini-centric hub** where:

1. **LangGraph** sits at the center of a hexagonal architecture, coordinating all interactions
2. **Gemini 2.5 Flash** handles all LLM operations with native function calling
3. **Interactions API** manages stateful conversations server-side (no client-side session management)
4. **Gemini File Search** (managed RAG) replaces ChromaDB for document intelligence
5. **Knowledge Graph** remains local for data privacy and structured queries
6. **Streaming responses** provide real-time user experience
7. **Hexagonal ports/adapters** ensure vendor independence and testability

---

## 📊 Current State (v4) vs Future State

| Component | Current v4 | Future State ATLAS |
|-----------|------------|-------------------|
| **Orchestrator** | LangGraph with 8 nodes ✅ | Enhanced with Interactions API + Streaming |
| **Architecture** | Hexagonal (ports/adapters) ✅ | Fully hexagonal with all external systems as adapters |
| **LLM** | Gemini 2.5 Flash via function calling ✅ | Gemini with Interactions API for state management |
| **State Management** | Manual chat history in LangGraph state | Interactions API (server-side via `interaction_id`) |
| **RAG System** | ChromaDB (local vector DB) | Gemini File Search (fully managed) |
| **Knowledge Graph** | DataService adapter (in-memory JSON) ✅ | Same (local for data privacy) |
| **Function Calling** | GeminiFunctionCallingService ✅ | Integrated with Interactions API |
| **Streaming** | ❌ Not implemented | ✅ Gemini streaming API |
| **Response Format** | Single-turn answer | Real-time streaming with citations |

**Key Insight:** Most of the target architecture is already in place! We need to:
1. Integrate Interactions API fully into LangGraph
2. Replace ChromaDB with Gemini File Search
3. Add streaming support
4. Enhance function calling with server-side state

---

## 🏗️ Architecture Diagram: Future State

```
┌────────────────────────────────────────────────────────────────────┐
│                         CLIENT DEVICE                              │
│                    (Streamlit / Web / Mobile)                      │
└────────────────────────────────────────────────────────────────────┘
                                ↕ (interaction_id only)
┌────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH ORCHESTRATOR (Hub)                    │
│                                                                    │
│  Hexagonal Core: Intent → Attribute → Entity → Query Planning     │
│                  → KG Execution → Parameter Gathering              │
│                  → Computation → Answer Composition                │
└────────────────────────────────────────────────────────────────────┘
                ↕               ↕                ↕
┌─────────────────────┐  ┌──────────────┐  ┌─────────────────────┐
│  GEMINI ADAPTER     │  │ FILE SEARCH  │  │ KNOWLEDGE GRAPH     │
│  (Interactions API) │  │ ADAPTER      │  │ ADAPTER             │
│                     │  │ (Managed RAG)│  │ (Local Privacy)     │
│ • State mgmt        │  │              │  │                     │
│ • Function calling  │  │ Documents:   │  │ • Liases Foras data │
│ • Streaming         │  │ 1. Layers    │  │ • Project entities  │
│ • Tool routing      │  │    Excel     │  │ • Dimensional model │
│                     │  │ 2. Pitch     │  │ • Structured queries│
└─────────────────────┘  │    Doc       │  └─────────────────────┘
                         │ 3. Glossary  │
                         │    PDF       │
                         └──────────────┘
```

---

## 📋 Implementation Phases

### **Phase 1: Gemini Interactions API Integration** (Days 1-3)

**Goal:** Replace manual chat history with server-side state management

**Current State:**
- `gemini_interactions_adapter.py` exists but not integrated into LangGraph
- `gemini_function_calling_service.py` uses manual chat history
- LangGraph state includes `conversation_history` field

**Tasks:**

1. **Enhance Gemini LLM Adapter** (`app/adapters/gemini_llm_adapter.py`)
   - Add `previous_interaction_id` parameter to all methods
   - Use `interactions_adapter` for stateful calls
   - Maintain backward compatibility with stateless calls

2. **Update LangGraph State Schema** (`app/orchestration/state_schema.py`)
   - Add `interaction_id: Optional[str]` field
   - Add `previous_interaction_id: Optional[str]` field
   - Deprecate `conversation_history` (keep for backward compatibility)

3. **Modify Answer Composer Node** (`app/nodes/answer_composer_node.py`)
   - Extract `interaction_id` from LLM response
   - Store in state for next turn

4. **Update API Endpoints** (`app/api/v4.py`)
   - Accept `interaction_id` in request (optional)
   - Return `interaction_id` in response
   - Document multi-turn usage pattern

**Success Criteria:**
- ✅ Multi-turn conversations work with `interaction_id` chaining
- ✅ No client-side chat history required
- ✅ Backward compatibility maintained for single-turn queries

---

### **Phase 2: Gemini File Search Migration** (Days 4-7)

**Goal:** Replace ChromaDB with Google's fully managed RAG system

**Current State:**
- ChromaDB adapter at `app/adapters/chroma_adapter.py`
- Used in attribute_resolver_node for semantic search
- 54 documents indexed locally

**Files to Migrate:**
1. `/change-request/managed-rag/LF-Layers_FULLY_ENRICHED_ALL_36.xlsx`
2. `/change-request/managed-rag/Lf Capability Pitch Document.docx`
3. `/change-request/managed-rag/Glossary.pdf`

**Tasks:**

1. **Create Gemini File Search Adapter** (`app/adapters/gemini_file_search_adapter.py`)
   ```python
   class GeminiFileSearchAdapter(VectorDBPort):
       """
       Adapter for Gemini File Search (managed RAG)

       Implements VectorDBPort interface for seamless replacement of ChromaDB.
       """

       def __init__(self, api_key: str):
           self.client = genai.Client(api_key=api_key)
           self.corpus_id = None  # Will be set after upload

       def upload_documents(self, files: List[str]) -> str:
           """Upload documents to Gemini File Search corpus"""
           # Implementation using client.files.upload()
           pass

       def search_attributes(self, query: str, k: int = 5) -> List[Dict]:
           """Search attributes using Gemini File Search"""
           # Implementation using file search tool
           pass

       def search_semantic(self, query: str, filter_type: str = None) -> List[Dict]:
           """Semantic search across documents"""
           pass
   ```

2. **Upload Documents to Gemini**
   - Script: `scripts/upload_to_gemini_file_search.py`
   - Upload 3 managed RAG files
   - Store corpus_id in environment variable

3. **Update Attribute Resolver Node**
   - Replace ChromaDB adapter with GeminiFileSearchAdapter
   - Use dependency injection (port pattern)
   - Test semantic search accuracy vs ChromaDB

4. **Performance Comparison**
   - Measure latency: ChromaDB vs Gemini File Search
   - Expected: 2-5x faster (eliminates network hops)
   - Document results

**Success Criteria:**
- ✅ All 3 documents uploaded to Gemini File Search
- ✅ Attribute resolution works with managed RAG
- ✅ Latency reduced by 2-5x
- ✅ VectorDBPort interface unchanged (hexagonal principle)

---

### **Phase 3: Function Calling + Interactions API Fusion** (Days 8-10)

**Goal:** Integrate function calling with Interactions API for unified LLM interaction

**Current State:**
- `GeminiFunctionCallingService` handles function calling separately
- `GeminiInteractionsAdapter` handles state separately
- No unified service combining both

**Tasks:**

1. **Create Unified Gemini Orchestration Service** (`app/services/gemini_orchestration_service.py`)
   ```python
   class GeminiOrchestrationService:
       """
       Unified service combining Interactions API + Function Calling

       Features:
       - Server-side state via interaction_id
       - Native function calling with tool routing
       - Streaming support
       - Automatic function execution loop
       """

       def __init__(self, interactions_adapter: GeminiInteractionsAdapter,
                    function_registry: FunctionRegistry):
           self.interactions = interactions_adapter
           self.registry = function_registry

       def process_with_functions(
           self,
           query: str,
           previous_interaction_id: Optional[str] = None,
           max_iterations: int = 5
       ) -> Dict:
           """
           Process query with automatic function calling loop

           Returns:
               - interaction_id: For next turn
               - response: Final text response
               - function_calls: List of functions executed
               - streaming_enabled: bool
           """
           pass

       def stream_with_functions(
           self,
           query: str,
           previous_interaction_id: Optional[str] = None
       ) -> Generator[str, None, None]:
           """Stream response with function calling"""
           pass
   ```

2. **Integrate with LangGraph**
   - Update `answer_composer_node.py` to use unified service
   - Use `previous_interaction_id` from state
   - Store new `interaction_id` in state

3. **Update Function Registry**
   - Add `get_gemini_function_declarations()` method
   - Return FunctionDeclaration objects for Interactions API
   - Ensure compatibility with both old and new SDK

**Success Criteria:**
- ✅ Function calling works with Interactions API
- ✅ Multi-turn conversations maintain context
- ✅ No redundant state management code
- ✅ Unified interface for LLM operations

---

### **Phase 4: Streaming Response Implementation** (Days 11-13)

**Goal:** Add real-time streaming for improved UX

**Current State:**
- No streaming support
- Responses returned as complete strings
- No intermediate feedback to user

**Tasks:**

1. **Add Streaming Support to Gemini Adapter**
   ```python
   def stream_response(
       self,
       query: str,
       previous_interaction_id: Optional[str] = None,
       tools: Optional[List] = None
   ) -> Generator[str, None, None]:
       """
       Stream response tokens in real-time

       Yields:
           Text chunks as they arrive from Gemini
       """
       # Use Gemini streaming API
       pass
   ```

2. **Update Answer Composer Node**
   - Add `stream_mode: bool` to state
   - If streaming enabled, yield chunks instead of waiting
   - Maintain provenance and citations in final message

3. **Create Streaming API Endpoint** (`app/api/v4.py`)
   ```python
   @router.post("/v4/query/stream")
   async def query_stream(request: QueryRequest):
       """
       Stream query response in real-time

       Returns:
           Server-Sent Events (SSE) stream with:
           - Text chunks
           - Function call notifications
           - Final provenance
       """
       async def generate():
           async for chunk in orchestrator.stream_query(request.query):
               yield f"data: {json.dumps(chunk)}\n\n"

       return StreamingResponse(generate(), media_type="text/event-stream")
   ```

4. **Update Frontend (Streamlit)**
   - Add streaming response handler
   - Display typing animation as tokens arrive
   - Show function calls in progress

**Success Criteria:**
- ✅ Responses stream in real-time (<200ms to first token)
- ✅ Function calls displayed as they execute
- ✅ Final response includes full provenance
- ✅ Fallback to non-streaming if client doesn't support SSE

---

### **Phase 5: Enhanced Knowledge Graph Tools** (Days 14-16)

**Goal:** Create comprehensive KG tools for LLM access

**Current State:**
- Basic KG functions in `function_registry.py`
- Limited to simple queries
- No traversal or relationship queries

**Tasks:**

1. **Add Advanced KG Functions**
   ```python
   # New functions to add:

   def traverse_relationships(
       project_id: int,
       relationship_type: str,
       depth: int = 1
   ) -> Dict:
       """Traverse KG relationships (e.g., 'LOCATED_IN', 'DEVELOPED_BY')"""
       pass

   def compare_projects(
       project_ids: List[int],
       attributes: List[str]
   ) -> Dict:
       """Compare multiple projects across specified attributes"""
       pass

   def get_market_context(
       location: str,
       radius_km: float = 10
   ) -> Dict:
       """Get all projects in geographic proximity"""
       pass

   def get_dimensional_lineage(
       project_id: int,
       target_metric: str
   ) -> Dict:
       """
       Trace calculation lineage from Layer 3 → Layer 2 → Layer 1 → Layer 0

       Example:
           IRR → NPV, Cash Flows → Revenue, Costs → Price, Units, Area
       """
       pass
   ```

2. **Register Tools with Function Registry**
   - Add schemas for all new functions
   - Implement handlers
   - Add to Gemini function declarations

3. **Document Tool Usage Patterns**
   - Create examples for common queries
   - Update CLAUDE.md with function catalog
   - Add to API documentation

**Success Criteria:**
- ✅ 15+ KG tools available to LLM
- ✅ Complex traversal queries work
- ✅ Lineage tracing implemented
- ✅ LLM can autonomously decide which tools to use

---

### **Phase 6: Testing & Validation** (Days 17-20)

**Goal:** Comprehensive testing of future-state architecture

**Test Categories:**

1. **Unit Tests**
   - Interactions API adapter (state management)
   - File Search adapter (semantic search accuracy)
   - Streaming response handler
   - Each new KG tool function

2. **Integration Tests**
   - Multi-turn conversations with function calling
   - Streaming + function calling combination
   - File Search + KG hybrid queries
   - End-to-end LangGraph flow

3. **Performance Tests**
   ```python
   # Benchmark targets:

   Single-turn query (no functions):      < 1 second
   Multi-turn query (with state):         < 1.5 seconds
   File Search semantic query:            < 500ms
   KG structured query:                   < 200ms
   Streaming first token:                 < 200ms
   Function calling loop (5 functions):   < 3 seconds
   ```

4. **Regression Tests**
   - All existing v4 tests must pass
   - No breaking changes to API contracts
   - Backward compatibility verified

**Success Criteria:**
- ✅ 100% of unit tests passing
- ✅ 100% of integration tests passing
- ✅ Performance targets met
- ✅ No regressions in existing functionality

---

## 🔧 Technical Implementation Details

### Environment Variables (New)

```bash
# .env additions

# Gemini Interactions API
GOOGLE_API_KEY=your_api_key_here

# Gemini File Search
GEMINI_FILE_SEARCH_CORPUS_ID=your_corpus_id_here  # Set after upload

# Streaming configuration
ENABLE_STREAMING=true
STREAMING_CHUNK_SIZE=50  # tokens per chunk
```

### Dependencies (New)

```toml
# pyproject.toml or requirements.txt

# Existing
google-generativeai>=0.3.0

# New for Interactions API
google-genai>=1.0.0  # New SDK with Interactions API support

# Streaming support
sse-starlette>=1.6.5  # Server-Sent Events for FastAPI
```

### File Structure (New Files)

```
app/
├── adapters/
│   ├── gemini_file_search_adapter.py       # NEW: Managed RAG adapter
│   └── gemini_orchestration_service.py     # NEW: Unified LLM service
├── services/
│   └── streaming_service.py                # NEW: Streaming response handler
└── api/
    └── streaming_endpoints.py              # NEW: SSE endpoints

scripts/
└── upload_to_gemini_file_search.py         # NEW: Document upload utility

tests/
├── test_interactions_api.py                # NEW: State management tests
├── test_file_search.py                     # NEW: Managed RAG tests
└── test_streaming.py                       # NEW: Streaming tests
```

---

## 🎯 Success Metrics

### Performance

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| First token latency | N/A (no streaming) | <200ms | ∞ |
| Semantic search | 1-2s (ChromaDB) | <500ms | 2-4x faster |
| Multi-turn context | Manual history | Server-side | Automatic |
| RAG accuracy | 70-80% | 85-95% | +15-20% |

### User Experience

- ✅ Real-time response streaming (typing animation)
- ✅ No client-side session management required
- ✅ Automatic function calling without user intervention
- ✅ Citations from managed RAG documents

### Developer Experience

- ✅ Hexagonal architecture maintained (easy adapter swapping)
- ✅ Comprehensive function catalog (15+ tools)
- ✅ No vendor lock-in (all external systems behind ports)
- ✅ Testable (dependency injection throughout)

---

## 🚀 Migration Strategy

### Incremental Rollout

1. **Week 1:** Interactions API integration (backward compatible)
2. **Week 2:** File Search migration (parallel with ChromaDB initially)
3. **Week 3:** Function calling fusion + streaming
4. **Week 4:** Testing, documentation, final cutover

### Rollback Plan

- Keep ChromaDB adapter as fallback (toggle via env var)
- Maintain stateless mode for Interactions API (backward compat)
- Feature flags for streaming (`ENABLE_STREAMING=false`)
- Git tags at each phase for easy rollback

### Monitoring

```python
# app/monitoring/atlas_metrics.py

class ATLASMetrics:
    """Monitor future-state architecture health"""

    def track_interaction_api_usage(self):
        """Track Interactions API calls, errors, latency"""
        pass

    def track_file_search_performance(self):
        """Track File Search query latency, accuracy"""
        pass

    def track_streaming_metrics(self):
        """Track streaming chunk delivery, disconnects"""
        pass

    def track_function_calling_patterns(self):
        """Track which functions are called most, success rate"""
        pass
```

---

## 📚 Documentation Updates

### User-Facing

1. **API Documentation** (`/docs` endpoint)
   - New streaming endpoints
   - `interaction_id` usage patterns
   - Multi-turn conversation examples

2. **CLAUDE.md**
   - Updated architecture diagram
   - Function catalog (15+ tools)
   - Managed RAG document list

### Developer-Facing

1. **Architecture Decision Records (ADRs)**
   - ADR-001: Why Interactions API over manual state
   - ADR-002: Why Gemini File Search over ChromaDB
   - ADR-003: Why streaming via SSE

2. **Code Comments**
   - Hexagonal port contracts
   - Adapter implementation patterns
   - Streaming generator usage

---

## 🎓 Learning Resources

### Gemini Interactions API

- [Official Docs](https://ai.google.dev/gemini-api/docs/interactions)
- [Multi-turn conversation examples](https://github.com/google/generative-ai-docs)

### Gemini File Search

- [Managed RAG guide](https://ai.google.dev/gemini-api/docs/file-search)
- [File upload API](https://ai.google.dev/gemini-api/docs/files)

### Streaming with FastAPI

- [SSE with FastAPI](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [sse-starlette library](https://github.com/sysid/sse-starlette)

---

## ✅ Completion Checklist

### Phase 1: Interactions API
- [ ] Gemini LLM adapter supports `previous_interaction_id`
- [ ] LangGraph state includes `interaction_id`
- [ ] Answer composer extracts and stores `interaction_id`
- [ ] API endpoints accept and return `interaction_id`
- [ ] Multi-turn test passing

### Phase 2: File Search
- [ ] Gemini File Search adapter created
- [ ] 3 managed RAG files uploaded
- [ ] Attribute resolver uses File Search
- [ ] Latency benchmarks completed
- [ ] Semantic search accuracy validated

### Phase 3: Function Calling Fusion
- [ ] Unified orchestration service created
- [ ] Function calling works with Interactions API
- [ ] LangGraph integrated
- [ ] Function registry updated

### Phase 4: Streaming
- [ ] Streaming support in Gemini adapter
- [ ] Answer composer supports streaming
- [ ] SSE endpoints created
- [ ] Frontend streaming handler implemented

### Phase 5: Enhanced KG Tools
- [ ] Advanced KG functions implemented
- [ ] Function registry updated
- [ ] Documentation complete
- [ ] LLM can use new tools

### Phase 6: Testing
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Performance benchmarks met
- [ ] No regressions

---

## 🎉 Final Outcome

**ATLAS becomes a production-ready, AI-first real estate analytics system where:**

1. ✅ LangGraph orchestrates all query processing via hexagonal architecture
2. ✅ Gemini handles all LLM operations with server-side state management
3. ✅ Managed RAG eliminates vector DB maintenance overhead
4. ✅ Streaming provides instant user feedback
5. ✅ Local Knowledge Graph ensures data privacy
6. ✅ 15+ tools enable autonomous LLM decision-making
7. ✅ Hexagonal design ensures testability and vendor independence

**Result:** 2-5x faster responses, 95%+ RAG accuracy, zero client-side state management, real-time streaming UX.

---

**Next Steps:** Proceed with Phase 1 implementation (Interactions API integration).
