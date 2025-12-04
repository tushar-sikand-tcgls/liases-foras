"""
Quick startup test for the new architecture

Tests:
1. Function registry initialization
2. Gemini service initialization
3. Orchestrator initialization
4. All service imports
"""

import os
os.environ['GOOGLE_API_KEY'] = 'AIzaSyAG33P0W7MaScsX7VJxBy-dPJiiIbZ_XhM'

print("=" * 60)
print("TESTING NEW ARCHITECTURE STARTUP")
print("=" * 60)

# Test 1: Function Registry
print("\n1. Testing Function Registry...")
try:
    from app.services.function_registry import get_function_registry
    registry = get_function_registry()
    summary = registry.get_registry_summary()
    print(f"   ✓ Function Registry initialized")
    print(f"   ✓ Total functions: {summary['total_functions']}")
    print(f"   ✓ By layer: {summary['by_layer']}")
    print(f"   ✓ By category: {summary['by_category']}")
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Gemini Function Calling Service
print("\n2. Testing Gemini Function Calling Service...")
try:
    from app.services.gemini_function_calling_service import get_gemini_function_calling_service
    gemini_service = get_gemini_function_calling_service()
    print(f"   ✓ Gemini service initialized")
    print(f"   ✓ API key configured: {gemini_service.api_key[:20]}...")
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Chat History Service
print("\n3. Testing Chat History Service...")
try:
    from app.services.chat_history_service import get_chat_history_service
    chat_service = get_chat_history_service()

    # Create test session
    session = chat_service.create_session()
    print(f"   ✓ Chat History service initialized")
    print(f"   ✓ Test session created: {session['session_id']}")
    print(f"   ✓ Token threshold: {chat_service.TOKEN_THRESHOLD}")
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Orchestrator Service
print("\n4. Testing Orchestrator Service...")
try:
    from app.services.orchestrator_service import get_orchestrator
    orchestrator = get_orchestrator()
    print(f"   ✓ Orchestrator service initialized")

    # Get available functions
    functions_summary = orchestrator.get_available_functions()
    print(f"   ✓ Available functions: {functions_summary['total_functions']}")
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Main Application
print("\n5. Testing Main Application Import...")
try:
    from app.main import app
    print(f"   ✓ Main application imported")
    print(f"   ✓ Total routes: {len(app.routes)}")

    # List new endpoints
    new_endpoints = [
        "/api/qa/question/v2",
        "/api/mcp/query/natural",
        "/api/mcp/session",
        "/api/mcp/functions"
    ]

    print(f"\n   New Endpoints Added:")
    for route in app.routes:
        if hasattr(route, 'path'):
            for endpoint in new_endpoints:
                if endpoint in route.path:
                    print(f"      ✓ {route.path} [{', '.join(route.methods)}]")

except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("STARTUP TEST COMPLETE")
print("=" * 60)
print("\nTo start the server, run:")
print("  python api_server.py")
print("  or")
print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
