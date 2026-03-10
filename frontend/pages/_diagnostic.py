"""
Diagnostic Page - Check Code Status in Running Streamlit Process
"""
import streamlit as st
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.set_page_config(page_title="Diagnostic", page_icon="🔍", layout="wide")

st.title("🔍 Code Diagnostic")
st.markdown("Check if bug fixes are loaded in this Streamlit process")

st.divider()

# Test 1: Module inspection
st.header("1. Module Code Inspection")

try:
    from app.services.dynamic_formula_service import DynamicFormulaService
    import inspect

    service = DynamicFormulaService()
    source = inspect.getsource(service.search_attribute)

    col1, col2 = st.columns(2)

    with col1:
        if 'position_bonus' in source:
            st.success("✅ Position-based scoring fix is LOADED")
        else:
            st.error("❌ Position-based scoring fix is NOT loaded")
            st.warning("You need to STOP and RESTART the Streamlit server!")

    with col2:
        if 'attr_lower in query_lower' in source:
            st.success("✅ Containment check fix is LOADED")
        else:
            st.error("❌ Containment check fix is NOT loaded")
            st.warning("You need to STOP and RESTART the Streamlit server!")

    with st.expander("View search_attribute source code"):
        st.code(source, language="python")

except Exception as e:
    st.error(f"Error: {e}")

st.divider()

# Test 2: Live query test
st.header("2. Live Query Test")

try:
    from app.orchestration import QueryOrchestrator

    orchestrator = QueryOrchestrator()
    query = "What is the Project Size of Sara City in Units?"

    st.info(f"Testing query: {query}")

    result = orchestrator.execute_query(query)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Query Result")
        st.json(result)

    with col2:
        st.subheader("Status")
        if result.get('result'):
            st.success("✅ Query returned a result")
            if 'value' in result.get('result', {}):
                value = result['result']['value']
                st.success(f"✅ Value: {value}")
                if value == 3018:
                    st.success("✅ CORRECT VALUE!")
                else:
                    st.error(f"❌ Wrong value! Expected 3018, got {value}")
        else:
            st.error("❌ Query returned NO result")
            st.error("This is the BUG - fixes are not active in this process!")

        if result.get('error'):
            st.error(f"Error: {result['error']}")

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())

st.divider()

# Test 3: Test Service
st.header("3. Test Service Integration")

try:
    from app.testing.test_service import AutoHealingTestService
    from app.testing.test_models import BDDTestCase, TestType

    excel_path = "/Users/tusharsikand/Documents/Projects/liases-foras/change-request/BDD-test-cases/BDD_Test_Cases_Micro.xlsx"

    service = AutoHealingTestService(excel_path)

    # Create a test case
    test_case = BDDTestCase(
        test_id=0,
        row_number=2,
        type=TestType.OBJECTIVE,
        prompt='What is the Project Size of Sara City in Units?',
        good_answer='3018 units',
        expected_answer_include='3018',
        score_target='> 8/10'
    )

    st.info("Executing single test case through AutoHealingTestService...")

    result = service.execute_test(test_case, 'diagnostic_run', use_rate_limiter=False)

    st.subheader("Test Result")
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Model Answer", result.model_answer if result.model_answer else "NO RESULT")

    with col2:
        st.metric("Expected", test_case.good_answer)

    if result.model_answer and result.model_answer != "No result returned":
        st.success("✅ Test service returned an answer!")
    else:
        st.error("❌ Test service returned 'No result returned'")
        st.error("**This is the bug you're experiencing!**")

    with st.expander("Full Test Result"):
        st.json({
            'model_answer': result.model_answer,
            'passed': result.passed,
            'error': result.error_message,
            'execution_time_ms': result.execution_time_ms
        })

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())

st.divider()

# Instructions
st.header("🔧 How to Fix")

st.markdown("""
### If you see ❌ errors above:

1. **STOP the Streamlit server completely:**
   - Go to the terminal where Streamlit is running
   - Press `Ctrl+C` to stop it
   - Wait for "Stopping..." message

2. **START the server again:**
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

3. **Come back to this diagnostic page** and check if all tests show ✅

### Why is this necessary?

Streamlit caches Python modules when the server starts. Editing files doesn't reload them automatically. You must restart the server process to pick up code changes.
""")

# Show process info
st.divider()
st.subheader("Process Info")
st.text(f"Python: {sys.executable}")
st.text(f"Working dir: {Path.cwd()}")

if st.button("🔄 Reload Page"):
    st.rerun()
