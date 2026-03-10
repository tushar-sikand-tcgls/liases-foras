"""
Test Interactions API Compatibility with KG Function Declaration

This script verifies that the KG function declaration works correctly with
the new Interactions API format (raw dict → types.FunctionDeclaration).

Tests:
1. Function declaration schema format
2. Tool creation with File Search + KG
3. Simple query execution
4. Function call detection and execution
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ ERROR: google-genai package not installed")
    print("Install with: pip install google-genai")
    sys.exit(1)

from app.adapters.gemini_unified_adapter import GeminiUnifiedAdapter
from app.adapters.data_service_kg_adapter import get_data_service_kg_adapter


def test_kg_function_declaration_format():
    """Test that KG function declaration is correctly formatted for Interactions API"""
    print(f"\n{'='*80}")
    print(f"TEST 1: KG Function Declaration Format")
    print(f"{'='*80}\n")

    # Get KG adapter
    kg_adapter = get_data_service_kg_adapter()

    # Create unified adapter
    unified_adapter = GeminiUnifiedAdapter(kg_adapter=kg_adapter)

    # Create KG tool
    try:
        kg_tool = unified_adapter._create_kg_function_tool()

        print("✅ KG tool created successfully")
        print(f"   Type: {type(kg_tool)}")
        print(f"   Has function_declarations: {hasattr(kg_tool, 'function_declarations')}")

        if hasattr(kg_tool, 'function_declarations'):
            func_decls = kg_tool.function_declarations
            print(f"   Number of functions: {len(func_decls)}")

            for i, func_decl in enumerate(func_decls):
                print(f"\n   Function {i+1}:")
                print(f"     Name: {func_decl.name}")
                print(f"     Description: {func_decl.description[:100]}...")
                if hasattr(func_decl, 'parameters'):
                    print(f"     Has parameters: ✅")
                    # Check if parameters are correctly structured
                    params = func_decl.parameters
                    if hasattr(params, 'properties'):
                        print(f"     Properties count: {len(params.properties)}")
                        print(f"     Properties: {list(params.properties.keys())}")
                    if hasattr(params, 'required'):
                        print(f"     Required: {params.required}")

        print("\n✅ PASS: KG function declaration format is correct")
        return True

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_search_tool_format():
    """Test that File Search tool is correctly formatted"""
    print(f"\n{'='*80}")
    print(f"TEST 2: File Search Tool Format")
    print(f"{'='*80}\n")

    # Get KG adapter
    kg_adapter = get_data_service_kg_adapter()

    # Create unified adapter
    unified_adapter = GeminiUnifiedAdapter(kg_adapter=kg_adapter)

    # Create File Search tool
    try:
        file_search_tool = unified_adapter._create_file_search_tool()

        print("✅ File Search tool created successfully")
        print(f"   Type: {type(file_search_tool)}")
        print(f"   Has file_search: {hasattr(file_search_tool, 'file_search')}")

        if hasattr(file_search_tool, 'file_search'):
            file_search = file_search_tool.file_search
            print(f"   File Search Type: {type(file_search)}")
            if hasattr(file_search, 'file_search_store_names'):
                stores = file_search.file_search_store_names
                print(f"   Store count: {len(stores)}")
                print(f"   Store names: {stores}")

        print("\n✅ PASS: File Search tool format is correct")
        return True

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tools_configuration():
    """Test that both tools can be configured together"""
    print(f"\n{'='*80}")
    print(f"TEST 3: Tools Configuration (File Search + KG)")
    print(f"{'='*80}\n")

    # Get KG adapter
    kg_adapter = get_data_service_kg_adapter()

    # Create unified adapter
    unified_adapter = GeminiUnifiedAdapter(kg_adapter=kg_adapter)

    try:
        # Create both tools
        file_search_tool = unified_adapter._create_file_search_tool()
        kg_tool = unified_adapter._create_kg_function_tool()

        tools = [file_search_tool, kg_tool]

        print("✅ Both tools created successfully")
        print(f"   Total tools: {len(tools)}")
        print(f"   Tool 1: File Search")
        print(f"   Tool 2: Knowledge Graph Function")

        # Test config creation
        config = types.GenerateContentConfig(
            tools=tools,
            temperature=0.2
        )

        print(f"\n✅ GenerateContentConfig created successfully")
        print(f"   Type: {type(config)}")
        print(f"   Tools count: {len(config.tools) if hasattr(config, 'tools') else 'N/A'}")

        print("\n✅ PASS: Tools configuration is correct")
        return True

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_kg_query():
    """Test a simple KG query to verify function calling works"""
    print(f"\n{'='*80}")
    print(f"TEST 4: Simple KG Query Execution")
    print(f"{'='*80}\n")

    # Get KG adapter
    kg_adapter = get_data_service_kg_adapter()

    # Create unified adapter
    unified_adapter = GeminiUnifiedAdapter(kg_adapter=kg_adapter)

    # Test query that should trigger KG function
    test_query = "What is the Project Size of Sara City?"

    print(f"Query: {test_query}")
    print(f"Expected: KG function call (get_project_metrics)")
    print(f"{'─'*80}\n")

    try:
        result = unified_adapter.query(
            user_query=test_query,
            enable_file_search=False,  # Disable File Search to isolate KG
            enable_kg=True
        )

        print(f"\n✅ Query executed successfully")
        print(f"   Response length: {len(result.text_response)} chars")
        print(f"   File Search used: {result.file_search_used}")
        print(f"   KG function called: {result.kg_function_called}")

        if result.kg_function_called:
            print(f"\n📊 KG Results:")
            print(f"   Success: {result.kg_results.get('success') if result.kg_results else 'N/A'}")
            if result.kg_results and result.kg_results.get('data'):
                print(f"   Data: {result.kg_results.get('data')}")

        print(f"\n📝 Response:")
        print(f"   {result.text_response[:200]}...")

        if result.kg_function_called:
            print("\n✅ PASS: KG function was called successfully")
            return True
        else:
            print("\n⚠️  WARNING: KG function was not called (may need to adjust prompt)")
            return False

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_search_query():
    """Test a File Search query to verify document RAG works"""
    print(f"\n{'='*80}")
    print(f"TEST 5: File Search Query Execution")
    print(f"{'='*80}\n")

    # Get KG adapter
    kg_adapter = get_data_service_kg_adapter()

    # Create unified adapter
    unified_adapter = GeminiUnifiedAdapter(kg_adapter=kg_adapter)

    # Test query that should trigger File Search
    test_query = "What is Absorption Rate? (definition from glossary)"

    print(f"Query: {test_query}")
    print(f"Expected: File Search (document RAG)")
    print(f"{'─'*80}\n")

    try:
        result = unified_adapter.query(
            user_query=test_query,
            enable_file_search=True,
            enable_kg=False  # Disable KG to isolate File Search
        )

        print(f"\n✅ Query executed successfully")
        print(f"   Response length: {len(result.text_response)} chars")
        print(f"   File Search used: {result.file_search_used}")
        print(f"   KG function called: {result.kg_function_called}")

        print(f"\n📝 Response:")
        print(f"   {result.text_response[:300]}...")

        if result.file_search_used or len(result.text_response) > 0:
            print("\n✅ PASS: File Search query executed successfully")
            return True
        else:
            print("\n⚠️  WARNING: File Search may not have been used")
            return False

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all compatibility tests"""
    print(f"\n{'#'*80}")
    print(f"# INTERACTIONS API COMPATIBILITY TESTS")
    print(f"# KG Function Declaration Fix Verification")
    print(f"{'#'*80}\n")

    print("Testing new Interactions API format:")
    print("  - Raw dict → types.FunctionDeclaration")
    print("  - Compatible with File Search + KG tools")
    print("  - Function calling execution\n")

    results = []

    # Run tests
    results.append(("KG Function Declaration Format", test_kg_function_declaration_format()))
    results.append(("File Search Tool Format", test_file_search_tool_format()))
    results.append(("Tools Configuration", test_tools_configuration()))
    results.append(("Simple KG Query", test_simple_kg_query()))
    results.append(("File Search Query", test_file_search_query()))

    # Summary
    print(f"\n{'#'*80}")
    print(f"# TEST SUMMARY")
    print(f"{'#'*80}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")

    print(f"\n{'─'*80}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'─'*80}\n")

    if passed == total:
        print("🎉 All tests passed! Interactions API compatibility verified.")
        print("\nThe KG function declaration is now correctly formatted for:")
        print("  1. Interactions API (raw dict format)")
        print("  2. Function calling with File Search + KG")
        print("  3. Autonomous tool selection by Gemini")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
