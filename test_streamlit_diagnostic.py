"""
Diagnostic script to test if fixes are loaded in the environment
Run this in the same environment where Streamlit is running
"""
import sys
sys.path.insert(0, '/Users/tusharsikand/Documents/Projects/liases-foras')

print("=" * 60)
print("STREAMLIT ENVIRONMENT DIAGNOSTIC")
print("=" * 60)

# Test 1: Check if modules can be imported
print("\n1. Testing imports...")
try:
    from app.orchestration import QueryOrchestrator
    from app.adapters import FormulaServiceAdapter
    from app.services.dynamic_formula_service import DynamicFormulaService
    print("   ✓ All modules imported successfully")
except Exception as e:
    print(f"   ✗ Import error: {e}")
    sys.exit(1)

# Test 2: Check if fixes are in loaded code
print("\n2. Checking if fixes are loaded...")
import inspect

service = DynamicFormulaService()
source = inspect.getsource(service.search_attribute)

if 'position_bonus' in source:
    print("   ✓ Position-based scoring fix is LOADED")
else:
    print("   ✗ Position-based scoring fix is NOT loaded")

if 'attr_lower in query_lower' in source:
    print("   ✓ Containment check fix is LOADED")
else:
    print("   ✗ Containment check fix is NOT loaded")

# Test 3: Actually run a test query
print("\n3. Running live test query...")
orchestrator = QueryOrchestrator()
query = "What is the Project Size of Sara City in Units?"

result = orchestrator.execute_query(query)

print(f"   Query: {query}")
print(f"   Query type: {result.get('query_type')}")
print(f"   Error: {result.get('error')}")
print(f"   Result: {result.get('result')}")

if result.get('result'):
    print("   ✓ Query returned a result!")
    if 'value' in result.get('result', {}):
        print(f"   ✓ Value: {result['result']['value']}")
else:
    print("   ✗ Query returned NO result")

# Test 4: Check attribute search
print("\n4. Testing attribute search...")
adapter = FormulaServiceAdapter()
search_result = adapter.search_attributes(query)

if search_result:
    print(f"   ✓ Found attribute: {search_result[0].get('name')}")
    print(f"   ✓ Confidence: {search_result[0].get('confidence')}")
else:
    print("   ✗ Attribute search returned nothing")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
