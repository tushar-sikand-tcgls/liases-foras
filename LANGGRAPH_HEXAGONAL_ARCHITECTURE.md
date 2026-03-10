# LangGraph + Hexagonal Architecture Design
## Real Estate Analytics Query Orchestrator

**Date:** 2025-12-11
**Architecture:** LangGraph State Machine + Hexagonal (Ports & Adapters)
**Status:** 🔨 Implementation in Progress

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER QUESTION                                │
│  "What is the IRR if I invest Rs.50 Cr in Sara City over 5 years?" │
└────────────────────────────┬────────────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH STATE MACHINE                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │ Intent       │ →  │ Attribute    │ →  │ KG Query     │         │
│  │ Classifier   │    │ Resolver     │    │ Planner      │         │
│  └──────────────┘    └──────────────┘    └──────────────┘         │
│         ↓                    ↓                    ↓                 │
│  ┌──────────────────────────────────────────────────┐              │
│  │         ROUTING LOGIC (3 BRANCHES)               │              │
│  ├──────────────────────────────────────────────────┤              │
│  │ 1. OBJECTIVE: Direct KG fetch                    │              │
│  │ 2. ANALYTICAL: Multi-project aggregation         │              │
│  │ 3. FINANCIAL: Multi-turn parameter gathering     │              │
│  └──────────────────────────────────────────────────┘              │
│         ↓                    ↓                    ↓                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │ KG Executor  │    │ Computation  │    │ Answer       │         │
│  │              │ →  │ Engine       │ →  │ Composer     │         │
│  └──────────────┘    └──────────────┘    └──────────────┘         │
└────────────────────────────────────────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────────┐
│                    HEXAGONAL ARCHITECTURE                           │
│                      (Ports & Adapters)                             │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │  VECTOR DB      │  │  KNOWLEDGE      │  │  LLM            │   │
│  │  PORT           │  │  GRAPH PORT     │  │  PORT           │   │
│  │                 │  │                 │  │                 │   │
│  │ • Search        │  │ • Fetch         │  │ • Classify      │   │
│  │   attributes    │  │   projects      │  │   intent        │   │
│  │ • Get schema    │  │ • Aggregate     │  │ • Plan queries  │   │
│  │   metadata      │  │ • Compare       │  │ • Explain       │   │
│  │                 │  │ • Resolve       │  │   results       │   │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘   │
│           ↓                    ↓                     ↓             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │  ChromaDB       │  │  Neo4j/         │  │  Gemini         │   │
│  │  Adapter        │  │  DataService    │  │  Adapter        │   │
│  │  (Embeddings)   │  │  Adapter        │  │  (JSON mode)    │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Three Data Layers

### 1. Vector DB (Schema Understanding) - ChromaDB

**Purpose:** Understand WHAT attributes mean, not WHAT their values are

**Data Source:** `LF-Layers_FULLY_ENRICHED_ALL_36.xlsx`

**Embeddings Created From:**
```
For each of 36 attributes:
  - Target Attribute (canonical name)
  - Description (detailed explanation)
  - Sample Prompt (example questions)
  - Variation in Prompt (synonyms)
  - Formula/Derivation (calculation method)
  - Assumptions (business rules)
```

**Query Flow:**
```python
user_query = "What is the unit saleable price for Sara City?"

# Vector search finds top-k relevant attributes
top_attributes = vector_db.search(user_query, k=3)
# Returns: [
#   {
#     "attribute": "Unit Saleable Price",
#     "description": "Average selling price per residential unit...",
#     "formula": "Total Sales Value / Total Units Sold",
#     "unit": "Rs.Cr.",
#     "layer": "L1",
#     "dimension": "CF/U"
#   },
#   {...}, {...}
# ]

# These are passed to LLM as context, NOT as the answer
```

**What Vector DB Does:**
- ✅ Identifies which attributes user is asking about
- ✅ Provides formula/derivation for computed metrics
- ✅ Clarifies units, dimensions, assumptions
- ❌ Does NOT provide actual numeric values (that's KG's job)

### 2. Knowledge Graph (Data Truth) - Neo4j

**Purpose:** Provide ALL numeric/factual answers

**Data Structure:**
```cypher
(:Project {
  projectId: 3306,
  projectName: "Sara City",
  developerName: "Sara Builders",
  location: "Chakan",
  launchDate: "2020-Q1",
  totalUnits: 3018,
  totalSaleableArea: 1234567.0,
  totalSalesValue: 456.78,
  soldPct: 89,
  ...
})

(:Developer {name: "Sara Builders", ...})
(:Location {name: "Chakan", city: "Pune", ...})

(:Project)-[:DEVELOPED_BY]->(:Developer)
(:Project)-[:LOCATED_IN]->(:Location)
```

**Queries:**
```python
# Objective: Fetch specific value
kg.fetch_attribute("Sara City", "totalUnits")
→ 3018

# Analytical: Aggregate across projects
kg.aggregate("totalUnits", location="Chakan", aggregation="sum")
→ 15000

# Analytical: Compare
kg.compare(["Sara City", "The Urbana"], attribute="soldPct")
→ [{"project": "Sara City", "soldPct": 89},
    {"project": "The Urbana", "soldPct": 96}]

# Financial: Fetch cash flow proxies
kg.fetch_cash_flow_data("Sara City")
→ {"annual_sales": 45.2, "total_investment": 350.0, ...}
```

### 3. LLM (Gemini) - Intelligence Layer

**Purpose:** Orchestrate, interpret, explain

**Responsibilities:**
1. **Intent Classification:**
   ```json
   {
     "intent": "financial",
     "subcategory": "IRR",
     "confidence": 0.92,
     "reasoning": "User asks about IRR which requires cash flows and discount rate"
   }
   ```

2. **Query Planning:**
   ```json
   {
     "vector_db_queries": [
       {"search": "IRR calculation", "purpose": "Get formula and assumptions"}
     ],
     "kg_queries": [
       {"action": "fetch", "project": "Sara City", "attributes": ["annual_sales", "total_investment"]},
       {"action": "fetch", "project": "Sara City", "attributes": ["project_duration"]}
     ],
     "missing_parameters": ["discount_rate", "holding_period"],
     "next_action": "ask_user"
   }
   ```

3. **Answer Composition:**
   ```
   Based on Sara City's data from our knowledge graph:
   - Total Investment: Rs.350 Cr (source: KG)
   - Annual Sales: Rs.45.2 Cr/year (source: KG)
   - Holding Period: 5 years (user input)

   Calculated IRR: 18.7%

   [Provenance: Direct KG data + scipy IRR calculation]
   [Assumptions: Uniform cash flows, no exit value]
   [Confidence: High - all inputs from verified sources]
   ```

---

## 🔄 LangGraph State Machine

### State Schema

```python
class QueryState(TypedDict):
    # Input
    query: str
    session_id: str
    conversation_history: List[Dict]

    # Intent Classification
    intent: str  # "objective" | "analytical" | "financial"
    subcategory: Optional[str]  # "IRR" | "NPV" | "comparison" | "aggregation"
    confidence: float

    # Attribute Resolution (from Vector DB)
    resolved_attributes: List[Dict]  # Top-k relevant attributes with metadata
    attribute_names: List[str]  # Canonical attribute names

    # Entity Resolution (from KG)
    resolved_projects: List[str]
    resolved_developers: List[str]
    resolved_locations: List[str]

    # Query Planning
    kg_query_plan: Dict
    vector_db_query_plan: Dict
    computation_plan: Optional[Dict]

    # Execution Results
    kg_data: Dict
    vector_db_data: Dict
    computation_results: Optional[Dict]

    # Multi-turn State (for Financial branch)
    required_parameters: Dict  # {"discount_rate": None, "holding_period": None}
    user_provided_parameters: Dict  # {"holding_period": 5}
    missing_parameters: List[str]

    # Output
    answer: str
    provenance: Dict
    confidence_score: float
    next_action: str  # "answer" | "ask_clarification" | "gather_parameters"
```

### Node Definitions

#### 1. IntentClassifierNode

**Input:** `state.query`, `state.conversation_history`
**Output:** `state.intent`, `state.subcategory`, `state.confidence`

**Logic:**
```python
def classify_intent(state: QueryState) -> QueryState:
    """Use LLM to classify user intent into 3 branches"""

    prompt = f"""
    Classify this real estate query into ONE of three intents:

    Query: "{state['query']}"

    Intents:
    1. OBJECTIVE - Direct retrieval of specific values
       Examples: "What is the total units for Sara City?"
                "Show me the sold % for The Urbana"

    2. ANALYTICAL - Comparison, aggregation, or multi-project analysis
       Examples: "Compare sold % across all Chakan projects"
                "Which project has the highest absorption rate?"

    3. FINANCIAL - Requires financial calculations (IRR, NPV, payback, etc.)
       Examples: "What is the IRR for Sara City?"
                "Calculate NPV with 12% discount rate"

    Return JSON:
    {{
      "intent": "objective|analytical|financial",
      "subcategory": "specific type",
      "confidence": 0.0-1.0,
      "reasoning": "why you chose this"
    }}
    """

    response = llm_port.classify(prompt)
    state["intent"] = response["intent"]
    state["subcategory"] = response["subcategory"]
    state["confidence"] = response["confidence"]

    return state
```

#### 2. AttributeResolverNode

**Input:** `state.query`
**Output:** `state.resolved_attributes`, `state.attribute_names`

**Logic:**
```python
def resolve_attributes(state: QueryState) -> QueryState:
    """Use Vector DB to find relevant attributes and their metadata"""

    # Search Vector DB for top-k relevant attributes
    search_results = vector_db_port.search_attributes(
        query=state["query"],
        k=5  # Top 5 most relevant
    )

    # Enrich state with attribute metadata
    state["resolved_attributes"] = [
        {
            "name": attr["Target Attribute"],
            "description": attr["Description"],
            "formula": attr["Formula/Derivation"],
            "unit": attr["Unit"],
            "dimension": attr["Dimension"],
            "layer": attr["Layer"],
            "sample_prompts": attr["Sample Prompt"],
            "variations": attr["Variation in Prompt"],
            "assumptions": attr["Assumption in Prompt"]
        }
        for attr in search_results
    ]

    state["attribute_names"] = [attr["name"] for attr in state["resolved_attributes"]]

    return state
```

#### 3. EntityResolverNode

**Input:** `state.query`
**Output:** `state.resolved_projects`, `state.resolved_developers`, `state.resolved_locations`

**Logic:**
```python
def resolve_entities(state: QueryState) -> QueryState:
    """Extract and resolve project/developer/location mentions"""

    # Use LLM + KG fuzzy matching to find entities
    entities = llm_port.extract_entities(state["query"])

    # Resolve to canonical names from KG
    state["resolved_projects"] = [
        kg_port.resolve_project(proj)
        for proj in entities.get("projects", [])
    ]

    state["resolved_developers"] = [
        kg_port.resolve_developer(dev)
        for dev in entities.get("developers", [])
    ]

    state["resolved_locations"] = [
        kg_port.resolve_location(loc)
        for loc in entities.get("locations", [])
    ]

    return state
```

#### 4. KGQueryPlannerNode

**Input:** `state.intent`, `state.resolved_attributes`, `state.resolved_projects`
**Output:** `state.kg_query_plan`

**Logic:**
```python
def plan_kg_queries(state: QueryState) -> QueryState:
    """Generate structured KG query plan based on intent"""

    context = {
        "intent": state["intent"],
        "attributes": state["attribute_names"],
        "projects": state["resolved_projects"],
        "locations": state["resolved_locations"]
    }

    prompt = f"""
    Generate a KG query plan for this context:
    {json.dumps(context, indent=2)}

    Return JSON array of queries:
    [
      {{
        "action": "fetch|aggregate|compare",
        "projects": ["Sara City"],
        "attributes": ["totalUnits", "soldPct"],
        "filters": {{}},
        "aggregation": null|"sum|avg|max|min"
      }}
    ]
    """

    query_plan = llm_port.plan_queries(prompt)
    state["kg_query_plan"] = query_plan

    return state
```

#### 5. KGExecutorNode

**Input:** `state.kg_query_plan`
**Output:** `state.kg_data`

**Logic:**
```python
def execute_kg_queries(state: QueryState) -> QueryState:
    """Execute KG queries deterministically (no LLM)"""

    results = {}

    for query in state["kg_query_plan"]:
        if query["action"] == "fetch":
            # Direct attribute fetch
            for project in query["projects"]:
                for attribute in query["attributes"]:
                    key = f"{project}.{attribute}"
                    results[key] = kg_port.fetch_attribute(project, attribute)

        elif query["action"] == "aggregate":
            # Aggregation across projects
            results["aggregation"] = kg_port.aggregate(
                attribute=query["attributes"][0],
                aggregation=query["aggregation"],
                filters=query.get("filters", {})
            )

        elif query["action"] == "compare":
            # Multi-project comparison
            results["comparison"] = kg_port.compare(
                projects=query["projects"],
                attribute=query["attributes"][0]
            )

    state["kg_data"] = results
    return state
```

#### 6. ComputationNode

**Input:** `state.intent`, `state.kg_data`, `state.user_provided_parameters`
**Output:** `state.computation_results`

**Logic:**
```python
def compute_financial_metrics(state: QueryState) -> QueryState:
    """Deterministic financial calculations (IRR, NPV, etc.)"""

    if state["intent"] != "financial":
        return state

    subcategory = state["subcategory"]

    if subcategory == "IRR":
        # Get cash flows from KG data
        cash_flows = state["kg_data"].get("cash_flows", [])

        # Calculate IRR using scipy
        from scipy.optimize import newton

        def npv_func(rate):
            return sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))

        try:
            irr = newton(npv_func, 0.1)  # Initial guess 10%
            state["computation_results"] = {
                "metric": "IRR",
                "value": irr * 100,  # Convert to percentage
                "unit": "%",
                "method": "Newton's method (scipy)",
                "inputs": cash_flows
            }
        except:
            state["computation_results"] = {"error": "IRR calculation failed"}

    elif subcategory == "NPV":
        cash_flows = state["kg_data"].get("cash_flows", [])
        discount_rate = state["user_provided_parameters"].get("discount_rate")

        npv = sum(cf / (1 + discount_rate) ** i for i, cf in enumerate(cash_flows))

        state["computation_results"] = {
            "metric": "NPV",
            "value": npv,
            "unit": "Rs.Cr.",
            "method": "Discounted cash flow",
            "inputs": {
                "cash_flows": cash_flows,
                "discount_rate": discount_rate
            }
        }

    return state
```

#### 7. ParameterGathererNode (Multi-turn)

**Input:** `state.subcategory`, `state.kg_data`
**Output:** `state.required_parameters`, `state.missing_parameters`, `state.next_action`

**Logic:**
```python
def gather_parameters(state: QueryState) -> QueryState:
    """Check if all required parameters are available for financial calculations"""

    if state["intent"] != "financial":
        return state

    # Define required parameters per financial metric
    requirements = {
        "IRR": ["cash_flows"],
        "NPV": ["cash_flows", "discount_rate"],
        "payback": ["cash_flows", "initial_investment"],
        "cash_on_cash": ["annual_cash_flow", "initial_investment"]
    }

    subcategory = state["subcategory"]
    required = requirements.get(subcategory, [])

    # Check what's missing
    missing = []
    for param in required:
        if param not in state["user_provided_parameters"] and param not in state["kg_data"]:
            missing.append(param)

    state["required_parameters"] = {p: None for p in required}
    state["missing_parameters"] = missing

    if missing:
        state["next_action"] = "gather_parameters"
    else:
        state["next_action"] = "compute"

    return state
```

#### 8. AnswerComposerNode

**Input:** `state.kg_data`, `state.computation_results`, `state.resolved_attributes`
**Output:** `state.answer`, `state.provenance`

**Logic:**
```python
def compose_answer(state: QueryState) -> QueryState:
    """Use LLM to compose natural language answer with proper provenance"""

    context = {
        "query": state["query"],
        "intent": state["intent"],
        "kg_data": state["kg_data"],
        "computation_results": state.get("computation_results"),
        "attributes_metadata": state["resolved_attributes"]
    }

    prompt = f"""
    Compose a clear, factual answer for this query.

    Query: {state['query']}
    Intent: {state['intent']}

    Data from Knowledge Graph (SOURCE OF TRUTH):
    {json.dumps(state['kg_data'], indent=2)}

    Computation Results (if any):
    {json.dumps(state.get('computation_results'), indent=2)}

    Attribute Metadata (for context):
    {json.dumps(state['resolved_attributes'][:2], indent=2)}

    Requirements:
    1. State clearly which projects/attributes were used
    2. Include numeric results with correct units
    3. Distinguish between:
       - [DIRECT] Retrieved directly from KG
       - [COMPUTED] Calculated using formula
       - [ASSUMED] Based on assumptions
    4. Add provenance footer showing data sources
    5. If uncertain or missing data, say so explicitly

    Example format:
    ---
    Sara City's Total Units is 3,018 units. [DIRECT - KG]

    This represents the total number of residential units in the project.

    [Provenance]
    - Data source: Knowledge Graph
    - Project: Sara City
    - Attribute: Total Units (Layer 0)
    - Last updated: 2024-Q4
    ---
    """

    answer = llm_port.generate_answer(prompt)

    state["answer"] = answer["text"]
    state["provenance"] = {
        "sources": ["Knowledge Graph"],
        "projects": state["resolved_projects"],
        "attributes": state["attribute_names"],
        "computation_method": state.get("computation_results", {}).get("method"),
        "confidence": state["confidence"]
    }

    return state
```

---

## 🌳 LangGraph Routing Logic

### Branch 1: OBJECTIVE (Direct Retrieval)

```
IntentClassifier → AttributeResolver → EntityResolver
                                            ↓
                  KGQueryPlanner → KGExecutor → AnswerComposer
```

**Example:**
- Query: "What is the total units for Sara City?"
- Flow: Classify (objective) → Find attribute (Total Units) → Resolve entity (Sara City) → Fetch from KG → Compose answer
- Result: "Sara City has 3,018 units [DIRECT - KG]"

### Branch 2: ANALYTICAL (Aggregation/Comparison)

```
IntentClassifier → AttributeResolver → EntityResolver
                                            ↓
                  KGQueryPlanner (multi-query) → KGExecutor → AnswerComposer
```

**Example:**
- Query: "Which project in Chakan has the highest sold %?"
- Flow: Classify (analytical) → Find attribute (Sold %) → Resolve location (Chakan) → Aggregate with MAX → Compose answer
- Result: "The Urbana has the highest sold % in Chakan at 96% [COMPUTED - Aggregation]"

### Branch 3: FINANCIAL (Multi-turn Parameter Gathering)

```
IntentClassifier → AttributeResolver → EntityResolver
                                            ↓
                  KGQueryPlanner → KGExecutor → ParameterGatherer
                                                      ↓
                                              Missing params?
                                              ├─ YES → AskUser (loop back)
                                              └─ NO  → ComputationNode → AnswerComposer
```

**Example (Multi-turn):**
```
User: "What is the IRR for Sara City?"

Turn 1:
  - Flow: Classify (financial, IRR) → Fetch KG data → Check parameters
  - Missing: cash_flows, holding_period
  - Response: "I need additional information:
              1. What is your expected holding period (years)?
              2. Or should I estimate cash flows from annual sales data?"

User: "Use 5 years and estimate from annual sales"

Turn 2:
  - Flow: Update parameters → Estimate cash flows from KG → Compute IRR → Answer
  - Result: "Estimated IRR for Sara City over 5 years: 18.7% [COMPUTED]
             [Assumptions: Uniform cash flows based on annual sales Rs.45.2 Cr/year]
             [Method: Newton's method for IRR root finding]"
```

---

## 🔌 Hexagonal Architecture (Ports & Adapters)

### Port Definitions

#### VectorDBPort (Interface)

```python
class VectorDBPort(ABC):
    """Port for attribute schema understanding"""

    @abstractmethod
    def search_attributes(self, query: str, k: int = 5) -> List[Dict]:
        """Search for top-k relevant attributes with metadata"""
        pass

    @abstractmethod
    def get_attribute_by_name(self, attribute_name: str) -> Optional[Dict]:
        """Get full metadata for a specific attribute"""
        pass

    @abstractmethod
    def get_all_attributes_by_layer(self, layer: str) -> List[Dict]:
        """Get all attributes in a specific layer (L0, L1, L2, L3)"""
        pass
```

#### KnowledgeGraphPort (Interface)

```python
class KnowledgeGraphPort(ABC):
    """Port for data retrieval and aggregation"""

    @abstractmethod
    def fetch_attribute(self, project: str, attribute: str) -> Any:
        """Fetch specific attribute value for a project"""
        pass

    @abstractmethod
    def aggregate(self, attribute: str, aggregation: str, filters: Dict = None) -> float:
        """Aggregate attribute across multiple projects"""
        pass

    @abstractmethod
    def compare(self, projects: List[str], attribute: str) -> List[Dict]:
        """Compare attribute values across projects"""
        pass

    @abstractmethod
    def resolve_project(self, project_name: str) -> Optional[str]:
        """Resolve fuzzy project name to canonical name"""
        pass

    @abstractmethod
    def fetch_cash_flow_data(self, project: str) -> Dict:
        """Fetch cash flow proxies for financial calculations"""
        pass
```

#### LLMPort (Interface)

```python
class LLMPort(ABC):
    """Port for LLM-based intelligence"""

    @abstractmethod
    def classify_intent(self, query: str, conversation_history: List = None) -> Dict:
        """Classify user intent"""
        pass

    @abstractmethod
    def plan_queries(self, context: Dict) -> Dict:
        """Generate structured query plan"""
        pass

    @abstractmethod
    def generate_answer(self, context: Dict) -> str:
        """Compose natural language answer"""
        pass

    @abstractmethod
    def extract_entities(self, query: str) -> Dict:
        """Extract project/developer/location mentions"""
        pass
```

---

## 📁 File Structure

```
app/
├── ports/                          # Port definitions (interfaces)
│   ├── __init__.py
│   ├── vector_db_port.py           # VectorDBPort interface
│   ├── knowledge_graph_port.py     # KnowledgeGraphPort interface
│   └── llm_port.py                 # LLMPort interface
│
├── adapters/                       # Adapter implementations
│   ├── __init__.py
│   ├── chroma_adapter.py           # ChromaDB implementation
│   ├── neo4j_adapter.py            # Neo4j implementation (or use existing data_service)
│   └── gemini_adapter.py           # Gemini LLM implementation
│
├── orchestration/
│   ├── __init__.py
│   ├── enhanced_orchestrator.py    # NEW: LangGraph orchestrator
│   └── state_schema.py             # QueryState TypedDict
│
├── nodes/                          # LangGraph node implementations
│   ├── __init__.py
│   ├── intent_classifier_node.py
│   ├── attribute_resolver_node.py
│   ├── entity_resolver_node.py
│   ├── kg_query_planner_node.py
│   ├── kg_executor_node.py
│   ├── computation_node.py
│   ├── parameter_gatherer_node.py
│   └── answer_composer_node.py
│
├── calculators/                    # Financial calculation logic
│   ├── __init__.py
│   ├── irr_calculator.py
│   ├── npv_calculator.py
│   └── payback_calculator.py
│
└── services/
    └── vector_db_loader.py         # Load Excel into ChromaDB
```

---

## 🎯 Benefits of This Architecture

**1. Separation of Concerns:**
- Vector DB: Schema understanding only
- KG: Data truth only
- LLM: Intelligence only

**2. Testability:**
- Mock ports for unit testing
- Test nodes independently
- Test LangGraph flow with mock data

**3. Swappable Components:**
- Replace ChromaDB with Pinecone → change adapter only
- Replace Gemini with Claude → change adapter only
- Replace Neo4j with PostgreSQL → change adapter only

**4. Multi-turn Support:**
- State persists across conversation turns
- Financial calculations can gather parameters incrementally
- LangGraph handles routing logic

**5. Provenance & Trust:**
- Every answer cites sources
- Clear distinction: DIRECT vs COMPUTED vs ASSUMED
- LLM never invents numbers

---

## ✅ Implementation Checklist

- [ ] Create port interfaces
- [ ] Implement ChromaDB adapter (Vector DB)
- [ ] Load Excel into ChromaDB with embeddings
- [ ] Implement Neo4j/DataService adapter (KG)
- [ ] Implement Gemini adapter (LLM)
- [ ] Create QueryState schema
- [ ] Implement all 8 LangGraph nodes
- [ ] Build LangGraph state machine with routing
- [ ] Implement financial calculators (IRR, NPV, payback)
- [ ] Add multi-turn conversation state management
- [ ] Create answer composer with provenance
- [ ] Test end-to-end with all 3 branches
- [ ] Document API usage and examples
