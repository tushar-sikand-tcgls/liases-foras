# LangGraph + Hexagonal Architecture - Implementation Progress

**Date:** 2025-12-11
**Status:** ⚙️ In Progress - Ports Defined, Ready for Adapters

---

## ✅ Completed

### 1. Architecture Design (100%)
- ✅ Created comprehensive architecture document: `LANGGRAPH_HEXAGONAL_ARCHITECTURE.md`
- ✅ Defined 3-branch flow: Objective, Analytical, Financial
- ✅ Designed 8 LangGraph nodes with clear responsibilities
- ✅ Specified port/adapter pattern for swappable components

### 2. Port Interfaces (100%)
- ✅ **VectorDBPort** (`app/ports/vector_db_port.py`)
  - `search_attributes(query, k)` - Semantic search for attributes
  - `get_attribute_by_name(name)` - Get specific attribute metadata
  - `get_all_attributes_by_layer(layer)` - Get L0/L1/L2/L3 attributes
  - `load_attributes_from_excel(path)` - Load enriched Excel

- ✅ **KnowledgeGraphPort** (`app/ports/knowledge_graph_port.py`)
  - `fetch_attribute(project, attribute)` - Get single value
  - `fetch_multiple_attributes(project, attributes)` - Batch fetch
  - `aggregate(attribute, aggregation, filters)` - Cross-project aggregation
  - `compare(projects, attribute)` - Multi-project comparison
  - `resolve_project/developer/location(name)` - Fuzzy name resolution
  - `fetch_cash_flow_data(project)` - Financial calculation data
  - `get_all_projects()` - List all projects

- ✅ **LLMPort** (`app/ports/llm_port.py`)
  - `classify_intent(query, history)` - Intent classification
  - `extract_entities(query)` - NER for projects/locations
  - `plan_kg_queries(context)` - Generate query plan
  - `compose_answer(query, kg_data, ...)` - Natural language response
  - `ask_clarification(missing_params, context)` - Multi-turn questions
  - `generate_json_response(prompt, schema)` - Structured output
  - `explain_calculation(type, inputs, result)` - Calculation explanation

### 3. Directory Structure
```
app/
├── ports/                          ✅ Created
│   ├── __init__.py                 ✅ Updated with new ports
│   ├── vector_db_port.py           ✅ Complete
│   ├── knowledge_graph_port.py     ✅ Complete
│   └── llm_port.py                 ✅ Complete
│
├── adapters/                       🔄 Exists (needs new adapters)
├── nodes/                          📁 Created (empty)
├── calculators/                    📁 Created (empty)
└── orchestration/                  🔄 Exists (query_orchestrator.py)
```

---

## 🔄 In Progress

### ChromaDB Adapter Implementation
**Status:** Next step
**File:** `app/adapters/chroma_adapter.py`

**What It Needs to Do:**
1. Implement `VectorDBPort` interface
2. Load `LF-Layers_FULLY_ENRICHED_ALL_36.xlsx` (36 attributes)
3. Create embeddings for each attribute using:
   - Target Attribute name
   - Description
   - Sample Prompts
   - Variations
   - Formula/Derivation
   - Assumptions
4. Provide similarity search via ChromaDB
5. Return rich metadata for LLM context

**Dependencies:**
```bash
pip install chromadb sentence-transformers pandas openpyxl
```

---

## 📋 Next Steps (Priority Order)

### Step 1: Implement ChromaDB Adapter (HIGH PRIORITY)
```python
# app/adapters/chroma_adapter.py
class ChromaAdapter(VectorDBPort):
    """ChromaDB implementation for attribute schema understanding"""

    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("lf_attributes")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def load_attributes_from_excel(self, excel_path: str) -> int:
        """Load Excel and create embeddings"""
        df = pd.read_excel(excel_path)

        for _, row in df.iterrows():
            # Create embedding text
            embedding_text = f"""
            {row['Target Attribute']}
            {row['Description']}
            {row['Sample Prompt']}
            {row['Variation in Prompt']}
            {row['Formula/Derivation']}
            """

            # Generate embedding
            embedding = self.embedding_model.encode(embedding_text)

            # Store in ChromaDB
            self.collection.add(
                ids=[row['Target Attribute']],
                embeddings=[embedding.tolist()],
                metadatas=[row.to_dict()]
            )

    def search_attributes(self, query: str, k: int = 5) -> List[Dict]:
        """Semantic search"""
        query_embedding = self.embedding_model.encode(query)
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=k
        )
        return results['metadatas'][0]
```

### Step 2: Implement Neo4j/DataService Adapter (HIGH PRIORITY)
**File:** `app/adapters/neo4j_kg_adapter.py` or reuse existing `data_service.py`

**Option A:** Wrap existing `data_service.py` as KG adapter
```python
# app/adapters/data_service_kg_adapter.py
from app.services.data_service import data_service
from app.ports.knowledge_graph_port import KnowledgeGraphPort

class DataServiceKGAdapter(KnowledgeGraphPort):
    """Adapter wrapping existing data_service"""

    def __init__(self):
        self.ds = data_service

    def fetch_attribute(self, project: str, attribute: str) -> Any:
        proj = self.ds.get_project_by_name(project)
        if not proj:
            return None
        return self.ds.get_value(proj.get(attribute))

    def aggregate(self, attribute: str, aggregation: str, filters: Dict = None) -> float:
        projects = self.ds.get_all_projects()
        if filters and "location" in filters:
            projects = [p for p in projects if self.ds.get_value(p.get('location')) == filters['location']]

        values = [self.ds.get_value(p.get(attribute)) for p in projects]
        values = [v for v in values if v is not None]

        if aggregation == "sum":
            return sum(values)
        elif aggregation == "avg":
            return sum(values) / len(values)
        elif aggregation == "max":
            return max(values)
        elif aggregation == "min":
            return min(values)
        # ... etc
```

### Step 3: Implement Gemini LLM Adapter (HIGH PRIORITY)
**File:** `app/adapters/gemini_llm_adapter.py`

**Reuse existing UltraThink:**
```python
from app.services.ultrathink_agent import get_ultrathink_agent
from app.ports.llm_port import LLMPort
import google.generativeai as genai

class GeminiLLMAdapter(LLMPort):
    """Gemini implementation for LLM intelligence"""

    def __init__(self):
        self.agent = get_ultrathink_agent()
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config={"response_mime_type": "application/json"}
        )

    def classify_intent(self, query: str, conversation_history: List = None) -> Dict:
        prompt = f"""Classify this query:
        Query: "{query}"

        Return JSON:
        {{
          "intent": "objective|analytical|financial",
          "subcategory": "...",
          "confidence": 0.0-1.0,
          "reasoning": "..."
        }}
        """
        response = self.model.generate_content(prompt)
        return json.loads(response.text)

    # ... implement other methods
```

### Step 4: Create QueryState Schema
**File:** `app/orchestration/state_schema.py`

```python
from typing import TypedDict, List, Dict, Optional, Any

class QueryState(TypedDict):
    # Input
    query: str
    session_id: str
    conversation_history: List[Dict]

    # Intent
    intent: str  # "objective" | "analytical" | "financial"
    subcategory: Optional[str]
    confidence: float

    # Resolved
    resolved_attributes: List[Dict]
    resolved_projects: List[str]

    # Plans
    kg_query_plan: Dict
    vector_db_query_plan: Dict

    # Results
    kg_data: Dict
    computation_results: Optional[Dict]

    # Multi-turn
    required_parameters: Dict
    missing_parameters: List[str]

    # Output
    answer: str
    provenance: Dict
    next_action: str
```

### Step 5: Implement LangGraph Nodes
**Files:** `app/nodes/*.py` (8 files)

Start with:
1. `intent_classifier_node.py` - Uses LLMPort
2. `attribute_resolver_node.py` - Uses VectorDBPort
3. `entity_resolver_node.py` - Uses LLMPort + KGPort
4. `kg_executor_node.py` - Uses KGPort
5. `answer_composer_node.py` - Uses LLMPort

### Step 6: Build LangGraph State Machine
**File:** `app/orchestration/enhanced_orchestrator.py`

```python
from langgraph.graph import StateGraph, END
from app.orchestration.state_schema import QueryState
from app.nodes import *
from app.ports import VectorDBPort, KnowledgeGraphPort, LLMPort

class EnhancedOrchestrator:
    def __init__(
        self,
        vector_db: VectorDBPort,
        kg: KnowledgeGraphPort,
        llm: LLMPort
    ):
        self.vector_db = vector_db
        self.kg = kg
        self.llm = llm
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(QueryState)

        # Add nodes
        workflow.add_node("classify", intent_classifier_node)
        workflow.add_node("resolve_attributes", attribute_resolver_node)
        workflow.add_node("resolve_entities", entity_resolver_node)
        # ...

        # Add edges
        workflow.set_entry_point("classify")
        workflow.add_conditional_edges(
            "classify",
            self._route_by_intent,
            {
                "objective": "resolve_attributes",
                "analytical": "resolve_attributes",
                "financial": "resolve_attributes"
            }
        )
        # ...

        return workflow.compile()
```

### Step 7: Implement Financial Calculators
**Files:** `app/calculators/*.py`

```python
# app/calculators/irr_calculator.py
from scipy.optimize import newton

def calculate_irr(cash_flows: List[float]) -> float:
    """Calculate IRR using Newton's method"""
    def npv_func(rate):
        return sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))

    return newton(npv_func, 0.1)  # 10% initial guess
```

---

## 🎯 Key Design Principles (Ultrathink)

`★ Insight ─────────────────────────────────────`
**1. Three-Layer Separation**
   - Vector DB: WHAT attributes mean (schema)
   - KG: WHAT values are (data truth)
   - LLM: HOW to interpret and explain (intelligence)

**2. Port-First Design**
   - Define interfaces BEFORE implementations
   - Allows swapping ChromaDB → Pinecone without changing nodes
   - Allows swapping Gemini → Claude without changing orchestrator

**3. LangGraph State Machine**
   - Explicit state transitions (no hidden state)
   - Conditional branching based on intent
   - Multi-turn support via state persistence

**4. Financial Multi-turn Flow**
   - ParameterGatherer node checks for missing inputs
   - Routes to "ask_user" if incomplete
   - Loops back to computation when complete
   - LLM generates clarification questions

**5. Provenance-First Answers**
   - Every answer includes source citation
   - [DIRECT] vs [COMPUTED] vs [ASSUMED] markers
   - LLM explains HOW, KG provides WHAT
`─────────────────────────────────────────────────`

---

## 📦 Dependencies to Install

```bash
# Vector DB
pip install chromadb sentence-transformers

# Data processing
pip install pandas openpyxl

# LLM (already have google-generativeai)
# No additional LLM dependencies needed

# Financial calculations (already have scipy)
# No additional calculation dependencies needed

# LangGraph (already have langgraph)
# No additional graph dependencies needed
```

---

## 🧪 Testing Strategy

### Unit Tests (Per Adapter)
```python
# tests/adapters/test_chroma_adapter.py
def test_search_attributes():
    adapter = ChromaAdapter()
    adapter.load_attributes_from_excel("path/to/excel")
    results = adapter.search_attributes("total units", k=3)
    assert len(results) == 3
    assert results[0]['Target Attribute'] == "Total Units"
```

### Integration Tests (Ports + Adapters)
```python
# tests/integration/test_vector_db_integration.py
def test_port_adapter_contract():
    port: VectorDBPort = ChromaAdapter()
    results = port.search_attributes("project size")
    assert isinstance(results, list)
    assert 'Target Attribute' in results[0]
```

### End-to-End Tests (Full LangGraph Flow)
```python
# tests/e2e/test_objective_branch.py
def test_objective_query():
    orchestrator = EnhancedOrchestrator(vector_db, kg, llm)
    response = orchestrator.execute("What is the total units for Sara City?")
    assert response['intent'] == "objective"
    assert "3018" in response['answer']
    assert "[DIRECT - KG]" in response['answer']
```

---

## 🚀 Quick Start Once Implemented

```python
from app.adapters.chroma_adapter import ChromaAdapter
from app.adapters.data_service_kg_adapter import DataServiceKGAdapter
from app.adapters.gemini_llm_adapter import GeminiLLMAdapter
from app.orchestration.enhanced_orchestrator import EnhancedOrchestrator

# Initialize adapters
vector_db = ChromaAdapter()
vector_db.load_attributes_from_excel("change-request/enriched-layers/LF-Layers_FULLY_ENRICHED_ALL_36.xlsx")

kg = DataServiceKGAdapter()
llm = GeminiLLMAdapter()

# Create orchestrator
orchestrator = EnhancedOrchestrator(vector_db, kg, llm)

# Execute queries
response = orchestrator.execute("What is the sold % for Sara City?")
print(response['answer'])

# Multi-turn financial query
response = orchestrator.execute("What is the IRR for Sara City?")
# → Asks for missing parameters

response = orchestrator.execute("Use 5 years and estimate from annual sales")
# → Computes and returns IRR
```

---

## 📊 Progress Summary

**Architecture & Design:** ████████████████████ 100%
**Port Interfaces:** ████████████████████ 100%
**Adapters:** ████░░░░░░░░░░░░░░░░ 20% (ChromaDB in progress)
**State Schema:** ░░░░░░░░░░░░░░░░░░░░ 0%
**LangGraph Nodes:** ░░░░░░░░░░░░░░░░░░░░ 0%
**State Machine:** ░░░░░░░░░░░░░░░░░░░░ 0%
**Financial Calculators:** ░░░░░░░░░░░░░░░░░░░░ 0%

**Overall:** ████████░░░░░░░░░░░░ 40%

**Estimated Remaining Work:** 4-6 hours
- ChromaDB Adapter: 1 hour
- KG Adapter Wrapper: 1 hour
- LLM Adapter: 1 hour
- State Schema + Nodes: 2 hours
- State Machine Assembly: 1 hour
- Testing & Integration: 1-2 hours

---

**Next Action:** Implement ChromaDB adapter (`app/adapters/chroma_adapter.py`)
